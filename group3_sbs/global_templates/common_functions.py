from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from global_templates.transaction_descriptions import debit_description, credit_description, transfer_description, payment_description
from global_templates.constants import MAX_BALANCE, MIN_BALANCE, NONCRITICAL_TRANSACTION_LIMIT
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction

def validate_amount(amount):
    if amount > MAX_BALANCE or amount < MIN_BALANCE:
        return False
    else:
        return True
