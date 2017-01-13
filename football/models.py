from django.db import models
from django.db.models import Sum

# Create your models here.
class Division(models.Model):
    name = models.CharField(max_length=2)
    total_games = models.IntegerField(default=1)
    attack_strength = models.FloatField(default=1)
    defense_strength = models.FloatField(default=1)
    fthg = models.IntegerField(default=1)
    ftag = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=200)
    division = models.ForeignKey(Division)
    fthg = models.IntegerField(default=0)
    ftag = models.IntegerField(default=0)
    attack_strength = models.FloatField(default=0)
    defense_strength = models.FloatField(default=0)

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
    home_win = models.FloatField(default = 0)
    draw = models.FloatField(default=0)
    away_win = models.FloatField(default=0)
    pfthg = models.IntegerField(default=0)
    pftag = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.completed == True:
            super(Match, self).save(*args, **kwargs)
            return
        else:
            # calculate expected goals
            # TODO: calculate expected goals.  
            super(Match, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s vs %s" % (
                self.date.strftime('%d, %b %Y'), 
                self.home_team, 
                self.away_team)

    class Meta:
        verbose_name_plural = "Matches"
        unique_together = ["date", "home_team", "away_team"]
