from django import forms

class AnalysisForm(forms.Form):
    home_team = forms.CharField(label='Home Team', max_length=200)
    away_team = forms.CharField(label='Away Yeam', max_length=200)
