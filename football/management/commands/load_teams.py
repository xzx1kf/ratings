from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from football.models import Team, Division

import csv

class Command(BaseCommand):
    help = 'Imports team data into the database'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        for filename in options['filename']:
            with open(filename) as f:
                reader = csv.DictReader(f)

                try:
                    for row in reader:
                        team = Team()
                        team.name = row['Name']
                        team.division = Division.objects.get(name=row['Division'])
                        try:
                            team.save()
                        except IntegrityError as e:
                            t = Team.objects.get(name=team.name)
                            t.division = team.division
                            self.stdout.write("{} - {}".format(
                                t.name,
                                t.division))
                            t.save()
                            pass
                except (csv.Error) as e:
                    raise CommandError('csv file {}, line {}: {}'.format(
                        filename,
                        reader.line_num,
                        e,
                    ))
