from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone

from football.models import Team, Division, Match

import csv

class Command(BaseCommand):
    help = 'Imports match data into the database'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        for filename in options['filename']:
            with open(filename) as f:
                reader = csv.DictReader(f)

                counter = 0
                try:
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
                        
                        self.stdout.write("{} - {} vs {}".format(
                            match.date,
                            match.home_team,
                            match.away_team))
                        try:
                            match.save()
                            counter += 1
                        except IntegrityError as e:
                            pass
                except (csv.Error) as e:
                    raise CommandError('csv file {}, line {}: {}'.format(
                        filename,
                        reader.line_num,
                        e,
                    ))
                except Team.DoesNotExist as e:
                    raise CommandError('{} vs {}, line {}: {}'.format(
                        row['HomeTeam'],
                        row['AwayTeam'],
                        reader.line_num,
                        e,
                    ))


                self.stdout.write("Added {} matches.".format(
                    counter))
