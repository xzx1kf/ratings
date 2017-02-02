from django.conf.urls import url

from . import views

app_name = 'football'
urlpatterns = [
    url(r'^$', views.fixtures, name='fixtures'),
    url(r'^fixtures/$', views.fixtures, name='fixtures'),
    url(r'^fixtures/(?P<match_id>[0-9]+)/$', views.match, name='match'),
    url(r'^tables/$', views.tables, name='tables'),
    ]
