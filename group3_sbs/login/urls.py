from django.conf.urls import url
from . import views

app_name = 'login'
urlpatterns = [
    url(r'^$', views.signin, name='signin'),
    url(r'^signout/$', views.signout, name='signout'),
    url(r'^loggedin/$', views.loggedin, name='loggedin'),
    url(r'^validate/$', views.loginValidate, name='loginValidate'),
    url(r'^locked_out/$', views.lock_out, name='lock_out'),
]
