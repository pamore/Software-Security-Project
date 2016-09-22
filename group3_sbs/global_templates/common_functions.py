from django.utils import timezone
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

def can_view_noncritical_transaction(user):
    if is_regular_employee(user) or is_system_manager(user):
        return True
    else:
        return False

def commit_transaction(transaction, user):
    type_of_transaction = transaction.type_of_transaction
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        return commit_transaction_credit_or_debit(transaction=transaction, user=user)
    # To do: Add transfer and payment functionality
    else:
        return False

def commit_transaction_credit_or_debit(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        account = data['account']
        if type_of_transaction == TRANSACTION_TYPE_CREDIT:
            new_amount = float(account.current_balance) - amount
            if validate_amount(new_amount):
                account.current_balance = new_amount
        elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
            new_amount = float(account.current_balance) + amount
            if validate_amount(new_amount):
                account.current_balance = new_amount
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        return True
    except:
        return False

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
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
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

def deny_transaction(transaction, user):
    try:
        save_transaction(transaction=transaction, user=user)
        return True
    except:
        return False

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

def parse_transaction_description(transaction_description, type_of_transaction):
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        return parse_transaction_description_credit_or_debit(transaction_description=transaction_description)
    # To do: add transfer and payment
    else:
        return {}

def parse_transaction_description_credit_or_debit(transaction_description):
    try:
        contents = transaction_description.split(',')
        transaction_type = contents[0].split(': ')[1]
        user_type = contents[1].split(': ')[1]
        user_id = contents[2].split(': ')[1]
        account_type = contents[3].split(': ')[1]
        account_id = contents[4].split(': ')[1]
        routing_id = contents[5].split(': ')[1]
        amount = contents[6].split(': ')[1]
        external_user = User.objects.get(id=int(user_id))
        if account_type == ACCOUNT_TYPE_CHECKING:
            account = CheckingAccount.objects.get(id=account_id)
        elif account_type == ACCOUNT_TYPE_SAVINGS:
            account = SavingsAccount.objects.get(id=account_id)
        else:
            raise Exception
        return {
            'transaction_type' : transaction_type,
            'user_type' : user_type,
            'external_user' : external_user,
            'account_type' : account_type,
            'account' : account,
            'account_id' : account_id,
            'routing_id' : routing_id,
            'amount' : amount,
        }
    except:
        return {}

def save_transaction(transaction, user):
    transaction.participants.add(user)
    transaction.resolver = user
    transaction.status = TRANSACTION_STATUS_RESOLVED
    transaction.time_resolved = timezone.now()
    transaction.save()

def validate_amount(amount):
    if amount > MAX_BALANCE or amount < MIN_BALANCE:
        return False
    else:
        return True
