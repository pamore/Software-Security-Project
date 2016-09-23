from django.conf.urls import url
from . import views

app_name = 'internal'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^transaction/noncritical/$', views.noncritical_transactions, name='noncritical_transactions'),
    url(r'^transaction/noncritical/(?P<transaction_id>[1-9][0-9]*)/approve/$', views.validate_noncritical_transaction_approval, name='validate_noncritical_transaction_approval'),
    url(r'^transaction/noncritical/(?P<transaction_id>[1-9][0-9]*)/deny/$', views.validate_noncritical_transaction_denial, name='validate_noncritical_transaction_denial'),
    url(r'^transaction/critical/$', views.critical_transactions, name='critical_transactions'),
    url(r'^transaction/critical/(?P<transaction_id>[1-9][0-9]*)/approve/$', views.validate_critical_transaction_approval, name='validate_critical_transaction_approval'),
    url(r'^transaction/critical/(?P<transaction_id>[1-9][0-9]*)/deny/$', views.validate_critical_transaction_denial, name='validate_critical_transaction_denial'),
    url(r'^external_user/profile/(?P<external_user_id>[1-9][0-9]*)/view/$', views.view_external_account, name='view_external_account'),
    url(r'^external_user/profile/request_access/$', views.external_user_account_access_request, name='external_user_account_access_request'),
    url(r'^external_user/profile/request_access/validate/$', views.validate_external_account_access_request, name='validate_external_account_access_request'),

]
