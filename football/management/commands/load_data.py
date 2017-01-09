from django.core.management.base import BaseCommand, CommandError
from football.models import Match, Team, Division

from django.utils import timezone

import csv

class Command(BaseCommand):
    help = 'Imports the data into the database'

    def handle(self, *args, **options):
        csv_file = "/home/nick/dev/ratings/football/data/Divisions.csv"

        with open(csv_file) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                division = Division()
                division.name = row['Name']
                division.save()


        csv_file = "/home/nick/dev/ratings/football/data/Teams.csv"

        with open(csv_file) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                team = Team()
                team.name = row['Name']
                team.save()

        csv_file = "/home/nick/dev/ratings/football/data/E0.csv"

        with open(csv_file) as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                match = Match()

                match.division = Division.objects.get(name=row['Div'])

                date = row['Date']
                now_aware = timezone.datetime.strptime(date, "%d/%m/%y")
                now_aware = timezone.make_aware(
                        now_aware, timezone.get_current_timezone())
                match.date = now_aware
                match.home_team = Team.objects.get(name=row['HomeTeam'])
                match.away_team = Team.objects.get(name=row['AwayTeam'])
                match.fthg = row['FTHG']
                match.ftag = row['FTAG']
                match.ftr = row['FTR']
                match.completed = True
                
                # TODO: Add exception handling to catch duplicates.
                # TODO: Change the "Adding" message.
                self.stdout.write("Adding") 
                match.save()
