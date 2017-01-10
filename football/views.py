from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.urls import reverse
from django.views import generic

from .models import Match, Team
from .forms import AnalysisForm

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

    teams = Team.objects.all()

    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            home_team = get_object_or_404(Team, pk=request.POST.get('home_team'))
            away_team = get_object_or_404(Team, pk=request.POST.get('away_team'))
            return HttpResponse("{} vs {}".format(home_team, away_team))
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
