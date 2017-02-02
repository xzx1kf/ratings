from django.db import models
from django.db.models import Sum
from django.utils import timezone

from scipy.stats import poisson
from smart_selects.db_fields import GroupedForeignKey, ChainedForeignKey

# Create your models here.
class Division(models.Model):
    name = models.CharField(max_length=2, unique=True)
    total_games = models.IntegerField(default=1)
    attack_strength = models.FloatField(default=1)
    defense_strength = models.FloatField(default=1)
    fthg = models.IntegerField(default=1)
    ftag = models.IntegerField(default=1)
    display_name = models.CharField(max_length=200)

    def __str__(self):
        return self.display_name

class Team(models.Model):
    name = models.CharField(max_length=200, unique=True)
    division = models.ForeignKey(Division)
    fthg = models.IntegerField(default=0)
    ftag = models.IntegerField(default=0)
    fthgc = models.IntegerField(default=0)
    ftagc = models.IntegerField(default=0)
    home_attack_strength = models.FloatField(default=0)
    home_defense_strength = models.FloatField(default=0)
    away_attack_strength = models.FloatField(default=0)
    away_defense_strength = models.FloatField(default=0)
    record = models.CharField(max_length=10, default="")

    def __str__(self):
        return "{}, {}".format(self.name, self.division)

class Match(models.Model):
    division = models.ForeignKey(Division)
    date = models.DateTimeField('match date')
    #home_team = models.ForeignKey(Team, related_name='home_team')
    home_team = ChainedForeignKey(
            Team, 
            chained_field="division", 
            chained_model_field="division", 
            show_all=False, 
            related_name='home_team')
    away_team = ChainedForeignKey(
            Team, 
            chained_field="division", 
            chained_model_field="division", 
            show_all=False, 
            related_name='away_team')
    #away_team = models.ForeignKey(Team, related_name='away_team')
    fthg = models.IntegerField(blank=True, null=True)
    ftag = models.IntegerField(blank=True, null=True)
    ftr = models.CharField(max_length=1, blank=True, default="")
    home_win = models.FloatField(default = 0)
    draw = models.FloatField(default=0)
    away_win = models.FloatField(default=0)
    pfthg = models.FloatField(default=0)
    pftag = models.FloatField(default=0)
    completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.fthg is not None and self.ftag is not None:
            self.completed = True
        else:
            self.completed = False

        if self.completed == True:
            # Add this match to the league table standings
            league = League.objects.get(active=True, division=self.division)
            home_team = League_Entry.objects.get(table=league, team=self.home_team)
            away_team = League_Entry.objects.get(table=league, team=self.away_team)

            if self.fthg > self.ftag:
                self.ftr = 'H'
                home_team.points += 3
                home_team.won += 1
                away_team.lost += 1

                self.home_team.record = "W" + self.home_team.record[0:9] 
                self.away_team.record = "L" + self.away_team.record[0:9]
            elif self.ftag > self.fthg:
                self.ftr = 'A'
                away_team.points += 3
                home_team.lost += 1
                away_team.won += 1

                self.home_team.record = "L" + self.home_team.record[0:9] 
                self.away_team.record = "W" + self.away_team.record[0:9]
            else:
                self.ftr = 'D'
                home_team.points += 1
                away_team.points += 1
                home_team.drawn += 1
                away_team.drawn += 1
                self.home_team.record = "D" + self.home_team.record[0:9] 
                self.away_team.record = "D" + self.away_team.record[0:9]

            home_team.played += 1
            home_team.goals_for += self.fthg
            home_team.goals_against += self.ftag
            home_team.goal_diff = home_team.goals_for - home_team.goals_against

            away_team.played += 1
            away_team.goals_for += self.ftag
            away_team.goals_against += self.fthg
            away_team.goal_diff = away_team.goals_for - away_team.goals_against
            
            away_team.save()
            home_team.save()
            self.home_team.save()
            self.away_team.save()

            super(Match, self).save(*args, **kwargs)
            return
        else:
            # calculate expected goals
            home_goals = self.home_team.home_attack_strength * self.away_team.away_defense_strength * self.division.attack_strength
            away_goals = self.away_team.away_attack_strength * self.home_team.home_defense_strength * self.division.defense_strength

            home_team_probs = []
            away_team_probs = []

            # calculate match probabilities
            for i in range(0, 6):
                home_team_probs.append(round((poisson.pmf(i, home_goals) * 100), 1))
                away_team_probs.append(round((poisson.pmf(i, away_goals) * 100), 1))

            self.pfthg = home_goals
            self.pftag = away_goals

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


class Odds(models.Model):
    match = models.ForeignKey(
        Match, 
        #limit_choices_to={'completed': False},
    )
    home = models.FloatField(default=0)
    draw = models.FloatField(default=0)
    away = models.FloatField(default=0)

    def __str__(self):
        return "%s - %s vs %s (%d,%d,%d)" % (
                self.match.date.strftime('%d, %b %Y'), 
                self.match.home_team, 
                self.match.away_team,
                self.home,
                self.draw,
                self.away)
    class Meta:
        verbose_name_plural = "Odds"


class League(models.Model):
    division = models.ForeignKey(Division)
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class League_Entry(models.Model):
    table = models.ForeignKey(League)
    team = models.ForeignKey(Team)
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    goal_diff = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    record = models.CharField(max_length=10, default="")

    def __str__(self):
        return self.team.name

