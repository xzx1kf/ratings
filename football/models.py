from django.db import models

# Create your models here.
class Division(models.Model):
    name = models.CharField(max_length=2)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Match(models.Model):
    division = models.ForeignKey(Division)
    date = models.DateTimeField('match date')
    home_team = models.ForeignKey(Team, related_name='home_team')
    away_team = models.ForeignKey(Team, related_name='away_team')
    fthg = models.IntegerField(blank=True, null=True)
    ftag = models.IntegerField(blank=True, null=True)
    ftr = models.CharField(max_length=1, blank=True, default="")
    completed = models.BooleanField(default=False)

    def __str__(self):
        return "%s - %s vs %s" % (
                self.date.strftime('%d, %b %Y'), 
                self.home_team, 
                self.away_team)

    class Meta:
        verbose_name_plural = "Matches"
        unique_together = ["date", "home_team", "away_team"]
