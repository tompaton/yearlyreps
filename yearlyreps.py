from dataclasses import dataclass
from datetime import date, datetime, timedelta
from django.contrib.auth import authenticate
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from mako.template import Template
from nanodjango import Django
from tally import Tally, TallyResults
from typing import Iterator

app = Django(SQLITE_DATABASE="data/yearlyreps.db")
app.api.title = "Yearly Reps API Documentation"

from ninja.pagination import paginate  # noqa: E402
from ninja.security import HttpBasicAuth  # noqa: E402


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            return username


@app.admin
class Goal(models.Model):
    goal_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.TextField(blank=False, null=False)
    target = models.IntegerField(blank=True, null=False)
    notes = models.TextField(blank=True, null=False)

    class Meta:
        managed = False
        db_table = "goal"

    def __str__(self):
        return f"{self.goal} ({self.goal_id})"


class GoalSchema(app.ninja.Schema):
    goal_id: int
    goal: str
    target: int
    notes: str


class NewGoalSchema(app.ninja.Schema):
    goal: str
    target: int
    notes: str


@app.admin
class Reps(models.Model):
    rep_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.ForeignKey(Goal, models.CASCADE, blank=False, null=False)
    date = models.DateField(blank=False, null=False)
    count = models.IntegerField(blank=True, null=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "reps"

    def __str__(self):
        return f"{self.date} {self.count} {self.goal} ({self.rep_id})"


class RepsSchema(app.ninja.Schema):
    goal_id: int
    rep_id: int
    date: date
    count: int
    notes: str | None


class NewRepSchema(app.ninja.Schema):
    date: datetime
    count: int
    notes: str | None = None


@app.api.get("/goals", response=list[GoalSchema])
def get_goals(request):
    return Goal.objects.all()


@app.api.get("/goals/{int:goal_id}", response=GoalSchema)
def get_goal(request, goal_id: int):
    return get_object_or_404(Goal, goal_id=goal_id)


@app.api.post("/goals", auth=BasicAuth(), response=GoalSchema)
def create_goal(request, new_goal: NewGoalSchema):
    return Goal.objects.create(
        goal=new_goal.goal, target=new_goal.target, notes=new_goal.notes
    )


@app.api.delete("/goals/{int:goal_id}", auth=BasicAuth())
def delete_goal(request, goal_id: int):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    goal.delete()
    return None


@app.api.get("/goals/{int:goal_id}/reps", response=list[RepsSchema])
@paginate
def get_reps(request, goal_id: int):
    return get_list_or_404(Reps.objects.order_by("-date"), goal_id=goal_id)


@app.api.get("/goals/{int:goal_id}/reps/{int:rep_id}", response=RepsSchema)
def get_rep(request, goal_id: int, rep_id: int):
    return get_object_or_404(Reps, goal_id=goal_id, rep_id=rep_id)


@app.api.post("/goals/{int:goal_id}/reps", auth=BasicAuth(), response=RepsSchema)
def create_rep(request, goal_id: int, new_rep: NewRepSchema):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    return goal.reps_set.create(
        date=new_rep.date.date(), count=new_rep.count, notes=new_rep.notes
    )


@app.api.delete("/goals/{int:goal_id}/reps/{int:rep_id}", auth=BasicAuth())
def delete_rep(request, goal_id: int, rep_id: int):
    rep = get_object_or_404(Reps, goal_id=goal_id, rep_id=rep_id)
    rep.delete()
    return None


@dataclass
class Status:
    name: str
    notes: str
    period_names: list[str]
    targets: list[tuple[str, int]]
    status: list[tuple[str, int]]
    max_total: float
    results: Iterator[TallyResults]


def goal_status(
    goal: Goal, today: date, show_all_dates: bool = True
) -> Status:
    tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
    dates = list(tally.dates())
    if not show_all_dates:
        min_date = today + timedelta(days=-42)
        max_date = today + timedelta(days=7)
        dates = [date for date in reversed(list(dates)) if min_date <= date <= max_date]
    return Status(
        goal.goal,
        goal.notes,
        tally.period_names,
        tally.targets(goal.target),
        tally.status(today),
        tally.max_total,
        tally.results(dates, goal.target, today),
    )


@app.route("/goals/status")
def get_goals_status_html(request):
    today = date.today()
    return HttpResponse(
        Template(filename="templates/goal-status.html").render_unicode(
            title="Yearly Goal Status",
            today=today,
            goals=[
                goal_status(goal, today, show_all_dates=False)
                for goal in Goal.objects.all()
            ],
        )
    )


@app.route("/goals/<int:goal_id>/status")
def get_goal_status_html(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    return HttpResponse(
        Template(filename="templates/goal-status.html").render_unicode(
            title=goal.goal, today=today, goals=[goal_status(goal, today)]
        )
    )


@app.api.get("/goals/{int:goal_id}/status")
def get_goal_status(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
    return tally.status(today)


@app.api.get("/goals/{int:goal_id}/status-v2")
def get_goal_status_v2(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
    return tally.status_v2(today, goal.target)
