from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.

# Internal User Home Page
@login_required
def index(request):
    user = request.user
    if hasattr(user, 'regularemployee'):
        return render(request, 'internal/index.html', {'user_type': "Regular Employee", 'first_name': user.regularemployee.first_name, 'last_name': user.regularemployee.last_name})
    elif hasattr(user, 'systemmanager'):
        return render(request, 'internal/index.html', {'user_type': "System Manager", 'first_name': user.regularemployee.first_name, 'last_name': user.regularemployee.last_name})
    elif hasattr(user, 'administrator'):
        return render(request, 'internal/index.html', {'user_type': "Administrator", 'first_name': user.regularemployee.first_name, 'last_name': user.regularemployee.last_name})
    else:
        return render(request, 'internal/error.html')

# View Noncritical Transactions
@login_required
def noncritical_transactions(request):
    return render(request, 'internal/noncritical_transactions.html')

# View Critical Transactions
@login_required
def critical_transactions(request):
    return render(request, 'internal/critical_transactions.html')
