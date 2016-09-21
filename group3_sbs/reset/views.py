from django.shortcuts import render
from django.contrib.auth.models import User

# Create your views here.


# Reset Page
def reset(request):
    return render(request, 'reset/reset.html')


# Reset Page
def resetUser(request):
    print("The resetUser function has been called\n")

    try:
        userNameEmailExists = User.objects.filter(username=request.POST['username'],email=request.POST['email']).exists()
        reCaptcha = request.POST['g-recaptcha-response']
        # print("The userNameEmailExists is %s\n"%(userNameEmailExists))
        # print("The reCaptcha is %s\n"%(reCaptcha))
        if(userNameEmailExists is True and reCaptcha):
            print("The username, email, and captcha have been verified\n")
            # return HttpResponseRedirect(reverse('login:loggedin'))
        else:
            raise Exception('Incorrect username and email combination')

        return render(request, 'reset/reset.html')
    except:
        return render(request, 'reset/reset.html', {'error_message': "Error occurred with submission",})

