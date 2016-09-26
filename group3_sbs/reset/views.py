from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.mail import send_mail

# Create your views here.

import string
import random


OTP_MESSAGE = "Hello Group3SBS User,\n\r" +\
              "You have recently requested to reset your account password from our reset page.\n\r" +\
              "To continue with resetting your account password please use the provided confirmation code\n\r" +\
              "to verify you have requested a password reset. This confirmation code has an expiration time of\n\r" +\
              "15 minutes, after which you will need to re-submit your password reset request.\n\r" +\
              "\n\r" +\
              "Your confirmation code is: '%s'\n\r" +\
              "\n\r" +\
              "Please continue to reset your password by entering the above confirmation code.\n\r" +\
              "\n\r"


def otpGenerator(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


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
            userOtp = otpGenerator(size=13)
            send_mail(
            'Group 3 SBS Password OTP',
            OTP_MESSAGE%(userOtp),
            'group3sbs@gmail.com',
            [request.POST['email']],
            fail_silently=True,
            )
            print("OTP code has been sent\n")
            #
            # if user's otpRequested and otpTimestamp < 15 minutes
            #   do not send another OTP until the 15 minutes expires
            # else e.g.  user's otpRequested and otpTimestamp > 15 minutes or otpRequested is False 
            #   set user's OTP requested value to true
            #   set the time stamp of the request
            #   set the value of the user's generated OTP
            #
            return render(request, 'reset/otpReset.html')
        else:
            raise Exception('Incorrect username and email combination')

        return render(request, 'reset/reset.html', {'error_message': "Error occurred with submission",})
    except:
        return render(request, 'reset/reset.html')


# OTP Page
def otpUserReset(request):
    print("The otpUserReset function has been called\n")

    try:
        userNameEmailExists = User.objects.filter(username=request.POST['username'],email=request.POST['email']).exists()
        reCaptcha = request.POST['g-recaptcha-response']
        # print("The userNameEmailExists is %s\n"%(userNameEmailExists))
        # print("The reCaptcha is %s\n"%(reCaptcha))
        if(userNameEmailExists is True and reCaptcha):
            print("The username, email, and captcha have been verified\n")
            otpPassword = request.POST['otpPassword']
            print("OTP code is '%s'\n"%(otpPassword))

            newPass = request.POST['newPassword']
            conPass = request.POST['confirmPassword']
            print("New password is '%s'\n"%(newPass))
            print("Confirm password is '%s'\n"%(conPass))
            if(newPass == conPass):
                #
                # if user's otpRequested is False or otpTimestamp > 15 minutes
                #   This OTP is expired, inform the user to re-submit their password reset request
                # else e.g.  user's otpRequested and otpTimestamp < 15 minutes
                #   set the otpRequested to False
                #   clear the otpTimeStamp
                #   reset the user's passwords to the newly provided passwords
                #

                print("New password is '%s'\n"%(newPass))

                return render(request, 'reset/otpReset.html')
            else:
                return render(request, 'reset/otpReset.html', {'error_message': "New password does not match confirm password",})
        else:
            return render(request, 'reset/otpReset.html', {'error_message': "Incorrect username and email combination",})

        return render(request, 'reset/otpReset.html', {'error_message': "Error occurred with submission",})
    except:
        return render(request, 'reset/otpReset.html')

