from django import forms
from .models import Team, Division

class AnalysisForm(forms.Form):
    premiership = Division.objects.filter(name='E0')
    home_team = forms.ModelChoiceField(queryset=Team.objects.filter(division=premiership), empty_label=None)
    away_team = forms.ModelChoiceField(queryset=Team.objects.filter(division=premiership), empty_label=None)
