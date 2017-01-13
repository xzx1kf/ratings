from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.urls import reverse
from django.views import generic

from .models import Match, Team, Division
from .forms import AnalysisForm

from scipy.stats import poisson

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'football/index.html'
    context_object_name = 'latest_matches_list'

    def get_queryset(self):
        """Return the last completed matches."""
        return Match.objects.filter(completed=True).order_by('-date')[:5]

class DetailView(generic.DetailView):
    model = Match
    template_name = 'football/detail.html'

# This view should probably be the index page.
def fixtures(request):
    fixtures = Match.objects.filter(
            completed=False).order_by(
            'date', 'home_team__name')

    return render(request, 'football/fixtures.html', {
        'fixtures' : fixtures,
        })

def analysis(request):


    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            division = Division.objects.get(name='E0')
            teams = Team.objects.filter(division=division)

            league_total_games = 0
            total_fthg = 0
            total_ftag = 0

            # Get league stats
            for team in teams:
                q = Match.objects.exclude(completed=False)
                q = q.filter(home_team=team)
                q = q.filter(division=division)
                q = q.order_by('-date')[:19]
                league_total_games += q.count()
                total_fthg += q.aggregate(Sum('fthg')).get('fthg__sum')
                total_ftag += q.aggregate(Sum('ftag')).get('ftag__sum')

            league_attack_strength = total_fthg / league_total_games
            league_defense_strength = total_ftag / league_total_games

            print("league total games: {}".format(league_total_games))
            print("total_fthg: {}".format(total_fthg))
            print("total_ftag: {}".format(total_ftag))
            print("league attack strength: {}".format(league_attack_strength))
            print("league defense strength: {}".format(league_defense_strength))

            # Get team stats
            home_team = get_object_or_404(Team, pk=request.POST.get('home_team'))
            away_team = get_object_or_404(Team, pk=request.POST.get('away_team'))

            home_team_fthg = Match.objects.filter(
                    home_team=home_team).exclude(completed=False).order_by(
                            '-date')[:19].aggregate(
                                    Sum('fthg')).get('fthg__sum')
            away_team_fthg = Match.objects.filter(away_team=away_team).exclude(completed=False).order_by('-date')[:19].aggregate(
                    Sum('fthg')).get('fthg__sum')
            home_team_ftag = Match.objects.filter(away_team=away_team).exclude(completed=False).order_by('-date')[:19].aggregate(
                    Sum('ftag')).get('ftag__sum')
            away_team_ftag = Match.objects.filter(home_team=home_team).exclude(completed=False).order_by('-date')[:19].aggregate(
                    Sum('ftag')).get('ftag__sum')

            print("{} fthg: {}".format(home_team.name, home_team_fthg))
            print("{} fthg: {}".format(away_team.name, away_team_fthg))
            print("{} ftag: {}".format(home_team.name, home_team_ftag))
            print("{} ftag: {}".format(away_team.name, away_team_ftag))

            # calculate home team attack strength
            ht_attack_strength = (home_team_fthg / 19) / (total_fthg / league_total_games)
            # calculate away team defense strength
            at_defense_strength = (away_team_fthg / 19) / (total_fthg / league_total_games)
            # calculate expected home goals
            home_goals = ht_attack_strength * at_defense_strength * league_attack_strength

            print("{} attack strength: {}".format(home_team.name, ht_attack_strength))
            print("{} denfese strength: {}".format(away_team.name, at_defense_strength))
            print("{} expected goals: {}".format(home_team.name, home_goals))

            # calculate away team attack strength
            at_attack_strength = (home_team_ftag / 19) / (total_ftag / league_total_games)
            # calculate home team defense strength
            ht_defense_strength = (away_team_ftag / 19) / (total_ftag / league_total_games)
            # calculate expected away goals
            away_goals = at_attack_strength * ht_defense_strength * league_defense_strength

            print("{} attack strength: {}".format(away_team.name, at_attack_strength))
            print("{} denfese strength: {}".format(home_team.name, ht_defense_strength))
            print("{} expected goals: {}".format(away_team.name, away_goals))

            home_team_probabilities = []
            away_team_probabilities = []

            for i in range(0,6):
                home_team_probabilities.append(round((poisson.pmf(i, home_goals) * 100), 1))
                away_team_probabilities.append(round((poisson.pmf(i, away_goals) * 100), 1))

                #print("{}".format(he))
                #print("{}".format(ae))

            # calculate match probabilities
            # home win %
            home_win_probability = 0
            for i in range(0,6):
                for j in range(i+1,6):
                    home = home_team_probabilities[j]
                    away = away_team_probabilities[i]
                    home_win_probability += (home / 10) * (away / 10)
            print("home win probability: {}".format(home_win_probability))

            # draw %
            draw_probability = 0
            for i in range(0,6):
                home = home_team_probabilities[i]
                away = away_team_probabilities[i]
                draw_probability += (home / 10) * (away / 10)
            print("draw probability: {}".format(draw_probability))

            # away win %
            away_win_probability = 0
            for i in range(0,6):
                for j in range(i+1,6):
                    home = home_team_probabilities[i]
                    away = away_team_probabilities[j]
                    away_win_probability += (home / 10) * (away / 10)
            print("away win probability: {}".format(away_win_probability))

            # home team last 5 home matches
            home_team_last_5_matches = Match.objects.filter(home_team=home_team).exclude(completed=False).order_by('-date')[:5]
            away_team_last_5_matches = Match.objects.filter(away_team=away_team).exclude(completed=False).order_by('-date')[:5]
            last_5_matches = zip(home_team_last_5_matches, away_team_last_5_matches)
    
            return render(request, 'football/results.html', {
                'home_team'     : home_team,
                'away_team'     : away_team,
                'home_goals'    : round(home_goals),
                'away_goals'    : round(away_goals),
                'home_win_probability'      : round(home_win_probability, 1),
                'draw_probability'          : round(draw_probability, 1),
                'away_win_probability'      : round(away_win_probability, 1),
                'home_team_probabilities'   : home_team_probabilities,
                'away_team_probabilities'   : away_team_probabilities,
                'home_team_last_5_matches'  : home_team_last_5_matches,
                'away_team_last_5_matches'  : away_team_last_5_matches,
                'last_5_matches'            : last_5_matches,
                })
    else:
        form = AnalysisForm()

    return render(request, 'football/analysis.html', {'form': form})
