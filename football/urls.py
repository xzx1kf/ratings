from django.conf.urls import url

from . import views

app_name = 'football'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^extract/$', views.extract, name='extract'),
]
