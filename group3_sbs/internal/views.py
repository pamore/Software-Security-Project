from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from global_templates.common_functions import is_administrator, is_regular_employee, is_system_manager
from external.models import ExternalNoncriticalTransaction, ExternalCriticalTransaction

# Create your views here.

# Internal User Home Page
@login_required
def index(request):
    user = request.user
    if is_regular_employee(user):
        return render(request, 'internal/index.html', {'user_type': "Regular Employee", 'first_name': user.regularemployee.first_name, 'last_name': user.regularemployee.last_name})
    elif is_system_manager(user):
        return render(request, 'internal/index.html', {'user_type': "System Manager", 'first_name': user.systemmanager.first_name, 'last_name': user.systemmanager.last_name})
    elif is_administrator(user):
        return render(request, 'internal/index.html', {'user_type': "Administrator", 'first_name': user.administrator.first_name, 'last_name': user.administrator.last_name})
    else:
        return render(request, 'internal/error.html')

# View Noncritical Transactions
@login_required
def noncritical_transactions(request):
    user = request.user
    if is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_regular_employee(user) or is_system_manager(user):
        transactions = ExternalNoncriticalTransaction.objects.order_by('time_created')
        return render(request, 'internal/noncritical_transactions.html', {'transactions': transactions})
    else:
        return render(request, 'internal/error.html')

# View Critical Transactions
@login_required
def critical_transactions(request):
    user = request.user
    if is_regular_employee(user) or is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_system_manager(user):
        transactions = ExternalCriticalTransaction.objects.order_by('time_created')
        return render(request, 'internal/critical_transactions.html', {'transactions': transactions})
    else:
        return render(request, 'internal/error.html')
