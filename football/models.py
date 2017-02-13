from django.db import models
from django.db.models import Sum
from django.utils import timezone

from scipy.stats import poisson
from smart_selects.db_fields import GroupedForeignKey, ChainedForeignKey

# Create your models here.
class Division(models.Model):
    name = models.CharField(max_length=2, unique=True)
    betfair_name = models.CharField(max_length=200, default="")
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
    betfair_name = models.CharField(max_length=200, default="")
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
        return "{}".format(self.name)

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
    under = models.FloatField(default=0)
    over = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if self.fthg is not None and self.ftag is not None:
            self.completed = True
        else:
            self.completed = False

        if self.completed == True:
            # Add this match to the league table standings
            league = League.objects.get(active=True, division=self.division)
            home_team = League_Entry.objects.get(
                    table=league, team=self.home_team)
            away_team = League_Entry.objects.get(
                    table=league, team=self.away_team)

            if self.fthg > self.ftag:
                self.ftr = 'H'
                home_team.points += 3
                home_team.won += 1
                away_team.lost += 1

                home_team.record = home_team.record[1:10] + 'W'
                away_team.record = away_team.record[1:10] + 'L'
            elif self.ftag > self.fthg:
                self.ftr = 'A'
                away_team.points += 3
                home_team.lost += 1
                away_team.won += 1

                home_team.record = home_team.record[1:10] + 'L'
                away_team.record = away_team.record[1:10] + 'W'
            else:
                self.ftr = 'D'
                home_team.points += 1
                away_team.points += 1
                home_team.drawn += 1
                away_team.drawn += 1
                home_team.record = home_team.record[1:10] + 'D'
                away_team.record = away_team.record[1:10] + 'D'

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

        super(Match, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s vs %s" % (
                self.date.strftime('%d, %b %Y'),
                self.home_team,
                self.away_team)

    class Meta:
        verbose_name_plural = "Matches"
        unique_together = ["date", "home_team", "away_team"]


class Probability_Type(models.Model):
    name =  models.CharField(default="", max_length=200)

class Probability(models.Model):
    match = models.ForeignKey(Match)
    team = models.ForeignKey(Team)
    probability_type = models.ForeignKey(Probability_Type)
    name = models.CharField(default="", max_length=100)
    probability = models.FloatField(default=0)

    def __str__(self):
        return("%s- %s" % (self.match, self.name))

    class Meta:
        unique_together = ('match', 'team', 'name', 'probability_type')


class Odds(models.Model):
    match = models.ForeignKey(
        Match,
        #limit_choices_to={'completed': False},
    )
    home = models.FloatField(default=0)
    draw = models.FloatField(default=0)
    away = models.FloatField(default=0)
    over = models.FloatField(default=0)
    under = models.FloatField(default=0)

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

