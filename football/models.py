from django.db import models

# Create your models here.
class Match(models.Model):
    division = models.CharField(max_length=2)
    date = models.DateTimeField('match date')
    home_team = models.CharField(max_length=200)
    away_team = models.CharField(max_length=200)
    fthg = models.IntegerField(default=0)
    ftag = models.IntegerField(default=0)
    ftr = models.CharField(max_length=1)

    def __str__(self):
        return "%s - %s vs %s" % (
                self.date.strftime('%d, %b %Y'), 
                self.home_team, 
                self.away_team)

    class Meta:
        verbose_name_plural = "Matches"
