from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.db.models import Q
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from easy_pdf.rendering import render_to_pdf_response
from external.models import *
from internal.models import *
from global_templates.common_functions import *
from global_templates.constants import *
from M2Crypto import RSA, EVP
import M2Crypto, time, logging, datetime

logger = logging.getLogger('external')

# Create your views here.

""" Render Functions for Web Pages """

# View Bank Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def all_statements(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(participants=user, status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(participants=user, status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render(request, 'external/all_statements.html',
                  {'transactions': transactions, 'title': 'All Transactions'})

# PDF All Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def all_statements_pdf(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(participants=user, status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(participants=user,status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render_to_pdf_response(request, 'external/all_statements_pdf.html', context={'transactions': transactions, 'username': user.username, 'title': 'All Transactions'}, filename=None, encoding=u'utf-8')

# Charge Card or Pay Card Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def charge_limit(request):
    user = request.user
    profile = get_any_user_profile(username=user.username)
    if profile and has_credit_card(user):
        charge_limit = min(float(profile.credit_card.charge_limit),float(profile.credit_card.remaining_credit))
        pay_limit = float(CREDIT_CARD_MAX_BALANCE)- max(float(profile.credit_card.charge_limit),float(profile.credit_card.remaining_credit))
        return render(request, 'external/charge_limit.html', {'credit_card': profile.credit_card, 'charge_limit':charge_limit, 'pay_limit': pay_limit})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Checking Account Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def checking_account(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, 'is_merchant_organization' : False})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, 'is_merchant_organization' : True})
    else:
        logger.info("User %s tried to access checking account page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# View Checking/Savings Bank Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def checking_and_savings_statements(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render(request, 'external/all_statements.html',
                  {'transactions': transactions, 'title': 'Checking and Savings'})

# View Checking/Savings Bank Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def checking_and_savings_statements_pdf(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT), ~Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render_to_pdf_response(request, 'external/all_statements_pdf.html', context={'transactions': transactions, 'username': user.username, 'title': 'Checking and Savings'}, filename=None, encoding=u'utf-8')

# Credit Card Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card(request):
    user = request.user
    if is_individual_customer(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'credt_card': user.individualcustomer.credit_card})
    elif is_merchant_organization(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'credt_card': user.merchantorganization.credit_card})
    else:
        logger.info("User %s tried to access credit card page without a credit card " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# View Checking/Savings Bank Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card_statements(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT) | Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT) | Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render(request, 'external/all_statements.html',
                  {'transactions': transactions, 'title': 'Credit Card'})

# View Checking/Savings Bank Statements
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card_statements_pdf(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT) | Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(Q(participants=user), Q(status=TRANSACTION_STATUS_RESOLVED), Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_CREDIT) | Q(type_of_transaction=CREDIT_CARD_TRANSACTION_TYPE_DEBIT)).order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render_to_pdf_response(request, 'external/all_statements_pdf.html', context={'transactions': transactions, 'username': user.username, 'title': 'Credit Card'}, filename=None, encoding=u'utf-8')

# Credit Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        logger.info("User %s tried to access credit checking account page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Credit Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        logger.info("User %s tried to access credit savings account page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Render Page for Critical Challenge Response
@never_cache
@login_required
@user_passes_test(is_external_user)
def critical_challenge_response(request, account_type, type_of_transaction):
    user = request.user
    success_redirect = 'external/critical_challenge_response.html'
    error_redirect = 'external:error'
    try:
        profile = get_any_user_profile(username=user.username)
        if (profile.otp_timestamp + OTP_EXPIRATION_DATE) < int(time.time()):
            profile.otp_pass = otpGenerator(size=OTP_LENGTH)
            profile.otp_timestamp = int(time.time())
            profile.save()
    except:
        logger.info("User %s encountered an error with getting a OTP for critical challenge response" % (request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    try:
        message = 'Hi, ' + user.username + '!\nPlease decrypt the following string using your private key and submit the decrypted value to the site. It is padded with oeap.\n\n'
        message = message + 'Use a command like this to extract it. Assuming you have openssl installed and your private_key is called private_key.pem in the PEM format and all files are in the same directory:\n\n'
        message = message + "openssl rsautl -oaep -decrypt -in otp.bin -out output.txt -inkey private_key.pem -keyform PEM\necho `cat output.txt`"
        cert = profile.certificate
        cert = str(cert)
        certificate = M2Crypto.X509.load_cert_string(cert)
        public_key = certificate.get_pubkey()
        rsa_public_key = public_key.get_rsa()
        signed = rsa_public_key.public_encrypt(profile.otp_pass, M2Crypto.RSA.pkcs1_oaep_padding)
        mail = EmailMessage("CSE545 Group3 SBS Critical Challenge Response", message,'group3sbs@gmail.com',[profile.email])
        mail.attach('otp.bin', signed, 'application/x-binary')
        mail.send()
        logger.info("Encrypted OTP sent to user %s" % (request.user.username))
    except:
        logger.info("Failed to send encrypted OTP to user %s" % (request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    return render(request, success_redirect, {'account_type': account_type, 'type_of_transaction': type_of_transaction})

# Debit Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        amount_limit = min(float(user.individualcustomer.checking_account.active_balance),float(user.individualcustomer.checking_account.current_balance))
        return render(request, 'external/debit.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    elif is_merchant_organization(user) and has_checking_account(user):
        amount_limit = min(float(user.merchantorganization.checking_account.active_balance),float(user.merchantorganization.checking_account.current_balance))
        return render(request, 'external/debit.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access debit checking account page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Debit Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        amount_limit = min(float(user.individualcustomer.savings_account.active_balance),float(user.individualcustomer.savings_account.current_balance))
        return render(request, 'external/debit.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_savings_account(user):
        amount_limit = min(float(user.merchantorganization.savings_account.active_balance),float(user.merchantorganization.savings_account.current_balance))
        return render(request, 'external/debit.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access debit savings account page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# External Error Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def error(request):
    return render(request, 'external/error.html')

# External User Home Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def index(request):
    user = request.user
    if is_individual_customer(user) and not has_no_account(user):
        return render(request, 'external/index.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name, 'checkingaccount': user.individualcustomer.checking_account, 'savingsaccount': user.individualcustomer.savings_account, 'creditcard': user.individualcustomer.credit_card})
    elif is_merchant_organization(user) and not has_no_account(user):
        return render(request, 'external/index.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name, 'checkingaccount': user.merchantorganization.checking_account, 'savingsaccount': user.merchantorganization.savings_account, 'creditcard': user.merchantorganization.credit_card})
    else:
        logger.info("User %s tried to access homepage without any account" % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Payment Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_email_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        amount_limit = min(float(user.individualcustomer.checking_account.active_balance),float(user.individualcustomer.checking_account.current_balance))
        return render(request, 'external/payment_email.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_checking_account(user):
        amount_limit = min(float(user.merchantorganization.checking_account.active_balance),float(user.merchantorganization.checking_account.current_balance))
        return render(request, 'external/payment_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access email payment checking page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Payment Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        amount_limit = min(float(user.individualcustomer.checking_account.active_balance),float(user.individualcustomer.checking_account.current_balance))
        return render(request, 'external/payment.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_checking_account(user):
        amount_limit = min(float(user.merchantorganization.checking_account.active_balance),float(user.merchantorganization.checking_account.current_balance))
        return render(request, 'external/payment.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access payment checking page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Payment Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_email_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        amount_limit = min(float(user.individualcustomer.savings_account.active_balance),float(user.individualcustomer.savings_account.current_balance))
        return render(request, 'external/payment_email.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_savings_account(user):
        amount_limit = min(float(user.merchantorganization.savings_account.active_balance),float(user.merchantorganization.savings_account.current_balance))
        return render(request, 'external/payment_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access email payment savings page without a  savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Payment Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        amount_limit = min(float(user.individualcustomer.savings_account.active_balance),float(user.individualcustomer.savings_account.current_balance))
        return render(request, 'external/payment.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_savings_account(user):
        amount_limit = min(float(user.merchantorganization.savings_account.active_balance),float(user.merchantorganization.savings_account.current_balance))
        return render(request, 'external/payment.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access email savings page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

"""
# Payment on Behalf Checking Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_checking(request):
    user = request.user
    if is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/payment_on_behalf.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment on Behalf Checking Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_email_checking(request):
    user = request.user
    if is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/payment_on_behalf_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment on Behalf Savings Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_savings(request):
    user = request.user
    if is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/payment_on_behalf.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment on Behalf Savings Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_email_savings(request):
    user = request.user
    if is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/payment_on_behalf_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

"""

# User Profile View Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def profile(request):
    user = request.user
    profile = get_any_user_profile(username=user.username)
    return render(request, 'external/profile.html', {'profile': profile})

# User Profile Edit Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def profile_edit(request):
    user = request.user
    profile = get_any_user_profile(username=user.username)
    if has_permission_to_edit_profile(user):
        logger.info("User %s is editing their profile"%(request.user.username))
        return render(request, 'external/profile_edit.html', {'profile': profile, 'STATES': STATES})
    else:
        if create_transaction_external_user_profile_edit_request(user):
            logger.info("User %s is requesting access to edit their profile"%(request.user.username))
            return render(request, 'external/profile.html', {'profile': profile, 'message': "Awaiting Internal Employee Approval for Account Edit"})
        else:
            logger.info("User %s tried edit their profile. Transaction to request access for profile edit failed to be created." % (request.user.username))
            return HttpResponseRedirect(reverse("external:error"))

# Savings Account Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def savings_account(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, 'is_merchant_organization' : False})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, 'is_merchant_organization' : True})
    else:
        logger.info("User %s tried to access savings account page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Display Credit Card Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def show_credit_info(request):
    user = request.user
    #days=now.day
    #days_late=days-5
    #user.individualcustomer.credit_card.days_late=days_late
    #update CreditCard set days_late = days_late where id=user.id;
    if is_individual_customer(user) and has_credit_card(user):
        return render(request, 'external/show_credit_info.html', {'show_credit_info': user.individualcustomer.credit_card})
    elif is_merchant_organization(user) and has_credit_card(user):
        return render(request, 'external/show_credit_info.html', {'show_credit_info': user.merchantorganization.credit_card})
    else:
        logger.info("User %s tried to access credit card page without a credit card " % (request.user.username))
        return render(request, 'external/error.html')

# Transfer Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_email_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        amount_limit = min(float(user.individualcustomer.checking_account.active_balance),float(user.individualcustomer.checking_account.current_balance))
        return render(request, 'external/transfer_email.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_checking_account(user):
        amount_limit = min(float(user.merchantorganization.checking_account.active_balance),float(user.merchantorganization.checking_account.current_balance))
        return render(request, 'external/transfer_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access email transfer checking page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Transfer Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        amount_limit = min(float(user.individualcustomer.checking_account.active_balance),float(user.individualcustomer.checking_account.current_balance))
        return render(request, 'external/transfer.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'checking_account': user.individualcustomer.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_checking_account(user):
        amount_limit = min(float(user.merchantorganization.checking_account.active_balance),float(user.merchantorganization.checking_account.current_balance))
        return render(request, 'external/transfer.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'checking_account': user.merchantorganization.checking_account, "account_type": "Checking", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access transfer checking page without a checking account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Transfer Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_email_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        amount_limit = min(float(user.individualcustomer.savings_account.active_balance),float(user.individualcustomer.savings_account.current_balance))
        return render(request, 'external/transfer_email.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_savings_account(user):
        amount_limit = min(float(user.merchantorganization.savings_account.active_balance),float(user.merchantorganization.savings_account.current_balance))
        return render(request, 'external/transfer_email.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access email transfer savings page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

# Transfer Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        amount_limit = min(float(user.individualcustomer.savings_account.active_balance),float(user.individualcustomer.savings_account.current_balance))
        return render(request, 'external/transfer.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name,'savings_account': user.individualcustomer.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    elif  is_merchant_organization(user) and has_savings_account(user):
        amount_limit = min(float(user.merchantorganization.savings_account.active_balance),float(user.merchantorganization.savings_account.current_balance))
        return render(request, 'external/transfer.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name,'savings_account': user.merchantorganization.savings_account, "account_type": "Savings", "amount_limit": amount_limit})
    else:
        logger.info("User %s tried to access transfer savings account page without a savings account " % (request.user.username))
        return HttpResponseRedirect(reverse('external:error'))

""" Validator Functions for Web Pages """

# Add a certificate
@never_cache
@login_required
@user_passes_test(is_external_user)
def add_certificate(request):
    user = request.user
    certificate = request.POST['certificate']
    profile = get_any_user_profile(username=user.username)
    if not validate_certificate(certificate) or not validate_certificate(profile.certificate):
        profile.certificate = None
    else:
        profile.certificate = str(certificate)
    profile.save()
    logger.info("User %s added a certificate %s "%(request.user.username, str(certificate)))
    return HttpResponseRedirect(reverse('external:profile'))

# Add requested payment to DB
@never_cache
@login_required
@user_passes_test(is_external_user)
def addPaymentRequestToDB(request):
    user = request.user
    flag = "null"
    payment_amount1 = float(request.POST['amount'])
    accountType = str(request.POST['account_type'])
    type_of_transaction = TRANSACTION_TYPE_PAYMENT_ON_BEHALF
    email = request.POST.get('email_address')
    if email:
        account = get_external_user_account_email(email=email, account_type=accountType)
        clientAccountNum = int(account.id)
        clientRoutingNum = long(account.routing_number)
    else:
        clientAccountNum = int(str(request.POST['account_number']))
        clientRoutingNum = long(str(request.POST['route_number']))
    clientAccountRecord = None
    if is_pki_needed(request=request, account_type=accountType, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for payment on behalf "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': accountType, 'type_of_transaction': type_of_transaction}))
    if(accountType == 'Checking'):
        client_CA_rowset = CheckingAccount.objects.all().filter(id=clientAccountNum)
        rowset_length = len(client_CA_rowset)
        client_IC_object = IndividualCustomer.objects.all().filter(checking_account_id=clientAccountNum)
        condition1 = (len(client_IC_object) > 0)
        condition2 = (len(client_CA_rowset) > 0)
        condition3 = False
        if condition2:
            client_CA_object = client_CA_rowset[0]
            condition3 = (client_CA_object.routing_number == clientRoutingNum)
        if (condition1 and condition2 and condition3):
            merchantCheckingsAccountNum = user.merchantorganization.checking_account_id
            merchantCheckingsRoutingNum = user.merchantorganization.checking_account.routing_number
            paymentRequest = MerchantPaymentRequest.objects.create(merchantCheckingsAccountNum=merchantCheckingsAccountNum,
                                                                   merchantCheckingRouteNum=merchantCheckingsRoutingNum,
                                                               accountType=accountType,
                                                               clientAccountNum=clientAccountNum,
                                                               clientRoutingNum=clientAccountNum,
                                                               requestAmount=payment_amount1)
            paymentRequest.save()
            flag = "request saved successfully"
            logger.info("Request from merchant " + str(request.user.username) + " was stored successfully")
            return HttpResponseRedirect(reverse('external:checking_account'))
        else:
            flag="invalid customer account details"
            logger.info("Request from merchant " + str(request.user.username)+ " was rejected for invalid information")
            return render(request, 'external/requestPayment.html',
              {'checking_account': user.merchantorganization.checking_account, 'flag': flag})

    if(accountType == 'Savings'):
        client_SA_rowset = SavingsAccount.objects.all().filter(id=clientAccountNum)
        rowset_length = len(client_SA_rowset)
        client_IC_object = IndividualCustomer.objects.all().filter(savings_account_id=clientAccountNum)
        condition1 = (len(client_IC_object)>0)
        condition2 = (len(client_SA_rowset)>0)
        condition3 = False
        if condition2:
            client_SA_object = client_SA_rowset[0]
            condition3 = (client_SA_object.routing_number == clientRoutingNum)
        if (condition1 and condition2 and condition3 ):
            merchantCheckingsAccountNum = user.merchantorganization.checking_account_id
            merchantCheckingsRoutingNum = user.merchantorganization.checking_account.routing_number
            paymentRequest = MerchantPaymentRequest.objects.create(
                merchantCheckingsAccountNum=merchantCheckingsAccountNum,
                merchantCheckingRouteNum=merchantCheckingsRoutingNum,
                accountType=accountType,
                clientAccountNum=clientAccountNum,
                clientRoutingNum=clientAccountNum,
                requestAmount=payment_amount1)
            paymentRequest.save()
            flag = "request saved successfully"
            logger.info("Request from merchant " + str(request.user.username) + " was stored successfully")
            return HttpResponseRedirect(reverse('external:checking_account'))
        else:
            flag = "invalid customer account details"
            log.info("Request from merchant " + str(request.user.username) + " was reject invalid details")
            return render(request, 'external/requestPayment.html',
                          {'checking_account': user.merchantorganization.checking_account, 'flag': flag})

# Approve Access Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def approveAccessRequests(request):
    user = request.user
    error_redirect = 'external:error'
    success_redirect = 'external:get_Accessrequests'
    internal_id = request.POST['internal_user_id']
    page_to_view = request.POST['page_to_view']
    access_request = accessRequests.objects.filter(externalUserId=user.id, internalUserId=internal_id, pageToView=page_to_view).first()
    if not access_request or access_request.externalUserId != user.id:
        logger.info("User %s tried approve an access request for an internal user %s to view page %s but did not have correct authorization to do so" % (request.user.username, str(internal_id), str(page_to_view)))
        return HttpResponseRedirect(reverse(error_redirect))
    internal_user = User.objects.filter(id=internal_id).first()
    if not internal_user:
        logger.info("User %s to to approve an access request, but user id %s does not belong to an internal user" % (request.user.username, str(internal_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    transaction = get_internal_access_transaction(user=internal_user, page_to_view=page_to_view)
    if commit_transaction(transaction=transaction, user=internal_user):
        access_request.delete()
        logger.info("User %s granted access to view page %s for internal user %s" % (request.user.username, page_to_view, internal_user.username))
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        logger.info("User %s tried to allow internal user %s to access page %s, but the transaction failed to be committed" % (request.user.username, internal_user.username, page_to_view))
        return HttpResponseRedirect(reverse(error_redirect))

# Validate Credit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card_credit_charge_limit_validate(request):
    user = request.user
    type_of_transaction = CREDIT_CARD_TRANSACTION_TYPE_CREDIT
    error_redirect = 'external:error'
    success_redirect = 'external:show_credit_info'
    return credit_card_credit_or_debit_validate(request=request,type_of_transaction=type_of_transaction,success_redirect=success_redirect, error_redirect=error_redirect)

@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card_debit_charge_limit_validate(request):
    user = request.user
    type_of_transaction = CREDIT_CARD_TRANSACTION_TYPE_DEBIT
    error_redirect = 'external:error'
    success_redirect = 'external:show_credit_info'
    return credit_card_credit_or_debit_validate(request=request,type_of_transaction=type_of_transaction,success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Credit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card_pay_late_fee_validation(request):
    user = request.user
    type_of_transaction = CREDIT_CARD_TRANSACTION_TYPE_PAY_LATE_FEE
    error_redirect = 'external:error'
    success_redirect = 'external:show_credit_info'
    return credit_card_pay_late_fee_validate(request=request,type_of_transaction=type_of_transaction,success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Credit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_CREDIT
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external:error'
    success_redirect = 'external:checking_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for crediting checking account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Credit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_CREDIT
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external:error'
    success_redirect = 'external:savings_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for crediting savings account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

# Validate PKI OTP Critical Challenge Response
@never_cache
@login_required
@user_passes_test(is_external_user)
def critical_challenge_response_validate(request, account_type, type_of_transaction):
    user = request.user
    username = request.POST['username']
    email = request.POST['email']
    otp = request.POST['otp']
    success_redirect = 'external'
    error_redirect = 'external:error'
    reset_otp_redirect = 'external:critical_challenge_response'
    if validate_username(username=username) and validate_email(email=email) and username == user.username:
        profile = get_any_user_profile(email=email, username=username)
        if profile and (profile.otp_timestamp + OTP_EXPIRATION_DATE) >= int(time.time()):
            if profile.otp_pass == otp :
                profile.otp_timestamp = time.time() - OTP_EXPIRATION_DATE
                profile.save()
                if add_external_user_make_critical_transaction(user=user, account_type=account_type, type_of_transaction=type_of_transaction):
                    success_redirect = critical_challenge_response_redirect_page(account_type=account_type, type_of_transaction=type_of_transaction)
                    logger.info("User %s completed pki challenge response and is going to %s"%(request.user.username, str(success_redirect)))
                    return HttpResponseRedirect(reverse(success_redirect))
                else:
                    logger.info("User %s failed to be granted permission after successfully completed pki challenge response "%(request.user.username))
                    return HttpResponseRedirect(reverse(error_redirect))
            else:
                logger.info("User %s is provided an incorrect opt of %s for the pki challenge response "%(request.user.username, str(otp)))
                return HttpResponseRedirect(reverse(reset_otp_redirect, kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
        else:
            logger.info("User %s entered otp of %s after it expired "%(request.user.username, str(otp)))
            return HttpResponseRedirect(reverse(reset_otp_redirect, kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        logger.info("User %s is attempting to perform a critical transaction using invalid username of %s and email of %s"%(request.user.username, str(username), str(email)))
        return HttpResponseRedirect(reverse(reset_otp_redirect, kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))

# Validate Debit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_DEBIT
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external:error'
    success_redirect = 'external:checking_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for debiting checking account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Debit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_DEBIT
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external:error'
    success_redirect = 'external:savings_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for debiting savings account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

#Get access Requests from data base and display them on web page
@never_cache
@login_required
@user_passes_test(is_external_user)
def getAccessRequests(request):
    user = request.user
    requests = accessRequests.objects.all().filter(externalUserId=user.id)
    return render(request, 'external/ViewPermissionRequsts.html',{'requests':requests})

# Validate Payment Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_PAYMENT
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external:error'
    success_redirect = 'external:checking_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for making a payment from their checking account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return payment_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Payment Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_PAYMENT
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external:error'
    success_redirect = 'external:savings_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for making a payment from their savings account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return payment_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Payment Checking Transaction
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_PAYMENT_ON_BEHALF
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external:error'
    success_redirect = 'external:checking_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for making a payment on belalf from their checking account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return payment_on_behalf_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Payment Savings Transaction
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_PAYMENT_ON_BEHALF
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external:error'
    success_redirect = 'external:savings_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for making a payment on behalf from their savings account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return payment_on_behalf_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Profile Edit Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def profile_edit_validate(request):
    user = request.user
    success_redirect = 'external:profile'
    error_redirect = 'external:profile_edit'
    profile = get_any_user_profile(username=user.username)
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    street_address = request.POST['street_address']
    city = request.POST['city']
    state = request.POST['state']
    zipcode = request.POST['zipcode']
    try:
        permission_codename = 'can_external_user_edit_own_profile_' + str(user.id)
        permission = Permission.objects.get(codename=permission_codename)
        permission_codename = 'external.' + permission_codename
    except:
        logger.info("There was database permission error when user %s tried to edit their profile"%(request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    if user.has_perm(permission_codename):
        if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
            user.user_permissions.remove(permission)
            user.save()
            logger.info("User %s successfully edited their account"%(request.user.username))
            return HttpResponseRedirect(reverse(success_redirect))
        else:
            logger.info("User %s provided incorrect changes when editing their account"%(request.user.username))
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        logger.info("User %s does not have permission to edit their profile "%(request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))

# Reject Access Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def rejectAccessRequests(request):
    user = request.user
    error_redirect = 'external:error'
    success_redirect = 'external:get_Accessrequests'
    internal_id = request.POST['internal_user_id']
    page_to_view = request.POST['page_to_view']
    access_request = accessRequests.objects.filter(externalUserId=user.id, internalUserId=internal_id, pageToView=page_to_view).first()
    if not access_request or access_request.externalUserId != user.id:
        logger.info("Failed to reject access request by internal user %s for %s's %s page "%(str(internal_id), request.user.username, page_to_view))
        return HttpResponseRedirect(reverse(error_redirect))
    access_request.delete()
    logger.info("User %s granted access to internal user %s to view %s "%(request.user.username, str(internal_id), str(page_to_view)))
    return HttpResponseRedirect(reverse(success_redirect))

# Reject Transaction Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def reject_approvals(request):
    user = request.user
    string_transaction_id = str(request.POST['id'])
    transaction_id = int(string_transaction_id)
    transaction = MerchantPaymentRequest.objects.all().filter(id=transaction_id)
    transaction.delete()
    logger.info("User %s rejected payment on behalf transction %s "%(request.user.username, str(transaction_id)))
    return HttpResponseRedirect(reverse('external:showPaymentRequests'))

# Redirect to Request Payment Email page
@never_cache
@login_required
@user_passes_test(is_external_user)
def request_payment_email(request):
    user = request.user
    return render(request, 'external/requestPaymentEmail.html',
                  {'checking_account': user.merchantorganization.checking_account})

# Redirect to Request Payment Email page
@never_cache
@login_required
@user_passes_test(is_external_user)
def request_payment(request):
    user = request.user
    return render(request, 'external/requestPayment.html',
                  {'checking_account': user.merchantorganization.checking_account})

# Validate Transfer Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_TRANSFER
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external:error'
    success_redirect = 'external:checking_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for transfer from their checking account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Transfer Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_TRANSFER
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external:error'
    success_redirect = 'external:savings_account'
    if is_pki_needed(request=request, account_type=account_type, type_of_transaction=type_of_transaction):
        logger.info("User %s is attempting to perform a critical transaction using pki for transfer from their savings account "%(request.user.username))
        return HttpResponseRedirect(reverse("external:critical_challenge_response", kwargs={'account_type': account_type, 'type_of_transaction': type_of_transaction}))
    else:
        return transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

# Show payment Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def showPaymentRequests(request):
    user = request.user
    checkingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Checking").filter(clientAccountNum=user.individualcustomer.checking_account_id)
    savingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Savings").filter(clientAccountNum=user.individualcustomer.savings_account_id)
    return render(request, 'external/showPaymentRequests.html',{'checkingRequests':checkingRequests,'savingRequests':savingRequests})

# Approve Transaction Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def update_approvals(request):
    user = request.user
    error_redirect = 'external:error'
    success_redirect = 'external:showPaymentRequests'
    string_transaction_id = str(request.POST['id'])
    transaction_id = int(string_transaction_id)
    transaction = MerchantPaymentRequest.objects.all().filter(id=transaction_id).first()
    if not payment_merchant_request_validate(request=request, merchant_request=transaction):
        logger.info("Payment on behalf transaction %s for user %s was not valid"%(str(transaction_id), request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    transaction.delete()
    logger.info("User %s approved payment on behalf transction %s "%(request.user.username, str(transaction_id)))
    return HttpResponseRedirect(reverse(success_redirect))
