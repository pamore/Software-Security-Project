from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.mail import send_mail
from global_templates.common_functions import get_any_user_profile, otpGenerator
import time

# Create your views here.

# 15 minute expiration time for OTP
EXPIRATION = 15 * 60

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

DEBUG = False

# Reset Page
def reset(request):
    return render(request, 'reset/reset.html')


# Reset Page
def resetUser(request):
    if DEBUG: print("The resetUser function has been called\n")

    try:
        user_otp = get_any_user_profile(request.POST['username'],request.POST['email'])
        reCaptcha = request.POST['g-recaptcha-response']
        if(user_otp and reCaptcha):
            if DEBUG: print("The username, email, and captcha have been verified\n")

            if((user_otp.otp_timestamp + EXPIRATION) >= int(time.time())):
                #
                # if user's otpRequested and otpTimestamp < 15 minutes
                #   do not send another OTP until the 15 minutes expires
                if DEBUG: print("The current OTP is still valid, do not re-send an OTP until it is expired\n")
                return render(request, 'reset/otpReset.html', {'error_message': "OTP recently sent, please check email",})
            else:
                # else e.g.  user's otpRequested and otpTimestamp > 15 minutes or otpRequested is False
                #   set user's OTP requested value to true
                #   set the time stamp of the request
                #   set the value of the user's generated OTP
                #
                if DEBUG: print("Generate an OTP code\n")
                user_otp.otp_pass = otpGenerator(size=13)
                user_otp.otp_timestamp = int(time.time())
                user_otp.save()
                if DEBUG: print("OTP pass and timestamp set and saved\n")
                check = send_mail(
                'Group 3 SBS Password OTP',
                OTP_MESSAGE%(user_otp.otp_pass),
                'group3sbs@gmail.com',
                [user_otp.email],
                fail_silently=False,
                )
                if DEBUG: print("Check is %d\n"%(check))
                while(check == 0):
                    check = send_mail(
                    'Group 3 SBS Password OTP',
                    OTP_MESSAGE%(user_otp.otp_pass),
                    'group3sbs@gmail.com',
                    [user_otp.email],
                    fail_silently=False,
                    )   
                if DEBUG: print("Password reset OTP code has been sent\n")
                return render(request, 'reset/otpReset.html', {'error_message': "OTP sent, please check email",})
        else:
            return render(request, 'reset/reset.html', {'error_message': "Incorrect username and email combination or missing reCaptcha",})
    except:
        if DEBUG: print("Threw an exception, did not complete try-block")
        return render(request, 'reset/reset.html')


# OTP Page
def otpUserReset(request):
    if DEBUG: print("The otpUserReset function has been called\n")

    try:
        user_otp = get_any_user_profile(request.POST['username'],request.POST['email'])
        reCaptcha = request.POST['g-recaptcha-response']
        if(user_otp and reCaptcha):
            if DEBUG: print("The username, email, and captcha have been verified\n")
            otpPassword = request.POST['otpPassword']
            if DEBUG: print("OTP code is '%s'\n"%(otpPassword))

            newPass = request.POST['newPassword']
            conPass = request.POST['confirmPassword']
            if DEBUG: print("New password is '%s'\n"%(newPass))
            if DEBUG: print("Confirm password is '%s'\n"%(conPass))
            if(newPass == conPass):
                #
                # if user's otpRequested is False or otpTimestamp > 15 minutes
                #   This OTP is expired, inform the user to re-submit their password reset request
                if((user_otp.otp_timestamp + EXPIRATION) >= int(time.time())):
                    if(user_otp.otp_pass == otpPassword):
                        if DEBUG: print("Successfully reset the user password")
                        user_otp.user.set_password(newPass)
                        user_otp.user.save()
                        user_otp.otp_timestamp = time.time() - EXPIRATION
                        user_otp.save()
                        return render(request, 'reset/otpReset.html', {'error_message': "Succesfully reset account password!",})
                    else:
                        return render(request, 'reset/otpReset.html', {'error_message': "Incorrect OTP password",})
                else:
                    return render(request, 'reset/reset.html', {'error_message': "OTP password is expired, re-submit password reset request",})
            else:
                return render(request, 'reset/otpReset.html', {'error_message': "New password does not match confirm password",})
        else:
            return render(request, 'reset/otpReset.html', {'error_message': "Incorrect username and email combination or missing reCaptcha",})

        return render(request, 'reset/otpReset.html', {'error_message': "Error occurred with submission",})
    except:
        return render(request, 'reset/otpReset.html')

