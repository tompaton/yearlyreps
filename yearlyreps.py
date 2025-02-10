from datetime import date
from django.db import models
from django.shortcuts import get_object_or_404, get_list_or_404
from nanodjango import Django

app = Django(SQLITE_DATABASE="data/yearlyreps.db")
app.api.title = "Yearly Reps API Documentation"

from ninja.pagination import paginate  # noqa: E402


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


@app.admin
class Reps(models.Model):
    rep_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.ForeignKey(Goal, models.CASCADE, blank=False, null=False)
    date = models.IntegerField(blank=False, null=False)
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


@app.api.get("/goals", response=list[GoalSchema])
def get_goals(request):
    return Goal.objects.all()


@app.api.get("/goals/{int:goal_id}", response=GoalSchema)
def get_goal(request, goal_id: int):
    return get_object_or_404(Goal, goal_id=goal_id)


@app.api.delete("/goals/{int:goal_id}")
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


@app.api.delete("/goals/{int:goal_id}/reps/{int:rep_id}")
def delete_rep(request, goal_id: int, rep_id: int):
    rep = get_object_or_404(Reps, goal_id=goal_id, rep_id=rep_id)
    rep.delete()
    return None
