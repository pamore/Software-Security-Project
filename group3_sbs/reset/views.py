from axes.decorators import watch_login
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from global_templates.common_functions import get_any_user_profile, otpGenerator, validate_email, validate_password, validate_username
from global_templates.constants import OTP_EXPIRATION_DATE, OTP_LENGTH
from M2Crypto import RSA, EVP
import M2Crypto, time

# Create your views here.

OTP_MESSAGE = "Hello Group3SBS User,\n\r" +\
              "You have recently requested to reset your account password from our reset page.\n\r" +\
              "To continue with resetting your account password please use the provided confirmation code in order " +\
              "to verify you have requested a password reset. This confirmation code has an expiration time of " +\
              "15 minutes, after which you will need to re-submit your password reset request.\n\r" +\
              "\n\r" +\
              "Your confirmation code is: %s\n\r" +\
              "\n\r" +\
              "Please continue to reset your password by entering the confirmation code.\n\r" +\
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
            if((user_otp.otp_timestamp + OTP_EXPIRATION_DATE) >= int(time.time())):
                #
                # if user's otpRequested and otpTimestamp < 15 minutes
                #   do not send another OTP until the 15 minutes expires
                if DEBUG: print("The current OTP is still valid, re-send current OTP until it is expired\n")
                try:
                    cert = user_otp.certificate
                    cert = str(cert)
                    certificate = M2Crypto.X509.load_cert_string(cert)
                    public_key = certificate.get_pubkey()
                    rsa_public_key = public_key.get_rsa()
                    signed = rsa_public_key.public_encrypt(user_otp.otp_pass, M2Crypto.RSA.pkcs1_oaep_padding)
                except:
                    signed = None
                if signed:
                    mail = EmailMessage("CSE545 Group3 SBS Password Recovery OTP", OTP_MESSAGE%('encrypted with your public key and attached in the document'),'group3sbs@gmail.com',[user_otp.email])
                    mail.attach('otp.bin', signed, 'application/x-binary')
                else:
                    mail = EmailMessage("CSE545 Group3 SBS Password Recovery OTP", OTP_MESSAGE%(user_otp.otp_pass),'group3sbs@gmail.com',[user_otp.email])
                mail.send()
                return render(request, 'reset/otpReset.html', {'error_message': "OTP recently sent, please check email",})
            else:
                # else e.g.  user's otpRequested and otpTimestamp > 15 minutes or otpRequested is False
                #   set user's OTP requested value to true
                #   set the time stamp of the request
                #   set the value of the user's generated OTP
                #
                if DEBUG: print("Generate an OTP code\n")
                user_otp.otp_pass = otpGenerator(size=OTP_LENGTH)
                user_otp.otp_timestamp = int(time.time())
                user_otp.save()
                if DEBUG: print("OTP pass and timestamp set and saved\n")
                try:
                    cert = user_otp.certificate
                    cert = str(cert)
                    certificate = M2Crypto.X509.load_cert_string(cert)
                    public_key = certificate.get_pubkey()
                    rsa_public_key = public_key.get_rsa()
                    signed = rsa_public_key.public_encrypt(user_otp.otp_pass, M2Crypto.RSA.pkcs1_oaep_padding)
                except:
                    signed = None
                if signed:
                    mail = EmailMessage("CSE545 Group3 SBS Password Recovery OTP", OTP_MESSAGE%('encrypted with your public key and attached in the document'),'group3sbs@gmail.com',[user_otp.email])
                    mail.attach('otp.bin', signed, 'application/x-binary')
                else:
                    mail = EmailMessage("CSE545 Group3 SBS Password Recovery OTP", OTP_MESSAGE%(user_otp.otp_pass),'group3sbs@gmail.com',[user_otp.email])
                mail.send()
                if DEBUG: print("Password reset OTP code has been sent\n")
                return render(request, 'reset/otpReset.html', {'error_message': "OTP sent, please check email",})
        else:
            return render(request, 'reset/reset.html', {'error_message': "Incorrect username and email combination or missing reCaptcha",})
    except:
        if DEBUG: print("Threw an exception, did not complete try-block")
        return render(request, 'reset/reset.html')


# OTP Page
@watch_login
def otpUserReset(request):
    if DEBUG: print("The otpUserReset function has been called\n")

    try:
        username = request.POST['username']
        email = request.POST['email']
        reCaptcha = request.POST['g-recaptcha-response']
        if not validate_email(email=email) or not validate_username(username=username):
            return render(request, 'reset/otpReset.html', {'error_message': "Incorrect username and email format",}, status=401)
        user_otp = get_any_user_profile(username, email)
        if(user_otp and reCaptcha):
            if DEBUG: print("The username, email, and captcha have been verified\n")
            otpPassword = request.POST['otpPassword']
            if DEBUG: print("OTP code is '%s'\n"%(otpPassword))

            newPass = request.POST['newPassword']
            conPass = request.POST['confirmPassword']
            if DEBUG: print("New password is '%s'\n"%(newPass))
            if DEBUG: print("Confirm password is '%s'\n"%(conPass))
            if newPass == conPass:
                if not validate_password(newPass) or not validate_password(conPass):
                    return render(request, 'reset/otpReset.html', {'error_message': "New password does not meet requirements",}, status=401)
                #
                # if user's otpRequested is False or otpTimestamp > 15 minutes
                #   This OTP is expired, inform the user to re-submit their password reset request
                if((user_otp.otp_timestamp + OTP_EXPIRATION_DATE) >= int(time.time())):
                    if(user_otp.otp_pass == otpPassword):
                        if DEBUG: print("Successfully reset the user password")
                        user_otp.user.set_password(newPass)
                        user_otp.user.save()
                        user_otp.otp_timestamp = time.time() - OTP_EXPIRATION_DATE
                        user_otp.save()
                        return render(request, 'reset/otpReset.html', {'error_message': "Succesfully reset account password!",})
                    else:
                        return render(request, 'reset/otpReset.html', {'error_message': "Incorrect OTP password",}, status=401)
                else:
                    return render(request, 'reset/reset.html', {'error_message': "OTP password is expired, re-submit password reset request",}, status=401)
            else:
                return render(request, 'reset/otpReset.html', {'error_message': "New password does not match confirm password",}, status=401)
        else:
            return render(request, 'reset/otpReset.html', {'error_message': "Incorrect username and email combination or missing reCaptcha",}, status=401)

        return render(request, 'reset/otpReset.html', {'error_message': "Error occurred with submission",}, status=401)
    except:
        return render(request, 'reset/otpReset.html', status=401)
