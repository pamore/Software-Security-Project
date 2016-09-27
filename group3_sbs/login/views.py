from axes.decorators import watch_login
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from group3_sbs.settings import *
from global_templates.common_functions import validate_user_type

# Create your views here

# Lockout Page
@never_cache
def lock_out(request):
    return render(request, 'login/lock_out.html')

# Login Page
@never_cache
def signin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login:loggedin'))
    else:
        return render(request, 'login/signin.html')

# Validate login
@never_cache
@watch_login
def loginValidate(request):
    try:
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None and validate_user_type(user, request.POST['user_type']):
            login(request, user)
            return HttpResponseRedirect(reverse('login:loggedin'))
        else:
            raise Exception('Incorrect username and password combination')
    except Exception as badPassword:
        return render(request, 'login/signin.html', {'error_message': badPassword[0],}, status=401)
    except:
        return render(request, 'login/signin.html', {'error_message': "Error occurred with submission",}, status=401)

# Logout
@never_cache
def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login:signin'))

# Logged in page
@never_cache
@login_required
def loggedin(request):
    user = request.user
    if (hasattr(user, 'regularemployee') or hasattr(user, 'systemmanager') or hasattr(user, 'administrator')) and (hasattr(user, 'individualcustomer') or hasattr(user, 'merchantorganization')):
        user.delete()
        return HttpResponseRedirect(reverse('login:signin'))
    elif hasattr(user, 'regularemployee') or hasattr(user, 'systemmanager') or hasattr(user, 'administrator'):
        return HttpResponseRedirect(reverse('internal:index'))
    elif hasattr(user, 'individualcustomer') or hasattr(user, 'merchantorganization'):
        return HttpResponseRedirect(reverse('external:index'))
    else:
        return HttpResponseRedirect(reverse('login:signout'))
