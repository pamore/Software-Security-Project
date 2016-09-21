from datetime import datetime
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from global_templates.transaction_descriptions import debit_description, credit_description, transfer_description, payment_description
from global_templates.constants import *
from external.models import SavingsAccount, CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction

def create_debit_or_credit_transaction(user, user_type, account_type, type_of_transaction, amount):
    if is_individual_customer(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount)
    elif is_individual_customer(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount)
    elif is_merchant_organization(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string  = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount)
    elif is_merchant_organization(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string  = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount)
    elif is_individual_customer(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount)
    elif is_individual_customer(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount)
    elif is_merchant_organization(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string  = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount)
    elif is_merchant_organization(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string  = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount)
    else:
        return False
    if amount > NONCRITICAL_TRANSACTION_LIMIT:
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=datetime.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=datetime.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
    transaction.participants.add(user)
    transaction.save()
    return True

def credit_or_debit_validate(request, type_of_transaction, account_type, success_payload, success_redirect, error_redirect):
    user = request.user
    if type_of_transaction == TRANSACTION_TYPE_CREDIT:
        amount = float(request.POST['credit_amount'])
    if type_of_transaction == TRANSACTION_TYPE_DEBIT:
        amount = float(request.POST['debit_amount'])
    if not validate_amount(amount):
        return render(request, error_redirect)
    if is_individual_customer(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(user.individualcustomer.checking_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(user.merchantorganization.checking_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(user.individualcustomer.savings_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(user.merchantorganization.savings_account.active_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(user.individualcustomer.checking_account.active_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(user.merchantorganization.checking_account.active_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(user.individualcustomer.savings_account.active_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(user.merchantorganization.savings_account.active_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount)
        return render(request, success_redirect, success_payload)
    else:
        return render(request, error_redirect)

def is_external_user(user):
    if (hasattr(user, INDIVIDUAL_CUSTOMER_ATTRIBUTE) or hasattr(user, MERCHANT_ORGANIZATION_ATTRIBUTE)) and not (is_internal_user(user)):
        return True
    else:
        return False

def is_internal_user(user):
    if (hasattr(user, REGULAR_EMPLOYEE_ATTRIBUTE) or hasattr(user, SYSTEM_MANAGER_ATTRIBUTE) or hasattr(user, ADMINISTRATOR_ATTRIBUTE)) and not (is_external_user(user)):
        return True
    else:
        return False

def is_administrator(user):
    if is_internal_user(user) and hasattr(user, ADMINISTRATOR_ATTRIBUTE):
        return True
    else:
        return False

def is_individual_customer(user):
    if is_external_user(user) and hasattr(user, INDIVIDUAL_CUSTOMER_ATTRIBUTE):
        return True
    else:
        return False

def is_merchant_organization(user):
    if is_external_user(user) and hasattr(user, MERCHANT_ORGANIZATION_ATTRIBUTE):
        return True
    else:
        return False

def is_regular_employee(user):
    if is_internal_user(user) and hasattr(user, REGULAR_EMPLOYEE_ATTRIBUTE):
        return True
    else:
        return False

def is_system_manager(user):
    if is_internal_user(user) and hasattr(user, SYSTEM_MANAGER_ATTRIBUTE):
        return True
    else:
        return False

def has_checking_account(user):
    if is_external_user(user) and is_individual_customer(user) and hasattr(user.individualcustomer, CHECKING_ACCOUNT_ATTRIBUTE):
        return True
    elif is_external_user(user) and is_merchant_organization(user) and hasattr(user.merchantorganization, CHECKING_ACCOUNT_ATTRIBUTE):
        return True
    else:
        return False

def has_credit_card(user):
    if is_external_user(user) and is_individual_customer(user) and hasattr(user.individualcustomer, CREDIT_CARD_ATTRIBUTE):
        return True
    elif is_external_user(user) and is_merchant_organization(user) and hasattr(user.merchantorganization, CREDIT_CARD_ATTRIBUTE):
        return True
    else:
        return False

def has_no_account(user):
    if not has_credit_card(user) and not has_checking_account(user) and not has_savings_account(user):
        True
    else:
        return False

def has_savings_account(user):
    if is_external_user(user) and is_individual_customer(user) and hasattr(user.individualcustomer, SAVINGS_ACCOUNT_ATTRIBUTE):
        return True
    elif is_external_user(user) and is_merchant_organization(user) and hasattr(user.merchantorganization, SAVINGS_ACCOUNT_ATTRIBUTE):
        return True
    else:
        return False

def validate_amount(amount):
    if amount > MAX_BALANCE or amount < MIN_BALANCE:
        return False
    else:
        return True
