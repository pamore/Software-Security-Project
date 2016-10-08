from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction
from global_templates.common_functions import create_debit_or_credit_transaction, credit_or_debit_validate, is_administrator, is_external_user, is_individual_customer, is_merchant_organization, is_regular_employee, is_system_manager, has_checking_account, has_credit_card, has_no_account, has_savings_account, validate_amount
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_CREDIT
# from global_templates.transaction_descriptions import debit_description, credit_description, transfer_description, payment_description

# Create your views here.

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
        return render(request, 'external/error.html')

# Checking Account Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def checking_account(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'checking_account': user.individualcustomer.checking_account})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'checking_account': user.merchantorganization.checking_account})
    else:
        return render(request, 'external/error.html')

# Savings Account Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def savings_account(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.individualcustomer.savings_account})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.merchantorganization.savings_account})
    else:
        return render(request, 'external/error.html')

# Credit Card Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_card(request):
    user = request.user
    if is_individual_customer(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'credt_card': user.individualcustomer.credit_card})
    elif is_merchant_organization(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'credt_card': user.merchantorganization.credit_card})
    else:
        return render(request, 'external/error.html')

# Credit Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Debit Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/debit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/debit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Credit Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Debit Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/debit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif  is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/debit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Validate Credit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_CREDIT
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external/error.html'
    success_redirect = 'external/credit.html'
    if is_individual_customer(user) and has_checking_account(user):
        success_payload = {'checking_account': user.individualcustomer.checking_account, 'account_type': account_type}
    elif is_merchant_organization(user) and has_checking_account(user):
        success_payload = {'checking_account': user.merchantorganization.checking_account, 'account_type': account_type}
    else:
        return render(request, error_redirect)
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_payload=success_payload, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Debit Checking Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_checking_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_DEBIT
    account_type = ACCOUNT_TYPE_CHECKING
    error_redirect = 'external/error.html'
    success_redirect = 'external/debit.html'
    if is_individual_customer(user) and has_checking_account(user):
        success_payload = {'checking_account': user.individualcustomer.checking_account, 'account_type': account_type}
    elif is_merchant_organization(user) and has_checking_account(user):
        success_payload = {'checking_account': user.merchantorganization.checking_account, 'account_type': account_type}
    else:
        return render(request, error_redirect)
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_payload=success_payload, success_redirect=success_redirect, error_redirect=error_redirect)


# Validate Credit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def credit_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_CREDIT
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external/error.html'
    success_redirect = 'external/credit.html'
    if is_individual_customer(user) and has_savings_account(user):
        success_payload = {'savings_account': user.individualcustomer.savings_account, 'account_type': account_type}
    elif is_merchant_organization(user) and has_savings_account(user):
        success_payload = {'savings_account': user.merchantorganization.savings_account, 'account_type': account_type}
    else:
        return render(request, error_redirect)
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_payload=success_payload, success_redirect=success_redirect, error_redirect=error_redirect)


# Validate Debit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def debit_savings_validate(request):
    user = request.user
    type_of_transaction = TRANSACTION_TYPE_DEBIT
    account_type = ACCOUNT_TYPE_SAVINGS
    error_redirect = 'external/error.html'
    success_redirect = 'external/debit.html'
    if is_individual_customer(user) and has_savings_account(user):
        success_payload = {'savings_account': user.individualcustomer.savings_account, 'account_type': account_type}
    elif is_merchant_organization(user) and has_savings_account(user):
        success_payload = {'savings_account': user.merchantorganization.savings_account, 'account_type': account_type}
    else:
        return render(request, error_redirect)
    return credit_or_debit_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_payload=success_payload, success_redirect=success_redirect, error_redirect=error_redirect)

# Validate Debit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def checking_statement(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(participants= user,account_type="Checking").order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(participants=user, account_type="Checking").order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render(request, 'external/checking_statement.html',
                  {'transactions': transactions})

# Validate Debit Savings Transaction
@never_cache
@login_required
@user_passes_test(is_external_user)
def savings_statement(request):
    user = request.user
    noncritical_transactions = ExternalNoncriticalTransaction.objects.filter(participant_id = user.id, account_type="Savings").order_by('time_created')
    critical_transactions = ExternalCriticalTransaction.objects.filter(participant_id=user.id, account_type="Savings").order_by('time_created')
    # Get all noncritical transactions for user
    # Get all critical
    transactions = []
    for transaction in noncritical_transactions:
        transactions.append(transaction)
    for transaction in critical_transactions:
        transactions.append(transaction)
    return render(request, 'external/savings_statement.html',
                  {'transactions': transactions})