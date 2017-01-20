from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from football.models import Team, Division

import csv

class Command(BaseCommand):
    help = 'Imports match data into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file';, nargs='+', type=string)

    def handle(self, *args, **options):
        for csv_file in options['csv_file']:
            try:
                with open(csv_file) as csv:
                    reader = csv.DictReader(csv)
            except csv.Error:
                raise CommandError('csv file "%s" could not be opened' % csv_file)

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
