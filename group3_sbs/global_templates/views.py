from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

# Create your views here.
@login_required
def stop_favicon(request):
    return HttpResponse("favicon.ico")
