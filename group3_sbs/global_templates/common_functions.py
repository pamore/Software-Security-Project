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
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        return commit_transaction_payment(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        return commit_transaction_transfer(transaction=transaction, user=user)
    else:
        return False

def commit_transaction_credit_or_debit(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        account = data['account']
        if type_of_transaction == TRANSACTION_TYPE_CREDIT:
            new_amount = float(account.current_balance) + amount
            if validate_amount(new_amount) and validate_amount(amount):
                account.current_balance = new_amount
            else:
                return False
        elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
            new_amount = float(account.current_balance) - amount
            if validate_amount(new_amount) and validate_amount(amount):
                account.current_balance = new_amount
            else:
                return False
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        account.save()
        return True
    except:
        return False

def commit_transaction_payment(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        sender = data['sender']
        receiver = data['receiver']
        sender_account = data['sender_account']
        receiver_account = data['receiver_account']
        sender_new_balance = float(sender_account.current_balance) - amount
        receiver_new_balance = float(receiver_account.current_balance) + amount
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
            if validate_amount(amount) and validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
                sender_account.current_balance = sender_new_balance
                receiver_account.current_balance = receiver_new_balance
            else:
                return False
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        sender_account.save()
        receiver_account.save()
        return True
    except:
        return False

def commit_transaction_transfer(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        sender = data['sender']
        receiver = data['receiver']
        sender_account = data['sender_account']
        receiver_account = data['receiver_account']
        sender_new_balance = float(sender_account.current_balance) - amount
        receiver_new_balance = float(receiver_account.current_balance) + amount
        if type_of_transaction == TRANSACTION_TYPE_TRANSFER:
            if validate_amount(amount) and validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
                sender_account.current_balance = sender_new_balance
                receiver_account.current_balance = receiver_new_balance
            else:
                return False
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        sender_account.save()
        receiver_account.save()
        return True
    except:
        return False

def create_debit_or_credit_transaction(user, user_type, account_type, type_of_transaction, amount, starting_balance, ending_balance):
    if is_individual_customer(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_individual_customer(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_merchant_organization(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string  = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_merchant_organization(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        description_string  = credit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_individual_customer(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.checking_account.id,routingID=user.individualcustomer.checking_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_individual_customer(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.individualcustomer.savings_account.id,routingID=user.individualcustomer.savings_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_merchant_organization(user) and has_checking_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string  = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.checking_account.id,routingID=user.merchantorganization.checking_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    elif is_merchant_organization(user) and has_savings_account(user) and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        description_string  = debit_description(userType=user_type,userID=user.id,accountType=account_type,accountID=user.merchantorganization.savings_account.id,routingID=user.merchantorganization.savings_account.routing_number,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
    else:
        return False
    if amount > NONCRITICAL_TRANSACTION_LIMIT:
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
    transaction.participants.add(user)
    transaction.save()
    return True

def create_payment_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    type_of_transaction = TRANSACTION_TYPE_PAYMENT
    description_string = payment_description(senderType=senderType, senderID=senderID, senderAccountType=senderAccountType, senderAccountID=senderAccountID, senderRoutingID=senderRoutingID, receiverType=receiverType, receiverID=receiverID, receiverAccountType=receiverAccountType, receiverAccountID=receiverAccountID, receiverRoutingID=receiverRoutingID, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_ending_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_ending_balance)
    if amount > NONCRITICAL_TRANSACTION_LIMIT:
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    transaction.participants.add(sender)
    transaction.participants.add(receiver)
    transaction.save()
    return True

def create_payment_on_behalf_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    type_of_transaction = TRANSACTION_TYPE_PAYMENT_ON_BEHALF
    description_string = payment_description(senderType=senderType, senderID=senderID, senderAccountType=senderAccountType, senderAccountID=senderAccountID, senderRoutingID=senderRoutingID, receiverType=receiverType, receiverID=receiverID, receiverAccountType=receiverAccountType, receiverAccountID=receiverAccountID, receiverRoutingID=receiverRoutingID, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_ending_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_ending_balance)
    if amount > NONCRITICAL_TRANSACTION_LIMIT:
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    transaction.participants.add(sender)
    transaction.participants.add(receiver)
    transaction.save()
    return True

def create_transfer_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    type_of_transaction = TRANSACTION_TYPE_TRANSFER
    description_string = transfer_description(senderType=senderType, senderID=senderID, senderAccountType=senderAccountType, senderAccountID=senderAccountID, senderRoutingID=senderRoutingID, receiverType=receiverType, receiverID=receiverID, receiverAccountType=receiverAccountType, receiverAccountID=receiverAccountID, receiverRoutingID=receiverRoutingID, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_ending_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_ending_balance)
    if amount > NONCRITICAL_TRANSACTION_LIMIT:
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    else:
        transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=sender.id)
    transaction.participants.add(sender)
    transaction.participants.add(receiver)
    transaction.save()
    return True

def credit_or_debit_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    user = request.user
    if type_of_transaction == TRANSACTION_TYPE_CREDIT:
        amount = float(request.POST['credit_amount'])
    if type_of_transaction == TRANSACTION_TYPE_DEBIT:
        amount = float(request.POST['debit_amount'])
    if not validate_amount(amount):
        return HttpResponseRedirect(reverse(error_redirect))
    if is_individual_customer(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        starting_balance = user.individualcustomer.checking_account.active_balance
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(starting_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        starting_balance = user.merchantorganization.checking_account.active_balance
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(starting_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        starting_balance = user.individualcustomer.savings_account.active_balance
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(starting_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_CREDIT:
        starting_balance = user.merchantorganization.savings_account.active_balance
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(starting_balance) + amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        starting_balance = user.individualcustomer.checking_account.active_balance
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(starting_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_CHECKING and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        starting_balance = user.merchantorganization.checking_account.active_balance
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(starting_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        starting_balance = user.individualcustomer.savings_account.active_balance
        user_type = INDIVIDUAL_CUSTOMER
        new_balance = float(starting_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_SAVINGS and type_of_transaction == TRANSACTION_TYPE_DEBIT:
        starting_balance = user.merchantorganization.savings_account.active_balance
        user_type = MERCHANT_ORGANIZATION
        new_balance = float(starting_balance) - amount
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()
            create_debit_or_credit_transaction(user=user, user_type=user_type, account_type=account_type, type_of_transaction=type_of_transaction, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

def deny_transaction(transaction, user):
    type_of_transaction = transaction.type_of_transaction
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        return deny_transaction_credit_or_debit(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT:
        return deny_transaction_payment(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        return deny_transaction_transfer(transaction=transaction, user=user)
    # To do: add payment functionality
    else:
        return False

def deny_transaction_credit_or_debit(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        account = data['account']
        if type_of_transaction == TRANSACTION_TYPE_CREDIT:
            new_amount = float(account.active_balance) - amount
            if validate_amount(new_amount):
                account.active_balance = new_amount
        elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
            new_amount = float(account.active_balance) + amount
            if validate_amount(new_amount):
                account.active_balance = new_amount
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        account.save()
        return True
    except:
        return False

def deny_transaction_payment(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        sender = data['sender']
        receiver = data['receiver']
        sender_account = data['sender_account']
        receiver_account = data['receiver_account']
        sender_new_balance = float(sender_account.active_balance) + amount
        receiver_new_balance = float(receiver_account.active_balance) - amount
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT:
            if validate_amount(amount) and validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
                sender_account.active_balance = sender_new_balance
                receiver_account.active_balance = receiver_new_balance
            else:
                return False
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        sender_account.save()
        receiver_account.save()
        return True
    except:
        return False

def deny_transaction_transfer(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        sender = data['sender']
        receiver = data['receiver']
        sender_account = data['sender_account']
        receiver_account = data['receiver_account']
        sender_new_balance = float(sender_account.active_balance) + amount
        receiver_new_balance = float(receiver_account.active_balance) - amount
        if type_of_transaction == TRANSACTION_TYPE_TRANSFER:
            if validate_amount(amount) and validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
                sender_account.active_balance = sender_new_balance
                receiver_account.active_balance = receiver_new_balance
            else:
                return False
        else:
            return False
        save_transaction(transaction=transaction, user=user)
        sender_account.save()
        receiver_account.save()
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
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT or TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        return parse_transaction_description_transfer(transaction_description=transaction_description)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        return parse_transaction_description_transfer(transaction_description=transaction_description)
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
        starting_balance = contents[7].split(': ')[1]
        ending_balance = contents[8].split(': ')[1]
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
            'starting_balance' : starting_balance,
            'ending_balance' : ending_balance,
        }
    except:
        return {}

def parse_transaction_description_transfer(transaction_description):
    try:
        contents = transaction_description.split(',')
        transaction_type = contents[0].split(': ')[1]
        sender_type = contents[1].split(': ')[1]
        sender_id = contents[2].split(': ')[1]
        sender_account_type = contents[3].split(': ')[1]
        sender_account_id = contents[4].split(': ')[1]
        sender_routing_id = contents[5].split(': ')[1]
        receiver_type = contents[6].split(': ')[1]
        receiver_id = contents[7].split(': ')[1]
        receiver_account_type = contents[8].split(': ')[1]
        receiver_account_id = contents[9].split(': ')[1]
        receiver_routing_id = contents[10].split(': ')[1]
        amount = contents[11].split(': ')[1]
        sender_starting_balance = contents[12].split(': ')[1]
        sender_ending_balance = contents[13].split(': ')[1]
        receiver_starting_balance = contents[14].split(': ')[1]
        receiver_ending_balance = contents[15].split(': ')[1]
        sender = User.objects.get(id=int(sender_id))
        receiver = User.objects.get(id=int(receiver_id))
        if sender_account_type == ACCOUNT_TYPE_CHECKING:
            sender_account = CheckingAccount.objects.get(id=int(sender_account_id))
        elif sender_account_type == ACCOUNT_TYPE_SAVINGS:
            sender_account = SavingsAccount.objects.get(id=int(sender_account_id))
        else:
            raise Exception
        if receiver_account_type == ACCOUNT_TYPE_CHECKING:
            receiver_account = CheckingAccount.objects.get(id=int(receiver_account_id))
        elif receiver_account_type == ACCOUNT_TYPE_SAVINGS:
            receiver_account = SavingsAccount.objects.get(id=int(receiver_account_id))
        else:
            raise Exception
        return {
            'transaction_type' : transaction_type,
            'sender_type' : sender_type,
            'sender' : sender,
            'sender_account_type' : sender_account_type,
            'sender_account' : sender_account,
            'sender_account_id' : sender_account_id,
            'sender_routing_id' : sender_routing_id,
            'receiver_type' : receiver_type,
            'receiver' : receiver,
            'receiver_account_type' : receiver_account_type,
            'receiver_account' : receiver_account,
            'receiver_account_id' : receiver_account_id,
            'receiver_routing_id' : receiver_routing_id,
            'amount' : amount,
            'sender_starting_balance' : sender_starting_balance,
            'sender_ending_balance' : sender_ending_balance,
            'receiver_starting_balance' : receiver_starting_balance,
            'receiver_ending_balance' : receiver_ending_balance,
        }
    except:
        return {}

def payment_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    return payment_or_transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

def payment_on_behalf_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    receiver = request.user
    receiver_account_type = account_type
    sender_account_type = request.POST['account_type']
    sender_account_ID = request.POST['account_number']
    sender_routing_ID = request.POST['route_number']
    if type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        amount = float(request.POST['payment_on_behalf_amount'])
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    try:
        if sender_account_type == ACCOUNT_TYPE_CHECKING:
            sender = User.objects.get(individualcustomer__checking_account__id=int(sender_account_ID ), individualcustomer__checking_account__routing_number=int(sender_routing_ID))
            sender_account = sender.individualcustomer.checking_account
        elif sender_account_type == ACCOUNT_TYPE_SAVINGS:
            sender = User.objects.get(individualcustomer__savings_account__id=int(sender_account_ID ), individualcustomer__savings_account__routing_number=int(sender_routing_ID))
            sender_account = sender.individualcustomer.savings_account
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    sender_user_type = INDIVIDUAL_CUSTOMER
    sender_starting_balance = sender_account.active_balance
    sender_new_balance = float(sender_starting_balance) - amount
    if not validate_amount(amount):
        return HttpResponseRedirect(reverse(error_redirect))
    if is_merchant_organization(receiver) and receiver_account_type == ACCOUNT_TYPE_CHECKING:
        receiver_account = receiver.merchantorganization.checking_account
    elif is_merchant_organization(receiver) and receiver_account_type == ACCOUNT_TYPE_SAVINGS:
        receiver_account = receiver.merchantorganization.savings_account
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    receiver_starting_balance = receiver_account.active_balance
    receiver_user_type = MERCHANT_ORGANIZATION
    receiver_new_balance = float(receiver_starting_balance) + amount
    if validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
        sender_account.active_balance = sender_new_balance
        receiver_account.active_balance = receiver_new_balance
        sender_account.save()
        receiver_account.save()
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
            create_payment_on_behalf_transaction(sender=sender, senderType=sender_user_type, senderID=sender.id, senderAccountType=sender_account_type, senderAccountID=sender_account.id, senderRoutingID=sender_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
        return HttpResponseRedirect(reverse(success_redirect))

def payment_or_transfer_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    user = request.user
    sender_account_type = account_type
    receiver_account_type = request.POST['account_type']
    receiver_account_ID = request.POST['account_number']
    receiver_routing_ID = request.POST['route_number']
    if type_of_transaction == TRANSACTION_TYPE_PAYMENT:
        amount = float(request.POST['payment_amount'])
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        amount = float(request.POST['transfer_amount'])
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if receiver_account_type == ACCOUNT_TYPE_CHECKING:
        try:
            receiver = User.objects.get(individualcustomer__checking_account__id=int(receiver_account_ID ), individualcustomer__checking_account__routing_number=int(receiver_routing_ID))
            receiver_user_type = INDIVIDUAL_CUSTOMER
            receiver_account = receiver.individualcustomer.checking_account
        except:
            receiver = User.objects.get(merchantorganization__checking_account__id=int(receiver_account_ID ), merchantorganization__checking_account__routing_number=int(receiver_routing_ID))
            receiver_user_type = MERCHANT_ORGANIZATION
            receiver_account = receiver.merchantorganization.checking_account
        receiver_starting_balance = receiver_account.active_balance
        receiver_new_balance = float(receiver_starting_balance) + amount
    elif receiver_account_type == ACCOUNT_TYPE_SAVINGS:
        try:
            receiver = User.objects.get(individualcustomer__savings_account__id=int(receiver_account_ID ), individualcustomer__savings_account__routing_number=int(receiver_routing_ID))
            receiver_user_type = INDIVIDUAL_CUSTOMER
            receiver_account = receiver.individualcustomer.savings_account
        except:
            receiver = User.objects.get(merchantorganization__savings_account__id=int(receiver_account_ID ), merchantorganization__savings_account__routing_number=int(receiver_routing_ID))
            receiver_user_type = MERCHANT_ORGANIZATION
            receiver_account = receiver.merchantorganization.savings_account
        receiver_starting_balance = receiver_account.active_balance
        receiver_new_balance = float(receiver_starting_balance) + amount
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if not validate_amount(amount):
        return HttpResponseRedirect(reverse(error_redirect))
    if is_individual_customer(user) and sender_account_type == ACCOUNT_TYPE_CHECKING:
        user_account = user.individualcustomer.checking_account
        sender_user_type = INDIVIDUAL_CUSTOMER
    elif is_individual_customer(user) and sender_account_type == ACCOUNT_TYPE_SAVINGS:
        user_account = user.individualcustomer.savings_account
        sender_user_type = INDIVIDUAL_CUSTOMER
    elif is_merchant_organization(user) and sender_account_type == ACCOUNT_TYPE_CHECKING:
        user_account = user.merchantorganization.checking_account
        sender_user_type = MERCHANT_ORGANIZATION
    elif is_merchant_organization(user) and sender_account_type == ACCOUNT_TYPE_SAVINGS:
        user_account = user.merchantorganization.savings_account
        sender_user_type = MERCHANT_ORGANIZATION
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    sender_starting_balance = user_account.active_balance
    sender_new_balance = float(sender_starting_balance) - amount
    if validate_amount(sender_new_balance) and validate_amount(receiver_new_balance):
        user_account.active_balance = sender_new_balance
        receiver_account.active_balance = receiver_new_balance
        user_account.save()
        receiver_account.save()
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT:
            create_payment_transaction(sender=user, senderType=sender_user_type, senderID=user.id, senderAccountType=sender_account_type, senderAccountID=user_account.id, senderRoutingID=user_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
        elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
            create_transfer_transaction(sender=user, senderType=sender_user_type, senderID=user.id, senderAccountType=sender_account_type, senderAccountID=user_account.id, senderRoutingID=user_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
    return HttpResponseRedirect(reverse(success_redirect))

def save_transaction(transaction, user):
    transaction.participants.add(user)
    transaction.resolver = user
    transaction.status = TRANSACTION_STATUS_RESOLVED
    transaction.time_resolved = timezone.now()
    transaction.save()

def transfer_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    return payment_or_transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

def validate_amount(amount):
    if amount > MAX_BALANCE or amount < MIN_BALANCE:
        return False
    else:
        return True
