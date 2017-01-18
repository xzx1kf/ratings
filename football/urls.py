from django.conf.urls import url

from . import views

app_name = 'football'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^analysis/$', views.analysis, name='analysis'),
    url(r'^fixtures/$', views.fixtures, name='fixtures'),
    url(r'^fixtures/(?P<match_id>[0-9]+)/$', views.match, name='match'),
    ]
