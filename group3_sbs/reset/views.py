from django.shortcuts import render

# Create your views here.


# Reset Page
def reset(request):
    return render(request, 'reset/reset.html')


# Reset Page
def resetUser(request):
    return render(request, 'reset/reset.html')

