from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.db.models import Sum, Q
from django.urls import reverse
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist

from .models import Match, Team, Division, Odds, League, League_Entry
from .forms import AnalysisForm, LeagueForm

from scipy.stats import poisson

def fixtures(request):

    fixtures = []
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            division = get_object_or_404(
                    Division, pk=request.POST.get('division'))
            fixtures = Match.objects.filter(
                    completed=False, division=division).order_by(
                    'date', 'home_team__name')
    else:
        division = Division.objects.first()
        form = LeagueForm(initial = { 'division': division } )
        fixtures = Match.objects.filter(
                completed=False,
                division=division,
            ).order_by(
                'date',
                'home_team__name'
            )
    return render(request, 'football/fixtures.html', {
        'fixtures'  : fixtures,
        'form'      : form,
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
    home_team_last_5_matches = Match.objects.filter(
            home_team=m.home_team).exclude(completed=False).order_by('-date')[:5]
    away_team_last_5_matches = Match.objects.filter(
            away_team=m.away_team).exclude(completed=False).order_by('-date')[:5]
    last_5_matches = zip(home_team_last_5_matches, away_team_last_5_matches)

    ht_last_5_matches = Match.objects.filter(
            Q(home_team=m.home_team) |
            Q(away_team=m.home_team)
            ).order_by('-date').exclude(completed=False)[:5]
    at_last_5_matches = Match.objects.filter(
            Q(home_team=m.away_team) |
            Q(away_team=m.away_team)
            ).order_by('-date').exclude(completed=False)[:5]
    last_5_matches_ha = zip(ht_last_5_matches, at_last_5_matches)


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
    try:
        odds = Odds.objects.get(match=m)
    except ObjectDoesNotExist:
        odds = None

    value, uo_value = get_expected_value(
            m,
            odds,
            home_win_probability,
            draw_probability,
            away_win_probability)

    return render(request, 'football/match.html', {
        'match' : m,
        'home_team'     : m.home_team,
        'away_team'     : m.away_team,
        'home_goals'    : m.pfthg,
        'away_goals'    : m.pftag,
        'home_win_probability'      : m.home_win,
        'draw_probability'          : m.draw,
        'away_win_probability'      : m.away_win,
        'home_team_probabilities'   : home_team_probabilities,
        'away_team_probabilities'   : away_team_probabilities,
        'last_5_matches'            : last_5_matches,
        'odds'                      : odds,
        'value'                     : value,
        'last_5_matches_ha'         : last_5_matches_ha,
        'league_table'              : league_entry,
        'home_entry'                : home_entry,
        'away_entry'                : away_entry,
        'under'                     : m.under,
        'over'                      : m.over,
        'uo_value'                  : uo_value,
        'home_team_position': home_team_position,
        'away_team_position': away_team_position,
        })

def tables(request):
    league_table = []
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            division = get_object_or_404(
                    Division, pk=request.POST.get('division'))
            league = League.objects.get(division=division, active=True)
            league_table = League_Entry.objects.filter(table=league).order_by(
                '-points', '-goal_diff')
    else:
        division = Division.objects.first()
        form = LeagueForm(initial = { 'division': division } )
        league = League.objects.get(division=division, active=True)
        league_table = League_Entry.objects.filter(table=league).order_by(
            '-points', '-goal_diff')

    return render(request, 'football/tables.html', {
        'league_table'  : league_table,
        'form'      : form,
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
