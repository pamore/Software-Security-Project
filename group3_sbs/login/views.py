from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here

# Login Page
def signin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login:loggedin'))
    else:
        return render(request, 'login/signin.html')

# Validate login
def loginValidate(request):
    try:
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('login:loggedin'))
        else:
            raise Exception('Incorrect username and password combination')
    except Exception as badPassword:
        return render(request, 'login/signin.html', {'error_message': badPassword[0],})
    except:
        return render(request, 'login/signin.html', {'error_message': "Error occurred with submission",})

# Logout
def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login:signin'))

# Logged in page
@login_required
def loggedin(request):
    return render(request, 'login/test.html')

# Add numbers
def add(request):
    return render(request, 'login/add.html')

def addNumbers(request):
    try:
        number1 = int(request.POST['number1'])
        number2 = int(request.POST['number2'])
        if isinstance(number1, int) and isinstance(number2, int):
            result = number1 + number2
            return render(request, 'login/add.html', {'add1': number1, 'add2': number2, 'result': result,})
        else:
            return render(request, 'login/add.html', {'error_message': "Error occurred with numbers",})
    except Exception as badPassword:
        return render(request, 'login/add.html', {'error_message': badPassword[0],})
