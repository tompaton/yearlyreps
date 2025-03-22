from dataclasses import dataclass
from datetime import date, timedelta
from django.http import HttpResponse, JsonResponse
from mako.template import Template
from .models import Goal
from django.shortcuts import get_object_or_404
from typing import Iterator
from .tally import Tally, TallyResults


def get_goals_status_html(request):
    today = date.today()
    return HttpResponse(
        Template(filename="app/templates/goal-status.html").render_unicode(
            title="Yearly Goal Status",
            today=today,
            goals=[
                goal_status(goal, today, show_all_dates=False)
                for goal in Goal.objects.all()
            ],
        )
    )


def get_goal_status_html(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    if request.accepts("text/html"):
        return HttpResponse(
            Template(filename="app/templates/goal-status.html").render_unicode(
                title=goal.goal, today=today, goals=[goal_status(goal, today)]
            )
        )
    else:
        tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
        return JsonResponse(tally.status(today), safe=False)


@dataclass
class Status:
    name: str
    notes: str
    period_names: list[str]
    targets: list[tuple[str, int]]
    status: list[tuple[str, int]]
    max_total: float
    results: Iterator[TallyResults]


def goal_status(goal: Goal, today: date, show_all_dates: bool = True) -> Status:
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
