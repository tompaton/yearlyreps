from django.db import models
from nanodjango import Django

app = Django(SQLITE_DATABASE="data/yearlyreps.db")


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


@app.admin
class Reps(models.Model):
    rep_id = models.AutoField(primary_key=True, blank=False, null=False)
    goal = models.ForeignKey(Goal, models.DO_NOTHING, blank=False, null=False)
    date = models.IntegerField(blank=False, null=False)
    count = models.IntegerField(blank=True, null=False)
    notes = models.TextField(blank=True, null=False)

    class Meta:
        managed = False
        db_table = "reps"

    def __str__(self):
        return f"{self.date} {self.count} {self.goal} ({self.rep_id})"
