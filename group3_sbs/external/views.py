import logging
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction
from global_templates.common_functions import create_debit_or_credit_transaction, credit_or_debit_validate, create_transaction_external_user_profile_edit_request, get_any_user_profile, has_checking_account, has_credit_card, has_no_account, has_permission_to_edit_profile, has_savings_account, is_administrator, is_external_user, is_individual_customer, is_merchant_organization, is_regular_employee, is_system_manager, payment_validate, payment_on_behalf_validate, transfer_validate, validate_amount, validate_profile_change
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, STATES, TRANSACTION_TYPE_CREDIT, TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_PAYMENT, TRANSACTION_TYPE_PAYMENT_ON_BEHALF, TRANSACTION_TYPE_TRANSFER
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction, MerchantPaymentRequest, IndividualCustomer
from global_templates.common_functions import create_debit_or_credit_transaction, credit_or_debit_validate, is_administrator, is_external_user, is_individual_customer, is_merchant_organization, is_regular_employee, is_system_manager, has_checking_account, has_credit_card, has_no_account, has_savings_account, payment_validate, payment_on_behalf_validate, transfer_validate, validate_amount
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, TRANSACTION_TYPE_CREDIT, TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_PAYMENT, TRANSACTION_TYPE_PAYMENT_ON_BEHALF, TRANSACTION_TYPE_TRANSFER


# Create your views here.

""" Render Functions for Web Pages """
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
        return HttpResponseRedirect(reverse('external:error'))

# External Error Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def error(request):
    return render(request, 'external/error.html')

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return render(request, 'external/profile_edit.html', {'profile': profile, 'STATES': STATES})
    else:
        if create_transaction_external_user_profile_edit_request(user):
            return render(request, 'external/profile.html', {'profile': profile, 'message': "Awaiting Internal Employee Approval for Account Edit"})
        else:
            return HttpResponseRedirect(reverse("external:error"))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

""" Validator Functions for Web Pages """
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
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

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
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

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
        return HttpResponseRedirect(reverse(error_redirect))
    if user.has_perm(permission_codename):
        if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
            user.user_permissions.remove(permission)
            user.save()
            return HttpResponseRedirect(reverse(success_redirect))
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

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
    return transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type,success_redirect=success_redirect, error_redirect=error_redirect)

# Redirect to Request Payment web page
@never_cache
@login_required
@user_passes_test(is_external_user)
def request_payment(request):
    user = request.user
    return render(request, 'external/requestPayment.html',
                  {'checking_account': user.merchantorganization.checking_account})

# Add requested payment to DB
@never_cache
@login_required
@user_passes_test(is_external_user)
def addPaymentRequestToDB(request):
    user = request.user
    flag = "null"
    payment_amount1 = int(str(request.POST['payment_amount']))
    accountType = str(request.POST['account_type'])
    clientAccountNum = int(str(request.POST['account_number']))
    clientRoutingNum = long(str(request.POST['route_number']))
    clientAccountRecord = None
    log = logging.getLogger('logging.FileHandler')
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
            paymentRequest = MerchantPaymentRequest.objects.create(merchantCheckingsAccountNum=merchantCheckingsAccountNum,
                                                               accountType=accountType,
                                                               clientAccountNum=clientAccountNum,
                                                               clientRoutingNum=clientAccountNum,
                                                               requestAmount=payment_amount1)
            paymentRequest.save()
            flag = "request saved successfully"
            log.info("Request from merchant "+ str(user.merchantorganization.checking_account_id)+" stored successfully")
            return render(request, 'external/requestPayment.html',
                      {'checking_account': user.merchantorganization.checking_account, 'flag': flag})
        else:
            flag="invalid customer account details"
            log.info("Request from merchant "+ str(user.merchantorganization.checking_account_id)+" Reject invalid details")
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
            paymentRequest = MerchantPaymentRequest.objects.create(
                merchantCheckingsAccountNum=merchantCheckingsAccountNum,
                accountType=accountType,
                clientAccountNum=clientAccountNum,
                clientRoutingNum=clientAccountNum,
                requestAmount=payment_amount1)
            paymentRequest.save()
            flag = "request saved successfully"
            log.error("Request from merchant " + str(user.merchantorganization.checking_account_id) + " Rejected for invalid data")
            return render(request, 'external/requestPayment.html',
                          {'checking_account': user.merchantorganization.checking_account, 'flag': flag})
        else:
            flag = "invalid customer account details"
            log.info("Request from merchant " + str(
                user.merchantorganization.checking_account_id) + " Reject invalid details")
            return render(request, 'external/requestPayment.html',
                          {'checking_account': user.merchantorganization.checking_account, 'flag': flag})


# Show payment Requests
@never_cache
@login_required
@user_passes_test(is_external_user)
def showPaymentRequests(request):
    user = request.user
    checkingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Checking").filter(clientAccountNum=user.individualcustomer.checking_account_id)
    savingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Saving").filter(clientAccountNum=user.individualcustomer.savings_account_id)
    return render(request, 'external/showPaymentRequests.html',{'checkingRequests':checkingRequests,'savingRequests':savingRequests})

# Update Approvals
@never_cache
@login_required
@user_passes_test(is_external_user)
def update_approvals(request):
    user = request.user
    #make transfer
    #add this to transactions of the user
    string_transaction_id = str(request.POST['id'])
    transaction_id = int(string_transaction_id)
    transaction = MerchantPaymentRequest.objects.all().filter(id=transaction_id)
    transaction.delete()
    checkingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Checking").filter(
        clientAccountNum=user.individualcustomer.checking_account_id)
    savingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Saving").filter(
        clientAccountNum=user.individualcustomer.savings_account_id)
    return render(request, 'external/showPaymentRequests.html',
                  {'checkingRequests': checkingRequests, 'savingRequests': savingRequests})

# Reject Approvals
@never_cache
@login_required
@user_passes_test(is_external_user)
def reject_approvals(request):
    user = request.user
    #add this to transactions of the merchant as failed ones
    string_transaction_id = str(request.POST['id'])
    transaction_id = int(string_transaction_id)
    transaction = MerchantPaymentRequest.objects.all().filter(id=transaction_id)
    transaction.delete()
    checkingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Checking").filter(
        clientAccountNum=user.individualcustomer.checking_account_id)
    savingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Saving").filter(
        clientAccountNum=user.individualcustomer.savings_account_id)
    return render(request, 'external/showPaymentRequests.html',
                  {'checkingRequests': checkingRequests, 'savingRequests': savingRequests})
