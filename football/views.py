from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from scipy.stats import poisson

from .forms import AnalysisForm, LeagueForm
from .models import Match, Team, Division, Odds, League, League_Entry


def fixtures(request, division_id=Division.objects.first().id):
    leagues = League.objects.filter(active=True)
    name = leagues.get(division__id=division_id)
    fixtures = Match.objects.filter(
            completed=False,
            division__id=division_id,
        ).order_by(
            'date',
            'home_team__name'
        )
    return render(request, 'football/fixtures.html', {
        'fixtures'  : fixtures,
        'leagues' : leagues,
        'name': name,
        'historical_display' : False,
    })


def match(request, match_id):
    m = Match.objects.get(id=match_id)

    home_team_probabilities = []
    away_team_probabilities = []

    for i in range(0,6):
        home_team_probabilities.append(
                round((poisson.pmf(i, m.pfthg) * 100), 1))
        away_team_probabilities.append(
                round((poisson.pmf(i, m.pftag) * 100), 1))

    # calculate match probabilities
    # home win %
    home_win_probability = 0
    for i in range(0,6):
        for j in range(i+1,6):
            home = home_team_probabilities[j]
            away = away_team_probabilities[i]
            home_win_probability += (home / 10) * (away / 10)

    # draw %
    draw_probability = 0
    for i in range(0,6):
        home = home_team_probabilities[i]
        away = away_team_probabilities[i]
        draw_probability += (home / 10) * (away / 10)

    # away win %
    away_win_probability = 0
    for i in range(0,6):
        for j in range(i+1,6):
            home = home_team_probabilities[i]
            away = away_team_probabilities[j]
            away_win_probability += (home / 10) * (away / 10)

    # home team last 5 home matches
    home_team_last_5_at_home = Match.objects.filter(
            home_team=m.home_team).exclude(completed=False).order_by('-date')[:5]
    away_team_last_5_away = Match.objects.filter(
            away_team=m.away_team).exclude(completed=False).order_by('-date')[:5]

    home_team_last_5 = Match.objects.filter(
            Q(home_team=m.home_team) |
            Q(away_team=m.home_team)
            ).order_by('-date').exclude(completed=False)[:5]
    away_team_last_5 = Match.objects.filter(
            Q(home_team=m.away_team) |
            Q(away_team=m.away_team)
            ).order_by('-date').exclude(completed=False)[:5]

    # Get the league table associated with this match
    league_table = League.objects.get(
            division=m.home_team.division, active=True)
    league_entry = League_Entry.objects.filter(
            table=league_table).order_by('-points', '-goal_diff')
    home_entry = League_Entry.objects.get(
            table=league_table, team=m.home_team)
    away_entry = League_Entry.objects.get(
            table=league_table, team=m.away_team)

    # Get the league positions for the home/away teams.
    home_team_position, away_team_position = get_league_positions(
            m, league_entry)

    # calculate the expected value for the given odds.
    odds, created = Odds.objects.get_or_create(match=m)

    value, uo_value = get_expected_value(
            m,
            odds,
            home_win_probability,
            draw_probability,
            away_win_probability)

    # calculate stakes
    home_stake = 0
    away_stake = 0
    draw_stake = 0
    over_stake = 0
    under_stake = 0

    if odds.home and odds.away and odds.draw and odds.over and odds.under > 0:
        home_stake = 200 /(2 * odds.home * (1 - (min(home_win_probability, 60) / 100)))
        draw_stake = 200 /(2 * odds.draw * (1 - (min(draw_probability, 60) / 100)))
        away_stake = 200 /(2 * odds.away * (1 - (min(away_win_probability, 60) / 100)))
        over_stake = 200 /(2 * odds.over * (1 - (min(m.over, 60) / 100)))
        under_stake = 200 /(2 * odds.under * (1 - (min(m.under, 60) / 100)))

    return render(request, 'football/match.html', {
        'home_team'     : m.home_team,
        'away_team'     : m.away_team,
        'home_goals'    : m.pfthg,
        'away_goals'    : m.pftag,
        'home_win_probability'      : m.home_win,
        'draw_probability'          : m.draw,
        'away_win_probability'      : m.away_win,
        'home_team_probabilities'   : home_team_probabilities,
        'away_team_probabilities'   : away_team_probabilities,
        'home_team_last_5_at_home' : home_team_last_5_at_home,
        'away_team_last_5_away' : away_team_last_5_away,
        'home_team_last_5' : home_team_last_5,
        'away_team_last_5' : away_team_last_5,
        'odds'                      : odds,
        'value'                     : value,
        'league_table'              : league_entry,
        'home_entry'                : home_entry,
        'away_entry'                : away_entry,
        'under'                     : m.under,
        'over'                      : m.over,
        'uo_value'                  : uo_value,
        'home_team_position': home_team_position,
        'away_team_position': away_team_position,
        'home_stake' : round(home_stake, 2),
        'draw_stake' : round(draw_stake, 2),
        'away_stake' : round(away_stake, 2),
        'over_stake' : round(over_stake, 2),
        'under_stake' : round(under_stake, 2),
        })

def tables(request, division_id=Division.objects.first().id):
    leagues = League.objects.filter(active=True)
    league = leagues.get(division__id=division_id, active=True)
    league_table = League_Entry.objects.filter(table=league).order_by(
        '-points', '-goal_diff')

    return render(request, 'football/tables.html', {
        'league_table'  : league_table,
        'leagues' : leagues,
        'name' : league.name,
        })


def team(request, team_id):
    team = Team.objects.get(pk=team_id)
    leagues = League.objects.filter(active=True)
    name = leagues.get(division__id=team.division_id)
    fixtures = Match.objects.filter(
            Q(home_team__id=team_id) |
            Q(away_team__id=team_id),
            completed=True,
            division__id=team.division_id,
        ).order_by(
            '-date',
            'home_team__name'
            )[:10]
    return render(request, 'football/fixtures.html', {
        'fixtures'  : fixtures,
        'leagues' : leagues,
        'name': name,
        'historical_display': True,
    })

def teams(request, division_id=Division.objects.first().id):
    leagues = League.objects.filter(active=True)
    league = leagues.get(division__id=division_id, active=True)
    teams = Team.objects.filter(division__id=division_id).order_by('name')

    list_of_teams = []

    for i in range(0, teams.count(), 5):
        list_of_teams.append(teams[i:i+5])

    return render(request, 'football/teams.html', {
        'leagues' : leagues,
        'name': league.name,
        'teams' : list_of_teams,
        })

def get_expected_value(match, odds, home, draw, away):
    """Return the expected value for the given odds."""
    value = None
    uo_value = None
    if odds is not None:
        home_value = odds.home * (home / 100)
        draw_value = odds.draw * (draw / 100)
        away_value = odds.away * (away / 100)
        match_value = (home_value, draw_value, away_value)
        under_value = odds.under * (match.under / 100)
        over_value = odds.over * (match.over / 100)
        over_under_value = (over_value, under_value)
        return match_value, over_under_value
    else:
        return (0,0,0), (0,0)

def get_league_positions(match, table):
    """Returns the league positions for the home and away teams."""
    counter = 0
    home_team_position = 0
    away_team_position = 0
    for team in table:
        counter += 1
        if team.team == match.home_team:
            home_team_position = counter
        if team.team == match.away_team:
            away_team_position = counter
    return home_team_position, away_team_position
