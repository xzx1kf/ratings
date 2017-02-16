from django.contrib import admin
from django.db.models import Sum, Q

from .models import *

from datetime import datetime, timedelta
from scipy.stats import poisson

def calculate_team_stats(modelteam, request, queryset):
    for team in queryset:
        q = Match.objects.filter(home_team=team)
        q = q.exclude(completed=False)
        q = q.order_by('-date')[:19]
        team.fthg = q.aggregate(Sum('fthg')).get('fthg__sum')

        q = Match.objects.filter(away_team=team)
        q = q.exclude(completed=False)
        q = q.order_by('-date')[:19]
        team.ftag = q.aggregate(Sum('ftag')).get('ftag__sum')

        q = Match.objects.filter(home_team=team)
        q = q.exclude(completed=False)
        q = q.order_by('-date')[:19]
        team.fthgc = q.aggregate(Sum('ftag')).get('ftag__sum')

        q = Match.objects.filter(away_team=team)
        q = q.exclude(completed=False)
        q = q.order_by('-date')[:19]
        team.ftagc = q.aggregate(Sum('fthg')).get('fthg__sum')

        # league stats
        d = Division.objects.get(pk=team.division.id)

        # calculate team attack and defense strengths
        team.home_attack_strength = (team.fthg / 19) / (d.fthg / d.total_games)
        team.home_defense_strength = (team.fthgc / 19) / (d.ftag / d.total_games)
        team.away_attack_strength = (team.ftag / 19) / (d.ftag / d.total_games)
        team.away_defense_strength = (team.ftagc / 19) / (d.fthg / d.total_games)

        team.save()

def calculate_stats(modeldivision, request, queryset):
    for division in queryset:
        teams = Team.objects.filter(division=division)
        league_total_games = 0
        total_fthg = 0
        total_ftag = 0

        for t in teams:
            q = Match.objects.exclude(completed=False)
            q = q.filter(home_team=t)
            q = q.order_by('-date')[:19]
            league_total_games += q.count()
            total_fthg += q.aggregate(Sum('fthg')).get('fthg__sum')
            total_ftag += q.aggregate(Sum('ftag')).get('ftag__sum')

        league_attack_strength = total_fthg / league_total_games
        league_defense_strength = total_ftag / league_total_games

        division.total_games=league_total_games
        division.attack_strength=league_attack_strength
        division.defense_strength=league_defense_strength
        division.fthg = total_fthg
        division.ftag = total_ftag
        division.save()

calculate_stats.short_description = "Calculate selected league stats"

def calculate_match_probabilities(match):
    # calculate expected goals
    home_goals = (match.home_team.home_attack_strength
        * match.away_team.away_defense_strength
        * match.division.attack_strength)
    away_goals = (match.away_team.away_attack_strength
        * match.home_team.home_defense_strength
        * match.division.defense_strength)

    match.pfthg = home_goals
    match.pftag = away_goals

    match.save()

    probability_type = Probability_Type.objects.get(name='goals')

    home_probabilities = []
    away_probabilities = []

    # calculate match probabilities
    for i in range(6):
        home_pmf = poisson.pmf(i, home_goals)
        away_pmf = poisson.pmf(i, away_goals)

        home_probs, created = Probability.objects.get_or_create(
                match=match,
                team=match.home_team,
                probability_type=probability_type,
                name=i)
        home_probs.probability = home_pmf
        away_probs, created  = Probability.objects.get_or_create(
                match=match,
                team=match.away_team,
                probability_type=probability_type,
                name=i)
        away_probs.probability = away_pmf
        home_probs.save()
        away_probs.save()

        print("{} - home: {}, away: {}".format(
            i,
            home_probs.probability,
            away_probs.probability))

        home_probabilities.append(home_probs)
        away_probabilities.append(away_probs)


    under = 0
    over = 0

    # home win %
    match.home_win = 0
    match.away_win = 0
    match.draw = 0
    for j, away in enumerate(away_probabilities):
        for i, home in enumerate(home_probabilities[j+1:]):
            probability = home.probability * away.probability
            match.home_win += probability

            if j <= 2 and i <= 0:
                under += probability
            else:
                over += probability

    match.home_win = round(match.home_win * 100, 1)

    # draw %
    for i in range(6):
        home = home_probabilities[i].probability
        away = away_probabilities[i].probability
        match.draw += (home) * (away)

        if i < 2:
            under += (home) * (away)
        else:
            over += (home) * (away)

    match.draw = round(match.draw * 100, 1)

    # away win %
    for i in range(6):
        for j in range(i+1,6):
            home = home_probabilities[i].probability
            away = away_probabilities[j].probability
            match.away_win += (home) * (away)

            if j <= 2 and i <= 0:
                under += (home) * (away)
            else:
                over += (home) * (away)

    match.away_win = round(match.away_win * 100, 1)

    match.under = under * 100
    match.over = over * 100
    return match

def refresh_match_stats(modelmatch, request, queryset):
    for match in queryset:
        if match.completed:
            continue
        else:
            match = calculate_match_probabilities(match)
            match.save()

def refresh_league(modelleague, request, queryset):
    for league in queryset:
        league_entries = League_Entry.objects.filter(table=league)

        for entry in league_entries:
            matches = Match.objects.filter(date__gte=league.start_date)
            matches = matches.filter(
                    Q(home_team=entry.team) |
                    Q(away_team=entry.team)).order_by('-date')
            matches = matches.filter(completed=True)

            entry.played = 0
            entry.won = 0
            entry.drawn = 0
            entry.lost = 0
            entry.goals_for = 0
            entry.goals_against = 0
            entry.goal_diff = 0
            entry.points = 0

            for m in matches:
                if m.home_team == entry.team:
                    if m.ftr == 'H':
                        entry.won += 1
                        entry.points += 3
                    elif m.ftr == 'D':
                        entry.drawn += 1
                        entry.points += 1
                    elif m.ftr == 'A':
                        entry.lost += 1

                    entry.goals_for += m.fthg
                    entry.goals_against += m.ftag
                elif m.away_team == entry.team:
                    if m.ftr == 'A':
                        entry.won += 1
                        entry.points += 3
                    elif m.ftr == 'D':
                        entry.drawn += 1
                        entry.points += 1
                    elif m.ftr == 'H':
                        entry.lost += 1

                    entry.goals_for += m.ftag
                    entry.goals_against += m.fthg

            last10 = matches[:10]
            for m in last10:
                if m.home_team==entry.team:
                    if m.ftr=='H':
                        entry.record = 'W' + entry.record[0:9]
                    elif m.ftr=='D':
                        entry.record = 'D' + entry.record[0:9]
                    else:
                        entry.record = 'L' + entry.record[0:9]
                else:
                    if m.ftr=='H':
                        entry.record = 'L' + entry.record[0:9]
                    elif m.ftr=='D':
                        entry.record = 'D' + entry.record[0:9]
                    else:
                        entry.record = 'W' + entry.record[0:9]

            entry.goal_diff = entry.goals_for - entry.goals_against
            entry.played = matches.count()

            entry.save()


class DivisionAdmin(admin.ModelAdmin):
    ordering = ['name']
    actions = [calculate_stats]


class TeamAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_filter = ('division',)
    actions = [calculate_team_stats]


class MatchAdmin(admin.ModelAdmin):
    list_display = (
            'division',
            'date',
            'home_team',
            'away_team',
            'fthg',
            'ftag',
            )
    list_editable = ('fthg', 'ftag')
    actions = [refresh_match_stats]
    list_filter = ('completed', 'division')
    fields = (
            'division',
            'date',
            'home_team',
            'away_team',
            'fthg',
            'ftag',
        )
    list_select_related = ('division', 'home_team',)

    def get_ordering(self, request):
        if request.GET.get('completed__exact') == '0':
            return ['date', 'division__name', 'home_team__name']
        else:
            return ['-date', 'division__name', 'home_team__name']

    def save_model(self, request, obj, form, change):
        if not obj.completed:
            match = calculate_match_probabilities(obj)
        super(MatchAdmin, self).save_model(request, obj, form, change)


class OddsAdmin(admin.ModelAdmin):
    list_filter = ('match__division', 'match__completed')
    ordering = [
            'match__date',
            'match__division__name',
            'match__home_team__name']
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "match":
            kwargs["queryset"] = Match.objects.filter(completed=False)
            return super(OddsAdmin, self).formfield_for_foreignkey(
                    db_field, request, **kwargs)


class LeagueAdmin(admin.ModelAdmin):
    actions = [refresh_league]


class League_EntryAdmin(admin.ModelAdmin):
    list_filter = ('table',)
    ordering = ['-points']


# Register your models here.
admin.site.register(Team, TeamAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Division, DivisionAdmin)
admin.site.register(Odds, OddsAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(League_Entry, League_EntryAdmin)
admin.site.register(Probability_Type)
admin.site.register(Probability)
