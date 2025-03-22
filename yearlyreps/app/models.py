from django.db import models


class Goal(models.Model):
    goal_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.TextField(blank=False, null=False)
    target = models.IntegerField(blank=True, null=False)
    notes = models.TextField(blank=True, null=False)

    def __str__(self):
        return f"{self.goal} ({self.goal_id})"


class Reps(models.Model):
    rep_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.ForeignKey(Goal, models.CASCADE, blank=False, null=False)
    date = models.DateField(blank=False, null=False)
    count = models.IntegerField(blank=True, null=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} {self.count} {self.goal} ({self.rep_id})"
