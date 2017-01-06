from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Match

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'football/index.html'
    context_object_name = 'latest_matches_list'

    def get_queryset(self):
        """Return the last completed matches."""
        return Match.objects.order_by('-date')[:5]

class DetailView(generic.DetailView):
    model = Match
    template_name = 'football/detail.html'
