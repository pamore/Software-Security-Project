from axes.decorators import watch_login
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader, RequestContext
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from group3_sbs.settings import *
from global_templates.constants import OTP_EXPIRATION_DATE, TRUSTED_DEVICE_EXPIRY
from global_templates.common_functions import validate_password, validate_user_type, validate_username, get_user_email, get_any_user_profile, get_user_trusted_keys, trustedDeviceKeyGenerator, otpGenerator
from django.core.mail import send_mail
import datetime, time

# Create your views here
DEBUG = False

TRUSTED_DEVICE_MESSAGE =  "Hello Group3SBS User,\n\r" +\
                          "You have recently attempted logging in to your account from an unrecognized new device.\n\r" +\
                          "To continue with verifying the device for use please use the provided confirmation code\n\r" +\
                          "to verify you trust this device for future logins. This confirmation code has an expiration time of\n\r" +\
                          "15 minutes, after which you will need to attempt logging in again to re-start device verification.\n\r" +\
                          "\n\r" +\
                          "Your confirmation code is: %s\n\r" +\
                          "\n\r" +\
                          "Please continue to verify the device by entering the above confirmation code.\n\r" +\
                          "\n\r"

# Verify Device
def deviceVerify(request):
    if DEBUG: print("The deviceVerify function has been called\n")
    try:
        profile = get_any_user_profile(request.POST['username'],request.POST['email'])
        reCaptcha = request.POST['g-recaptcha-response']
        if(profile and reCaptcha):
            if DEBUG: print("The username, email, and captcha have been verified\n")
            otpPassword = request.POST['otpPassword']
            if DEBUG: print("OTP code is '%s'\n"%(otpPassword))
            if((profile.otp_timestamp + OTP_EXPIRATION_DATE) >= int(time.time())):
                if(profile.otp_pass == otpPassword):
                    if DEBUG: print("Confirmed the user OTP key")
                    trusted_keys = get_user_trusted_keys(profile)
                    new_key = trustedDeviceKeyGenerator()

                    if(trusted_keys is None):
                        trusted_keys = [new_key]
                    elif(len(trusted_keys) == 10):
                        trusted_keys.pop()
                        trusted_keys.insert(0, new_key)
                    else:
                        trusted_keys.insert(0, new_key)

                    if DEBUG: print("trusted keys is:")
                    if DEBUG: print(trusted_keys)
                    if DEBUG: print("Update list of keys")
                    serial_keys = ''
                    for key in trusted_keys:
                        serial_keys += key + ';'

                    if DEBUG: print("Serialized keys '%s'"%(serial_keys))

                    profile.trusted_device_keys = serial_keys
                    profile.otp_timestamp = time.time() - OTP_EXPIRATION_DATE
                    profile.save()

                    if DEBUG: print("Update user profile keys and OTP")

                    oneYear = datetime.datetime.now()
                    oneYear.replace(year = oneYear.year + 1)

                    if DEBUG: print("Get cookie expiration")
                    user = profile.user
                    login(request, user)
                    response = redirect('login:signin')
                    if DEBUG: print("Generate response")
                    response.set_cookie('trusted_device',new_key,max_age=TRUSTED_DEVICE_EXPIRY)
                    if DEBUG: print("Finish verifying device, return response")
                    return response
                else:
                    return render(request, 'login/deviceVerify.html', {'error_message': "Incorrect OTP password",})
            else:
                return HttpResponseRedirect(reverse('login:signin'))
        else:
            return render(request, 'login/deviceVerify.html', {'error_message': "Incorrect username and email combination or missing reCaptcha",})
    except:
        if DEBUG: print("Threw an exception, did not complete try-block")
        return render(request, 'login/deviceVerify.html')

# Lockout Page
@never_cache
def lock_out(request):
    return render(request, 'login/lock_out.html')

# Logged in page
@never_cache
@login_required
def loggedin(request):
    user = request.user
    if (hasattr(user, 'regularemployee') or hasattr(user, 'systemmanager') or hasattr(user, 'administrator')) and (hasattr(user, 'individualcustomer') or hasattr(user, 'merchantorganization')):
        user.delete()
        return HttpResponseRedirect(reverse('login:signin'))
    else:
        # if there is a cookie for the device
        #   get the user profile
        #   check to see if the cookie stored on the device is in the list of trusted device keys
        #   if the device is trusted
        #       proceed to log in
        #   else
        #       send the user an OTP for verifying the device
        #       redirect the user to an OTP device verification page
        # else
        #   send the user an OTP for verifying the device
        #   redirect the user to an OTP device verification page

        user_email = get_user_email(user)
        profile = get_any_user_profile(user.username, user_email)
        if DEBUG: print("Current cookies:")
        if DEBUG: print request.COOKIES
        trusted_key = request.COOKIES.get('trusted_device')
        if(trusted_key != ''):
            if DEBUG: print("The 'trusted_device' cookie is present\n")
            trusted_keys = get_user_trusted_keys(profile)
            if(trusted_keys is None):
               trusted_keys = []

            if DEBUG: print("The 'trusted_device' cookie value is '%s'\n"%(trusted_key))

            if(not (trusted_key in trusted_keys)):
                if DEBUG: print("The 'trusted_device' cookie is not in the list\n")
                logout(request)
                return send_device_verify_otp(request, profile)
            else:
                if DEBUG: print("trusted key is:")
                if DEBUG: print trusted_key
                update_key = trustedDeviceKeyGenerator()
                if DEBUG: print("updated key is:")
                if DEBUG: print update_key
                trusted_keys.pop(trusted_keys.index(trusted_key))
                trusted_keys.insert(0,update_key)

                if DEBUG: print("trusted keys is:")
                if DEBUG: print trusted_keys
                if DEBUG: print("Update list of keys")
                serial_keys = ''
                for key in trusted_keys:
                    serial_keys += key + ';'

                if DEBUG: print("Serialized keys '%s'"%(serial_keys))

                profile.trusted_device_keys = serial_keys
                profile.otp_timestamp = time.time() - OTP_EXPIRATION_DATE
                profile.save()

            if hasattr(user, 'regularemployee') or hasattr(user, 'systemmanager') or hasattr(user, 'administrator'):
                response = redirect('internal:index')
                response.set_cookie('trusted_device',update_key,max_age=TRUSTED_DEVICE_EXPIRY)
                return response
            elif hasattr(user, 'individualcustomer') or hasattr(user, 'merchantorganization'):
                response = redirect('external:index')
                response.set_cookie('trusted_device',update_key,max_age=TRUSTED_DEVICE_EXPIRY)
                return response
            else:
                return HttpResponseRedirect(reverse('login:signout'))
        else:
            if DEBUG: print("The 'trusted_device' cookie is not present\n")
            logout(request)
            return send_device_verify_otp(request, profile)

# Validate login
@never_cache
@watch_login
def loginValidate(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        reCaptcha = request.POST['g-recaptcha-response']
        user = authenticate(username=username, password=password)
        if not reCaptcha:
            raise Exception('Are you a bot? Please fill out Recapchta.')
        if user is not None and validate_user_type(user, request.POST['user_type']) and validate_username(username=username) and validate_password(password=password):
            login(request, user)
            return HttpResponseRedirect(reverse('login:loggedin'))
        else:
            raise Exception('Incorrect username and password combination')
    except Exception as badPassword:
        return render(request, 'login/signin.html', {'error_message': badPassword[0],}, status=401)
    except:
        return render(request, 'login/signin.html', {'error_message': "Error occurred with submission",}, status=401)

# Login Page
@never_cache
def signin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login:loggedin'))
    else:
        return render(request, 'login/signin.html')

# Logout
@never_cache
def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login:signin'))

# Verify OTP
def send_device_verify_otp(request, profile):
    if((profile.otp_timestamp + OTP_EXPIRATION_DATE) >= int(time.time())):
        #
        # if user's otpRequested and otpTimestamp < 15 minutes
        #   do not send another OTP until the 15 minutes expires
        if DEBUG: print("The current OTP is still valid, re-send current OTP until it is expired\n")
        check = send_mail(
        'Group 3 SBS Trusted Device OTP',
        TRUSTED_DEVICE_MESSAGE%(profile.otp_pass),
        'group3sbs@gmail.com',
        [profile.email],
        fail_silently=False,
        )
        if DEBUG: print("Check is %d\n"%(check))
        print(profile.otp_pass)
        while(check == 0):
            check = send_mail(
            'Group 3 SBS Trusted Device OTP',
            TRUSTED_DEVICE_MESSAGE%(profile.otp_pass),
            'group3sbs@gmail.com',
            [profile.email],
            fail_silently=False,
            )
        return render(request, 'login/deviceVerify.html', {'error_message': "OTP recently sent, please check email",})
    else:
        # else e.g.  user's otpRequested and otpTimestamp > 15 minutes or otpRequested is False
        #   set the time stamp of the request
        #   set the value of the user's generated OTP
        #
        if DEBUG: print("Generate an OTP code\n")
        profile.otp_pass = otpGenerator(size=13)
        profile.otp_timestamp = int(time.time())
        profile.save()
        if DEBUG: print("OTP pass and timestamp set and saved\n")
        print(profile.otp_pass)
        check = send_mail(
        'Group 3 SBS Trusted Device OTP',
        TRUSTED_DEVICE_MESSAGE%(profile.otp_pass),
        'group3sbs@gmail.com',
        [profile.email],
        fail_silently=False,
        )
        if DEBUG: print("Check is %d\n"%(check))
        while(check == 0):
            check = send_mail(
            'Group 3 SBS Trusted Device OTP',
            TRUSTED_DEVICE_MESSAGE%(profile.otp_pass),
            'group3sbs@gmail.com',
            [profile.email],
            fail_silently=False,
            )
        if DEBUG: print("Trusted device OTP code has been sent\n")
        return render(request, 'login/deviceVerify.html', {'error_message': "OTP sent, please check email",})
