from django.conf.urls import url
from . import views

app_name = 'create'
urlpatterns = [
    url(r'^$', views.create, name='create'),
    url(r'^create/$', views.createUser, name='createUser'),
    url(r'^confirmAccount/$', views.confirmAccount, name='confirmAccount'),

]
