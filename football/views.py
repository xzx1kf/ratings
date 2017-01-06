from django.shortcuts import render

from django.http import HttpResponse

from .models import Match

from django.contrib.staticfiles.storage import staticfiles_storage

import csv

# Create your views here.
def index(request):
    return HttpResponse("Match Index")

def extract(request):
    # extract data from an excel spreadsheet and 
    # load it into the database. Must check that 
    # there are no duplicates.
    url = staticfiles_storage.url('E0.csv')
    with open(url) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(
                    row['Div'], 
                    row['Date'], 
                    row['HomeTeam'], 
                    row['AwayTeam'],
                    row['FTHG'],
                    row['FTAG'],
                    row['FTR'])
