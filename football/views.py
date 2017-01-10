from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.urls import reverse
from django.views import generic

from .models import Match, Team
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

def analysis(request):


    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            teams = Team.objects.all()

            league_total_games = 0

            # Get league stats
            for team in teams:
                league_total_games += Match.objects.filter(home_team=team).order_by('-date')[:19].count()
            total_fthg = Match.objects.order_by('-date')[:19].aggregate(
                    Sum('fthg')).get('fthg__sum')
            total_ftag = Match.objects.order_by('-date')[:19].aggregate(
                    Sum('ftag')).get('ftag__sum')
            league_attack_strength = total_fthg / league_total_games
            league_defense_strength = total_ftag / league_total_games

            # Get team stats
            home_team = get_object_or_404(Team, pk=request.POST.get('home_team'))
            away_team = get_object_or_404(Team, pk=request.POST.get('away_team'))

            home_team_fthg = Match.objects.filter(home_team=home_team).order_by('-date')[:19].aggregate(
                    Sum('fthg')).get('fthg__sum')
            away_team_fthg = Match.objects.filter(away_team=away_team).order_by('-date')[:19].aggregate(
                    Sum('fthg')).get('fthg__sum')
            home_team_ftag = Match.objects.filter(away_team=away_team).order_by('-date')[:19].aggregate(
                    Sum('ftag')).get('ftag__sum')
            away_team_ftag = Match.objects.filter(home_team=home_team).order_by('-date')[:19].aggregate(
                    Sum('ftag')).get('ftag__sum')

            # calculate home team attack strength
            ht_attack_strength = (home_team_fthg / 19) / (total_fthg / league_total_games)
            # calculate away team defense strength
            at_defense_strength = (away_team_fthg / 19) / (total_fthg / league_total_games)

            # calculate expected home goals
            home_goals = ht_attack_strength * at_defense_strength * league_attack_strength

            # calculate away team attack strength
            at_attack_strength = (home_team_ftag / 19) / (total_ftag / league_total_games)
            # calculate home team defense strength
            ht_defense_strength = (away_team_ftag / 19) / (total_ftag / league_total_games)

            # calculate expected away goals
            away_goals = at_attack_strength * ht_defense_strength * league_defense_strength

            probabilities = []
            away_team_probabilities = []

            for i in range(0,5):
                probabilities.append(
                        "{0:.0f}%".format(poisson.pmf(i, home_goals) * 100))
                probabilities.append(
                        "{0:.0f}%".format(poisson.pmf(i, away_goals) * 100))

            return render(request, 'football/results.html', {
                'home_team' : home_team,
                'away_team' : away_team,
                'probs'     : probabilities,
                })
            """
            return HttpResponse("{} {} {} vs {} {} {}".format(
                home_team, 
                home_team_fthg, 
                ht_attack_strength,
                away_team,
                away_team_fthg,
                poisson.pmf(2, home_goals)))
            """
    else:
        form = AnalysisForm()

    return render(request, 'football/analysis.html', {'form': form})

    """
    # Get Total number of matches
    number_of_matches = 0
    total_fthg = 0

    for team in teams:
        number_of_matches += Match.objects.filter(home_team=team).order_by('-date')[:19].count()
    
        # For those games get the number of FTHG and FTAG
        #total_fthg += Match.objects.filter(home_team=team).aggregate(
        #        Sum(F('fthg'))).value
        #print(total_fthg)


    total_fthg = Match.objects.aggregate(
            Sum('fthg')).get('fthg__sum')

    total_ftag = Match.objects.aggregate(
            Sum('ftag')).get('ftag__sum')

    # Get total home team home goals
    home_team = Team.objects.get(id=home_team_id)
    

    # Get total away team home goals
    away_team = Team.objects.get(id=away_team_id)
    
    return HttpResponse("{} {}".format(total_fthg, total_ftag))

    """
