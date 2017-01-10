from django import forms
from .models import Team

class AnalysisForm(forms.Form):
    home_team = forms.ModelChoiceField(queryset=Team.objects.all(), empty_label=None)
    away_team = forms.ModelChoiceField(queryset=Team.objects.all(), empty_label=None)
