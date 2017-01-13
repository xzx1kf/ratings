from django.contrib import admin
from django.db.models import Sum

from .models import Match, Division, Team

from datetime import datetime, timedelta

def calculate_team_stats(modelteam, request, queryset):
    for team in queryset:
        q = Match.objects.filter(home_team=team)
        #q = q.filter(date__gte=datetime.today() - timedelta(days=200))
        q = q.exclude(completed=False)
        q = q.order_by('-date')[:19]
        team.fthg = q.aggregate(Sum('fthg')).get('fthg__sum')
        team.ftag = q.aggregate(Sum('ftag')).get('ftag__sum')

        # league stats
        d = Division.objects.get(pk=team.division.id)

        # calculate team attack and defense strengths
        team.attack_strength = (team.fthg / 19) / (d.fthg / d.total_games)
        team.defense_strength = (team.ftag / 19) / (d.ftag / d.total_games)

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

class DivisionAdmin(admin.ModelAdmin):
    ordering = ['name']
    actions = [calculate_stats]

class TeamAdmin(admin.ModelAdmin):
    ordering = ['name']
    actions = [calculate_team_stats]

# Register your models here.
admin.site.register(Team, TeamAdmin)
admin.site.register(Match)
admin.site.register(Division, DivisionAdmin)
