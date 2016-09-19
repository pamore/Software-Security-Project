from django.conf.urls import url
from . import views

app_name = 'external'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^account/view/checking/$', views.checking_account, name='checking_account'),
    url(r'^account/view/savings/$', views.savings_account, name='savings_account'),
    url(r'^credit_card/$', views.credit_card, name='credit_card'),
    url(r'^account/credit/checking/$', views.credit_checking, name='credit_checking'),
    url(r'^account/debit/checking/$', views.debit_checking, name='debit_checking'),
    url(r'^account/credit/savings/$', views.credit_savings, name='credit_savings'),
    url(r'^account/debit/savings/$', views.debit_savings, name='debit_savings'),
    url(r'^account/credit/checking/validate/$', views.credit_checking_validate, name='credit_checking_validate'),
    url(r'^account/debit/checking/validate/$', views.debit_checking_validate, name='debit_checking_validate'),
    url(r'^account/credit/savings/validate/$', views.credit_savings_validate, name='credit_savings_validate'),
    url(r'^account/debit/savings/validate/$', views.debit_savings_validate, name='debit_savings_validate'),
]
