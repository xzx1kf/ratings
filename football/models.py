from django.db import models
from django.db.models import Sum

from scipy.stats import poisson

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
    fthgc = models.IntegerField(default=0)
    ftagc = models.IntegerField(default=0)
    home_attack_strength = models.FloatField(default=0)
    home_defense_strength = models.FloatField(default=0)
    away_attack_strength = models.FloatField(default=0)
    away_defense_strength = models.FloatField(default=0)

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
            home_goals = self.home_team.home_attack_strength * self.away_team.away_defense_strength * self.division.attack_strength
            away_goals = self.away_team.away_attack_strength * self.home_team.home_defense_strength * self.division.defense_strength

            print("{} expected goals: {}".format(self.home_team.name, home_goals))
            print("{} expected goals: {}".format(self.away_team.name, away_goals))
            """
            print("{} attack strength: {}".format(
                self.home_team.name, 
                self.home_team.attack_strength))
            print("{} defense strength: {}".format(
                self.away_team.name, 
                self.away_team.defense_strength))
            print("laegue attack strength: {}".format(
                self.division.attack_strength))

            print("{} attack strength: {}".format(
                self.away_team.name, 
                self.away_team.attack_strength))
            print("{} defense strength: {}".format(
                self.home_team.name, 
                self.home_team.defense_strength))
            print("laegue defense strength: {}".format(
                self.division.defense_strength))
            """

            home_team_probs = []
            away_team_probs = []

            # calculate match probabilities
            for i in range(0, 6):
                home_team_probs.append(round((poisson.pmf(i, home_goals) * 100), 1))
                away_team_probs.append(round((poisson.pmf(i, away_goals) * 100), 1))

            self.pfthg = round(home_goals, 0)
            self.pftag = round(away_goals, 0)

            # home win %
            self.home_win = 0
            self.away_win = 0
            self.draw = 0
            for i in range(0,6):
                for j in range(i+1,6):
                    home = home_team_probs[j]
                    away = away_team_probs[i]
                    self.home_win += (home / 10) * (away / 10)
            self.home_win = round(self.home_win, 1)
            
            # draw %
            for i in range(0,6):
                home = home_team_probs[i]
                away = away_team_probs[i]
                self.draw += (home / 10) * (away / 10)
            self.draw = round(self.draw, 1)

            # away win %
            for i in range(0,6):
                for j in range(i+1,6):
                    home = home_team_probs[i]
                    away = away_team_probs[j]
                    self.away_win += (home / 10) * (away / 10)
            self.away_win = round(self.away_win, 1)
            
            super(Match, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s vs %s" % (
                self.date.strftime('%d, %b %Y'), 
                self.home_team, 
                self.away_team)

    class Meta:
        verbose_name_plural = "Matches"
        unique_together = ["date", "home_team", "away_team"]
