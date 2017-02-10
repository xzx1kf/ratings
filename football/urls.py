from django.conf.urls import url

from . import views

app_name = 'football'
urlpatterns = [
    url(r'^$', views.fixtures, name='fixtures'),
    url(r'^fixtures/$', views.fixtures, name='default_fixtures'),
    url(r'^fixtures/(?P<division_id>[0-9]+)/$',
        views.fixtures,
        name='fixtures'),
    url(r'^match/(?P<match_id>[0-9]+)/$', views.match, name='match'),
    url(r'^tables/$', views.tables, name='default_tables'),
    url(r'^tables/(?P<division_id>[0-9]+)/$', views.tables, name='tables'),
    url(r'^teams/$', views.teams, name='default_teams'),
    url(r'^teams/(?P<division_id>[0-9]+)/$', views.teams, name='teams'),
    ]
