from django.conf.urls import url
from . import views

app_name = 'internal'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^transaction/noncritical/$', views.noncritical_transactions, name='noncritical_transactions'),
    url(r'^transaction/critical/$', views.critical_transactions, name='critical_transactions'),
]
