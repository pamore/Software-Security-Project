from django.conf.urls import url
from . import views

app_name = 'reset'
urlpatterns = [
    url(r'^$', views.reset, name='reset'),
    url(r'^reset/$', views.resetUser, name='resetUser'),

]
