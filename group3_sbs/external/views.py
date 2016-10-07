from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction, MerchantPaymentRequest
from global_templates.common_functions import create_debit_or_credit_transaction, credit_or_debit_validate, is_administrator, is_external_user, is_individual_customer, is_merchant_organization, is_regular_employee, is_system_manager, has_checking_account, has_credit_card, has_no_account, has_savings_account, payment_validate, payment_on_behalf_validate, transfer_validate, validate_amount
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, TRANSACTION_TYPE_CREDIT, TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_PAYMENT, TRANSACTION_TYPE_PAYMENT_ON_BEHALF, TRANSACTION_TYPE_TRANSFER


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
        return render(request, 'external/checking_account.html', {'checking_account': user.individualcustomer.checking_account, 'is_merchant_organization' : False})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'checking_account': user.merchantorganization.checking_account, 'is_merchant_organization' : True})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Savings Account Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def savings_account(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.individualcustomer.savings_account, 'is_merchant_organization' : False})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.merchantorganization.savings_account, 'is_merchant_organization' : True})
    else:
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

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
        return HttpResponseRedirect(reverse('external:error'))

# Payment Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/payment.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif  is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/payment.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def payment_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/payment.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif  is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/payment.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment on Behalf Checking Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_checking(request):
    user = request.user
    if is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/payment_on_behalf.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Payment on Behalf Savings Page
@never_cache
@login_required
@user_passes_test(is_merchant_organization)
def payment_on_behalf_savings(request):
    user = request.user
    if is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/payment_on_behalf.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Transfer Checking Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/transfer.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif  is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/transfer.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

# Transfer Savings Page
@never_cache
@login_required
@user_passes_test(is_external_user)
def transfer_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/transfer.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif  is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/transfer.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return HttpResponseRedirect(reverse('external:error'))

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
    payment_amount = request.POST['payment_amount']
    accountType = request.POST['account_type']
    clientAccountNum = request.POST['account_number']
    clientRoutingNum = request.POST['route_number']
    merchantCheckingsAccountNum = user.merchantorganization.checking_account_id
    paymentRequest = MerchantPaymentRequest.objects.create(merchantCheckingsAccountNum = merchantCheckingsAccountNum,accountType = accountType, clientAccountNum=clientAccountNum, clientRoutingNum = clientAccountNum,requestAmount=payment_amount)
    paymentRequest.save()
    return render(request, 'external/requestPayment.html',
                  {'checking_account': user.merchantorganization.checking_account})


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

# Delete Approvals
@never_cache
@login_required
@user_passes_test(is_external_user)
def reject_approvals(request):
    user = request.user
    #add this to transactions of the merchant as failed ones
    transaction = MerchantPaymentRequest.objects.all().filter(request.POST['id'])
    transaction.delete()
    checkingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Checking").filter(
        clientAccountNum=user.individualcustomer.checking_account_id)
    savingRequests = MerchantPaymentRequest.objects.all().filter(accountType="Saving").filter(
        clientAccountNum=user.individualcustomer.savings_account_id)
    return render(request, 'external/showPaymentRequests.html',
                  {'checkingRequests': checkingRequests, 'savingRequests': savingRequests})