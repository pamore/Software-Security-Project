from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.mail import send_mail
from global_templates.common_functions import get_any_user_profile, otpGenerator, get_new_routing_number, get_new_credit_card_number, validate_account_info, validate_certificate, validate_email, validate_password, validate_username
from global_templates.constants import INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, OTP_LENGTH, STATES
from external.models import SavingsAccount, CheckingAccount, CreditCard, IndividualCustomer, MerchantOrganization
import logging

logger = logging.getLogger('create')

# Create your views here.
DEBUG = False

NEW_ACCOUNT_MESSAGE = "Hello New User,\n\r" +\
                      "You have recently requested a new Group3SBS account.\n\r" +\
                      "To continue with creating your account please use the provided confirmation code to continue with your account creation.\n\r" +\
                      "You will be prompted with what account type you would like to create.\n\r" +\
                      "\n\r" +\
                      "Your requested username is: %s\n\r" +\
                      "\n\r" +\
                      "\n\r" +\
                      "Your confirmation code is: %s\n\r" +\
                      "\n\r" +\
                      "Please continue to create your account by entering the above confirmation code on the account creation page when prompted.\n\r" +\
                      "\n\r"

CREATED_ACCOUNT_MESSAGE = "Hello %s,\n\r" +\
                          "You have recently created a new Group3SBS account.\n\r" +\
                          "\n\r" +\
                          "Your account routing number is: %07d\n\r" +\
                          "\n\r" +\
                          "To continue please login to begin using your new account.\n\r" +\
                          "\n\r"

# Create Account Page
def create(request):
    return render(request, 'create/create.html')

def createUser(request):
    if DEBUG: print("The createUser function has been called\n")

    try:
        username = request.POST['username']
        email = request.POST['email']
        if not validate_email(email=email) or not validate_username(username=username):
            return render(request, 'create/create.html', {'error_message': "Username is unavailable.",})
        existing_user = get_any_user_profile(username, email)
        init_user = User.objects.filter(username=username)
        reCaptcha = request.POST['g-recaptcha-response']
        if(reCaptcha):
            if(existing_user):
                # if the user already fully exists (e.g. has a full profile)
                #   return error that username is unavailable
                if DEBUG: print("The full user profile already exists\n")
                logger.info("Full user account '%s' already exists"%(username))
                return render(request, 'create/create.html', {'error_message': "Username not correct. Try another.",})

            elif(init_user):
                # else if the username exists may have a pre-liminary account created (e.g. only a User type)
                init_email = User.objects.filter(username=username,email=email)
                if(init_email):
                    #   if email matches User email
                    #       resend their password/OTP and tell them to check email
                    #       re-direct them to final account creation
                    init_email = User.objects.get(username=username,email=email)
                    if DEBUG: print("The init user email exists in the system\n")
                    logger.info("Temporary user account '%s' already exists"%(username))
                    check = send_mail(
                    'Group 3 SBS New Account',
                    NEW_ACCOUNT_MESSAGE%(init_email.username,init_email.first_name),
                    'group3sbs@gmail.com',
                    [init_email.email],
                    fail_silently=False,
                    )
                    if DEBUG: print("Check is %d\n"%(check))
                    while(check == 0):
                        check = send_mail(
                        'Group 3 SBS New Account',
                        NEW_ACCOUNT_MESSAGE%(init_email.username,init_email.first_name),
                        'group3sbs@gmail.com',
                        [init_email.email],
                        fail_silently=False,
                        )
                        if DEBUG: print("Check is %d\n"%(check))
                    if DEBUG: print("New Account OTP code has been sent\n")
                    return render(request, 'create/confirmAccount.html', {'error_message': "New Account email sent, please check email","STATES" : STATES})
                else:
                    #   else
                    #       return error that new account username/email mismatch
                    logger.info("Temporary user account '%s' username/email mismatch"%(username))
                    return render(request, 'create/create.html', {'error_message': "Username and email account mismatch.",})

            else:
                # else
                #   the user is a new user
                #   create a new user object, assign the username, email, and OTP as first_name temporarily
                #   send email with new account information
                #   redirect the user
                if DEBUG: print("Create temporary user account object\n")
                new_user = User.objects.create_user(username=username,email=email,first_name=otpGenerator(size=OTP_LENGTH))
                new_user.save()
                if DEBUG: print("Initial account created and saved\n")
                logger.info("Temporary user account '%s' created"%(username))
                check = send_mail(
                'Group 3 SBS New Account',
                NEW_ACCOUNT_MESSAGE%(new_user.username,new_user.first_name),
                'group3sbs@gmail.com',
                [new_user.email],
                fail_silently=False,
                )
                if DEBUG: print("Check is %d\n"%(check))
                while(check == 0):
                    check = send_mail(
                    'Group 3 SBS New Account',
                    NEW_ACCOUNT_MESSAGE%(new_user.username,new_user.first_name),
                    'group3sbs@gmail.com',
                    [new_user.email],
                    fail_silently=False,
                    )
                if DEBUG: print("New Account info and OTP code has been sent\n")
                return render(request, 'create/confirmAccount.html', {'error_message': "New Account email sent, please check email", "STATES" : STATES})
    except:
        if DEBUG: print("Threw an exception, did not complete try-block")
        return render(request, 'create/create.html')

def confirmAccount(request):
    if DEBUG: print("The confirmUser function has been called\n")

    # if existing_user
    #   return error that the user account already exists
    # else if the init user exists
    #   if the init user email and OTP match
    #       delete the init user account to make a fresh user
    #       take the user input info details and create a corresponding account type
    #       display message that the new account has been created
    #   else
    #       return error that the email or OTP do match the account
    # else
    #   redirect the user to the account creation page and display message to create a new account

    try:
        user_type = request.POST['user_type']
        username = request.POST['username']
        email = request.POST['email']
        newPassword =  request.POST['newPassword']
        confirmPassword = request.POST['confirmPassword']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        address = request.POST['address']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zipcode']
        personalcode = request.POST['personalcode']
        certificate = request.POST.get('certificate')
        existing_user = get_any_user_profile(username,email)
        init_user = User.objects.filter(username=username)
        reCaptcha = request.POST['g-recaptcha-response']
        if DEBUG: print("Checking the reCaptcha\n")
        if(reCaptcha):
            if DEBUG: print("reCaptcha has been entered\n")
            if(existing_user):
                # if the user already fully exists (e.g. has a full profile)
                #   return error that username is unavailable
                if DEBUG: print("The full user profile already exists\n")
                logger.info("Full user account '%s' already exists"%(username))
                return render(request, 'create/create.html', {'error_message': "User already exists, please login or reset password.", "STATES" : STATES})

            elif(init_user):
                # else if the username exists may have a pre-liminary account created (e.g. only a User type)
                if DEBUG: print("Filter for the init user\n")
                if not validate_account_info(user_type=user_type, username=username, email=email, first_name=firstname, last_name=lastname, address=address, city=city, state=state,zipcode=zipcode, personal_code=personalcode):
                    logger.info("User '%s' invalid user input"%(username))
                    return render(request, 'create/confirmAccount.html', {'error_message': "User information not correct.", "STATES" : STATES})
                init_email = User.objects.filter(username=username,email=email,first_name=request.POST['otpPassword'])
                if(init_email):
                    if DEBUG: print("Located the init user\n")
                    if(newPassword == confirmPassword):
                        if DEBUG: print("The new password and confirm new password match\n")
                        if not validate_password(newPassword) or not validate_password(confirmPassword):
                            return render(request, 'create/confirmAccount.html', {'error_message': "Passsword incorrectly formatted.", "STATES" : STATES})
                        newUser = User.objects.get(username=username,email=email)
                        if DEBUG: print("Save new user\n")
                        new_routing = get_new_routing_number()
                        if DEBUG: print("New routing number is %d\n"%(new_routing))
                        checkingaccount = CheckingAccount.objects.create(
                                            interest_rate=0.03,
                                            routing_number=new_routing,
                                            current_balance=0.00,
                                            active_balance=0.00)
                        checkingaccount.save()
                        if DEBUG: print("Create and save checkings\n")

                        savingsaccount = SavingsAccount.objects.create(
                                            interest_rate=0.03,
                                            routing_number=new_routing,
                                            current_balance=0.00,
                                            active_balance=0.00)
                        savingsaccount.save()
                        if DEBUG: print("Create and save savings\n")

                        creditcard = CreditCard.objects.create(
                                            interest_rate=0.03,
                                            creditcard_number=get_new_credit_card_number(),
                                            charge_limit=1000.00,
                                            remaining_credit=1000.00,
                                            late_fee=15.00,
                                            days_late=0)
                        creditcard.save()
                        if DEBUG: print("Create and save credit card\n")

                        new_account = None
                        if not validate_certificate(certificate):
                            certificate = None
                        else:
                            ceriticate = str(certificate)
                        if(user_type == INDIVIDUAL_CUSTOMER):
                            if DEBUG: print("Individual account type\n")
                            individualcustomer = IndividualCustomer.objects.create(
                                                first_name=firstname,
                                                last_name=lastname,
                                                email=email,
                                                street_address=address,
                                                city=city,
                                                state=state,
                                                zipcode=zipcode,
                                                session_key="None",
                                                ssn=personalcode,
                                                checking_account_id=checkingaccount.id,
                                                savings_account_id=savingsaccount.id,
                                                credit_card_id=creditcard.id,
                                                user_id=newUser.id,
                                                certificate=certificate)
                            individualcustomer.save()
                            if DEBUG: print("Create and save ind. account type\n")
                            new_account = individualcustomer
                            logger.info("Created individual customer '%s' account"%(username))
                        else:
                            #(request.POST['user_type'] == MERCHANT_ORGANIZATION):
                            if DEBUG: print("Merchant account type\n")
                            merchantcustomer = MerchantOrganization.objects.create(
                                                first_name=firstname,
                                                last_name=lastname,
                                                email=email,
                                                street_address=address,
                                                city=city,
                                                state=state,
                                                zipcode=zipcode,
                                                session_key="None",
                                                business_code=personalcode,
                                                checking_account_id=checkingaccount.id,
                                                savings_account_id=savingsaccount.id,
                                                credit_card_id=creditcard.id,
                                                user_id=newUser.id,
                                                certificate=certificate)
                            merchantcustomer.save()
                            if DEBUG: print("Create and save merch. account type\n")
                            new_account = merchantcustomer
                            logger.info("Created merchant '%s' account"%(username))

                        newUser.set_password(newPassword)
                        newUser.email = ""
                        newUser.first_name = ""
                        newUser.save()

                        if DEBUG: print("The user account has been created and added to the system\n")
                        check = send_mail(
                        'Group 3 SBS New Account Created',
                        CREATED_ACCOUNT_MESSAGE%(new_account.user.username,new_routing),
                        'group3sbs@gmail.com',
                        [new_account.email],
                        fail_silently=False,
                        )
                        if DEBUG: print("Check is %d\n"%(check))
                        while(check == 0):
                            check = send_mail(
                            'Group 3 SBS New Account',
                            CREATED_ACCOUNT_MESSAGE%(new_account.user.username,new_routing),
                            'group3sbs@gmail.com',
                            [new_account.email],
                            fail_silently=False,
                            )
                            if DEBUG: print("Check is %d\n"%(check))
                        if DEBUG: print("New account created email sent\n")
                        return render(request, 'create/confirmAccount.html', {'error_message': "New account created! Email notification sent.","STATES" : STATES})
                    else:
                        logger.info("User '%s' new password/confirm password mismatch"%(username))
                        return render(request, 'create/confirmAccount.html', {'error_message': "New password and confirm password mismatch.","STATES" : STATES})
                else:
                    #   else
                    #       return error that new account username/email mismatch
                    logger.info("User '%s' username/email mismatch"%(username))
                    return render(request, 'create/confirmAccount.html', {'error_message': "Username and email account mismatch.","STATES" : STATES})

            else:
                if DEBUG: print("No user account present, need to apply for new account first\n")
                logger.info("User '%s' username not found, need to create account"%(username))
                return render(request, 'create/create.html', {'error_message': "Application not found, please re-apply for an account.","STATES" : STATES})

    except Exception as e:
        if DEBUG: print("Threw an exception, did not complete try-block")
        return render(request, 'create/confirmAccount.html', {"STATES" : STATES})
