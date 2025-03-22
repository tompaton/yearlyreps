from ninja import Router, Schema
from ninja.pagination import paginate
from ninja.security import HttpBasicAuth
from datetime import date, datetime
from django.contrib.auth import authenticate
from .models import Goal, Reps
from .tally import Tally
from django.shortcuts import get_object_or_404, get_list_or_404

router = Router()


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            return username


class GoalSchema(Schema):
    goal_id: int
    goal: str
    target: int
    notes: str


class NewGoalSchema(Schema):
    goal: str
    target: int
    notes: str


class RepsSchema(Schema):
    goal_id: int
    rep_id: int
    date: date
    count: int
    notes: str | None


class NewRepSchema(Schema):
    date: datetime
    count: int
    notes: str | None = None


@router.get("/goals", response=list[GoalSchema])
def get_goals(request):
    return Goal.objects.all()


@router.get("/goals/{int:goal_id}", response=GoalSchema)
def get_goal(request, goal_id: int):
    return get_object_or_404(Goal, goal_id=goal_id)


@router.post("/goals", auth=BasicAuth(), response=GoalSchema)
def create_goal(request, new_goal: NewGoalSchema):
    return Goal.objects.create(
        goal=new_goal.goal, target=new_goal.target, notes=new_goal.notes
    )


@router.delete("/goals/{int:goal_id}", auth=BasicAuth())
def delete_goal(request, goal_id: int):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    goal.delete()
    return None


@router.get("/goals/{int:goal_id}/reps", response=list[RepsSchema])
@paginate
def get_reps(request, goal_id: int):
    return get_list_or_404(Reps.objects.order_by("-date"), goal_id=goal_id)


@router.get("/goals/{int:goal_id}/reps/{int:rep_id}", response=RepsSchema)
def get_rep(request, goal_id: int, rep_id: int):
    return get_object_or_404(Reps, goal_id=goal_id, rep_id=rep_id)


@router.post("/goals/{int:goal_id}/reps", auth=BasicAuth(), response=RepsSchema)
def create_rep(request, goal_id: int, new_rep: NewRepSchema):
    goal = get_object_or_404(Goal, goal_id=goal_id)
    return goal.reps_set.create(
        date=new_rep.date.date(), count=new_rep.count, notes=new_rep.notes
    )


@router.delete("/goals/{int:goal_id}/reps/{int:rep_id}", auth=BasicAuth())
def delete_rep(request, goal_id: int, rep_id: int):
    rep = get_object_or_404(Reps, goal_id=goal_id, rep_id=rep_id)
    rep.delete()
    return None


@router.get("/goals/{int:goal_id}/status")
def get_goal_status(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
    return tally.status(today)


@router.get("/goals/{int:goal_id}/status-v2")
def get_goal_status_v2(request, goal_id: int):
    today = date.today()
    goal = get_object_or_404(Goal, goal_id=goal_id)
    tally = Tally.from_reps(goal.reps_set.all(), goal.target, today)
    return tally.status_v2(today, goal.target)
