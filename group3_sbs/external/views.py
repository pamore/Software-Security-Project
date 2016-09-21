from datetime import datetime
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from global_templates.transaction_descriptions import debit_description, credit_description, transfer_description, payment_description
from global_templates.constants import MAX_BALANCE, MIN_BALANCE, NONCRITICAL_TRANSACTION_LIMIT
from global_templates.common_functions import is_administrator, is_external_user, is_internal_user, is_individual_customer, is_merchant_organization, is_regular_employee, is_system_manager, has_checking_account, has_credit_card, has_no_account, has_savings_account, validate_amount
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction

# Create your views here.

# External User Home Page
@login_required
def index(request):
    user = request.user
    if is_individual_customer(user):
        if has_no_account(user):
            return render(request, 'external/error.html')
        else:
            return render(request, 'external/index.html', {'user_type': "Individual Customer", 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name, 'checkingaccount': user.individualcustomer.checking_account, 'savingsaccount': user.individualcustomer.savings_account, 'creditcard': user.individualcustomer.credit_card})
    elif is_merchant_organization(user):
        if has_no_account(user):
            return render(request, 'external/error.html')
        else:
            return render(request, 'external/index.html', {'user_type': "Merchant / Organization", 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name, 'checkingaccount': user.merchantorganization.checking_account, 'savingsaccount': user.merchantorganization.savings_account, 'creditcard': user.merchantorganization.credit_card})
    else:
        return render(request, 'external/error.html')

# Checking Account Page
@login_required
def checking_account(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'checking_account': user.individualcustomer.checking_account})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/checking_account.html', {'checking_account': user.merchantorganization.checking_account})
    else:
        return render(request, 'external/error.html')

# Savings Account Page
@login_required
def savings_account(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.individualcustomer.savings_account})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/savings_account.html', {'savings_account': user.merchantorganization.savings_account})
    else:
        return render(request, 'external/error.html')

# Credit Card Page
@login_required
def credit_card(request):
    user = request.user
    if is_individual_customer(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'credt_card': user.individualcustomer.credit_card})
    elif is_merchant_organization(user) and has_credit_card(user):
        return render(request, 'external/credit_card.html', {'credt_card': user.merchantorganization.credit_card})
    else:
        return render(request, 'external/error.html')

# Credit Checking Page
@login_required
def credit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/credit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Debit Checking Page
@login_required
def debit_checking(request):
    user = request.user
    if is_individual_customer(user) and has_checking_account(user):
        return render(request, 'external/debit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif is_merchant_organization(user) and has_checking_account(user):
        return render(request, 'external/debit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Credit Savings Page
@login_required
def credit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/credit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Debit Savings Page
@login_required
def debit_savings(request):
    user = request.user
    if is_individual_customer(user) and has_savings_account(user):
        return render(request, 'external/debit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif  is_merchant_organization(user) and has_savings_account(user):
        return render(request, 'external/debit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Validate Credit Checking Transaction
@login_required
def credit_checking_validate(request):
    user = request.user
    type_of_transaction = "credit"
    accountType = "Checking"
    amount = float(request.POST['credit_amount'])
    if not validate_amount(amount):
        return render(request, 'external/error.html')
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        userType = "Individual Customer"
        new_balance = float(user.individualcustomer.checking_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()

            # Create Transaction
            credit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        userType = "Merchant / Organization"
        new_balance = float(user.merchantorganization.checking_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()

            # Create Transaction
            credit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Validate Debit Checking Transaction
@login_required
def debit_checking_validate(request):
    user = request.user
    type_of_transaction = "debit"
    accountType = "Checking"
    amount = float(request.POST['debit_amount'])
    if not validate_amount(amount):
        return render(request, 'external/error.html')
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        userType = "Individual Customer"
        new_balance = float(user.individualcustomer.checking_account.active_balance) - amount
        if new_balance >= MIN_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()

            # Create Transaction
            debit_string = debit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        userType = "Merchant / Organization"
        new_balance = float(user.merchantorganization.checking_account.active_balance) - amount
        if new_balance >= MIN_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()

            # Create Transaction
            debit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Validate Credit Savings Transaction
@login_required
def credit_savings_validate(request):
    user = request.user
    type_of_transaction = "credit"
    accountType = "Savings"
    amount = float(request.POST['credit_amount'])
    if not validate_amount(amount):
        return render(request, 'external/error.html')
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        userType = "Individual Customer"
        new_balance = float(user.individualcustomer.savings_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()

            # Create Transaction
            credit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        userType = "Merchant / Organization"
        new_balance = float(user.merchantorganization.savings_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()

            # Create Transaction
            credit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=credit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Validate Debit Savings Transaction
@login_required
def debit_savings_validate(request):
    user = request.user
    type_of_transaction = "debit"
    accountType = "Savings"
    amount = float(request.POST['debit_amount'])
    if not validate_amount(amount):
        return render(request, 'external/error.html')
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        userType = "Individual Customer"
        new_balance = float(user.individualcustomer.savings_account.active_balance) - amount
        if new_balance >= MIN_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()

            # Create Transaction
            debit_string = debit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        userType = "Merchant / Organization"
        new_balance = float(user.merchantorganization.savings_account.active_balance) - amount
        if new_balance >= MIN_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()

            # Create Transaction
            debit_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount)
            if amount > NONCRITICAL_TRANSACTION_LIMIT:
                transaction = ExternalCriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            else:
                transaction = ExternalNoncriticalTransaction.objects.create(status="unresolved", time_created=datetime.now(), type_of_transaction=type_of_transaction, description=debit_string, initiator_id=user.id)
            transaction.participants.add(user)
            transaction.save()
            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')
