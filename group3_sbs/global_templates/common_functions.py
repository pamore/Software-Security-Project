from django.utils import timezone
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.mail import EmailMessage, send_mail
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.auth import authenticate, login, logout
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from external.models import CheckingAccount, CreditCard, ExternalNoncriticalTransaction, ExternalCriticalTransaction, IndividualCustomer, MerchantOrganization, SavingsAccount
from internal.models import Administrator, RegularEmployee, SystemManager, InternalNoncriticalTransaction, InternalCriticalTransaction
from global_templates.transaction_descriptions import debit_description, credit_description, transfer_description, payment_description
from global_templates.constants import *
from templated_email import send_templated_mail
import random
import re
import string

def add_edit_external_user_profile_permission(user):
    if is_external_user(user):
        try:
            if is_individual_customer(user):
                content_type = ContentType.objects.get_for_model(IndividualCustomer)
            else:
                content_type = ContentType.objects.get_for_model(MerchantOrganization)
            permission_codename = 'can_external_user_edit_own_profile_' + str(user.id)
            permission_name = "Can external user " + str(user.id) + " edit their profile"
            try:
                permission = Permission.objects.get(codename=permission_codename, name=permission_name, content_type=content_type)
            except:
                permission = Permission.objects.create(codename=permission_codename,name=permission_name, content_type=content_type)
            if user.has_perm(permission):
                return True
            user.user_permissions.add(permission)
            user.save()
            return True
        except:
            return False
    else:
        return False

def add_internal_edit_external_user_profile_permission(user, external_user):
    if is_regular_employee(user):
        try:
            content_type = ContentType.objects.get_for_model(RegularEmployee)
            permission_codename = 'can_internal_user_edit_external_user_profile_' + str(external_user.id)
            permission_name = "Can internal user" + str(user.id) + " edit external user " + str(external_user.id) + "'s profile"
            try:
                permission = Permission.objects.get(codename=permission_codename, name=permission_name, content_type=content_type)
            except:
                permission = Permission.objects.create(codename=permission_codename,name=permission_name, content_type=content_type)
            if user.has_perm(permission):
                return True
            user.user_permissions.add(permission)
            user.save()
            return True
        except:
            return False
    elif is_system_manager(user):
        return True
    else:
        return False

def add_view_external_user_permission(user, external_user, page_to_view):
    if is_regular_employee(user):
        try:
            content_type = ContentType.objects.get_for_model(RegularEmployee)
            permission_codename = 'can_view_external_user_' + page_to_view + '_' + str(external_user.id)
            permission_name = "Can view external user " + str(external_user.id) + "'s"+ page_to_view + " page"
            try:
                permission = Permission.objects.get(codename=permission_codename, name=permission_name, content_type=content_type)
            except:
                permission = Permission.objects.create(codename=permission_codename,name=permission_name, content_type=content_type)
            if user.has_perm(permission):
                return True
            user.user_permissions.add(permission)
            user.save()
            return True
        except:
            return False
    elif is_system_manager(user):
        return True
    else:
        return False

def can_edit_external_user_page(user, external_user_id, page_to_view):
    verify = False
    if is_regular_employee(user):
        try:
            permission_codename = 'can_internal_user_edit_external_user_profile_' + str(external_user_id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'internal.' + permission_codename
            if user.has_perm(permission_codename):
                external_user = User.objects.get(id=int(external_user_id))
                if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE:
                    verify = True
        except:
            pass
    elif is_system_manager(user):
        if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE:
            verify = True
    return verify

def can_resolve_internal_transaction(user):
    if is_administrator(user) or is_system_manager(user):
        return True
    else:
        return False

def can_resolve_noncritical_transaction(user, transaction_id):
    if is_regular_employee(user):
        try:
            permission_codename = 'can_resolve_external_noncritical_transaction_' + str(transaction_id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'internal.' + permission_codename
            if user.has_perm(permission_codename):
                user.user_permissions.remove(permission)
                user.save()
                return True
            else:
                return False
        except:
            return False
    elif is_system_manager(user):
        return True
    else:
        return False

def can_view_external_user_page(user, external_user_id, page_to_view):
    verify = False
    if is_regular_employee(user):
        try:
            permission_codename = 'can_view_external_user_' + page_to_view + '_' + str(external_user_id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'internal.' + permission_codename
            if user.has_perm(permission_codename):
                external_user = User.objects.get(id=int(external_user_id))
                if page_to_view == PAGE_TO_VIEW_PROFILE or (page_to_view == PAGE_TO_VIEW_SAVINGS_ACCOUNT and has_savings_account(external_user)) or (page_to_view == PAGE_TO_VIEW_CHECKING_ACCOUNT and has_checking_account(external_user)) or (page_to_view == PAGE_TO_VIEW_CREDIT_CARD and has_credit_card(external_user)):
                    verify = True
                    user.user_permissions.remove(permission)
                    user.save()
        except:
            pass
    elif is_system_manager(user) or is_administrator(user):
        external_user = User.objects.get(id=int(external_user_id))
        if page_to_view == PAGE_TO_VIEW_PROFILE or (page_to_view == PAGE_TO_VIEW_SAVINGS_ACCOUNT and has_savings_account(external_user)) or (page_to_view == PAGE_TO_VIEW_CHECKING_ACCOUNT and has_checking_account(external_user)) or (page_to_view == PAGE_TO_VIEW_CREDIT_CARD and has_credit_card(external_user)):
            verify = True
    return verify

def can_view_noncritical_transaction(user):
    if is_regular_employee(user) or is_system_manager(user):
        return True
    else:
        return False

def commit_transaction(transaction, user):
    type_of_transaction = transaction.type_of_transaction
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        result = commit_transaction_credit_or_debit(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        result = commit_transaction_payment(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        result = commit_transaction_transfer(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSACTION_ACCESS_REQUEST:
        result = commit_transaction_internal_noncritical(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST:
        result = commit_transaction_internal_transcaction_for_access(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_EXTERNAL_USER_PROFILE_EDIT_REQUEST:
        result = commit_transaction_external_user_profile_edit_request(transaction=transaction, user=user)
    else:
        result = False
    if result:
        pass # remove to test email
        """
        recipients = get_all_emails(transaction.participants.all())
        #send_notification_transaction(subject=TRANSACTION_SUBJECT_APPROVED, message=TRANSACTION_MESSAGE, transaction=transaction, status=TRANSACTION_STATUS_APPROVED, email_template=None, recipients=recipients)
        send_templated_mail(
            template_name='transaction_approval',
            from_email='group3sbs@gmail.com',
            recipient_list=recipients,
            context={
                'username':"user_name",
            },
            # Optional:
            # cc=['cc@example.com'],
            # bcc=['bcc@example.com'],
            # headers={'My-Custom-Header':'Custom Value'},
            # template_prefix="my_emails/",
            # template_suffix="email",
        )"""
    return result

def commit_transaction_credit_or_debit(transaction, user):
    try:
        type_of_transaction = transaction.type_of_transaction
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=type_of_transaction)
        amount = float(data['amount'])
        account = data['account']
        if type_of_transaction == TRANSACTION_TYPE_CREDIT:
            check = float(account.current_balance) + amount
            new_amount = float(account.current_balance) + amount
            if validate_amount(check) and validate_amount(amount):
                account.current_balance = new_amount
            else:
                return False
        elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
            check = float(account.current_balance) - amount
            new_amount = float(account.current_balance) - amount
            if validate_amount(check) and validate_amount(amount):
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

def commit_transaction_external_user_profile_edit_request(transaction, user):
    try:
        initiator = transaction.initiator
        if add_edit_external_user_profile_permission(user=initiator):
            save_transaction(transaction=transaction, user=user)
            return True
        else:
            return False
    except:
        return False

def commit_transaction_internal_noncritical(transaction, user):
    try:
        save_transaction(transaction=transaction, user=user)
        return True
    except:
        return False

def commit_transaction_internal_transcaction_for_access(transaction, user):
    try:
        data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=transaction.type_of_transaction)
        initiator = transaction.initiator
        external_user = data['external_user']
        page_to_view = data['page_to_view']
        if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE:
            if add_internal_edit_external_user_profile_permission(user=initiator, external_user=external_user):
                save_transaction(transaction=transaction, user=user)
                return True
            else:
                return False
        else:
            if add_view_external_user_permission(user=initiator, external_user=external_user, page_to_view=page_to_view):
                save_transaction(transaction=transaction, user=user)
                return True
            else:
                return False
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
        sender_check = float(sender_account.current_balance) - amount
        receiver_check =  float(receiver_account.current_balance) + amount
        sender_new_balance = float(sender_account.current_balance) - amount
        receiver_new_balance = float(receiver_account.current_balance) + amount
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
            if validate_amount(amount) and validate_amount(sender_check) and validate_amount(receiver_check):
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
        sender_check = float(sender_account.current_balance) - amount
        receiver_check =  float(receiver_account.current_balance) + amount
        sender_new_balance = float(sender_account.current_balance) - amount
        receiver_new_balance = float(receiver_account.current_balance) + amount
        if type_of_transaction == TRANSACTION_TYPE_TRANSFER:
            if validate_amount(amount) and validate_amount(sender_check) and validate_amount(receiver_check):
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

def create_debit_or_credit_transaction(user, type_of_transaction, userType, accountType, accountID, routingID, amount, starting_balance, ending_balance):
    try:
        if type_of_transaction == TRANSACTION_TYPE_CREDIT:
            description_string = credit_description(userType=userType,userID=user.id,accountType=accountType,accountID=accountID,routingID=routingID,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
        elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
            description_string  = debit_description(userType=userType,userID=user.id,accountType=accountType,accountID=accountID,routingID=routingID,amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)
        else:
            return False
        if amount > NONCRITICAL_TRANSACTION_LIMIT:
            transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
        else:
            transaction = ExternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
        transaction.participants.add(user)
        transaction.save()
        return True
    except:
        return False

def create_transaction_external_user_profile_edit_request(user):
    try:
        type_of_transaction = TRANSACTION_TYPE_EXTERNAL_USER_PROFILE_EDIT_REQUEST
        description_string = "User ID: " + str(user.id)
        description_string = description_string + ",Action: requests access to edit their profile"
        transaction = ExternalCriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
        transaction.save()
        return True
    except:
        return False

def create_internal_noncritical_transaction(user, external_transaction):
    try:
        type_of_transaction = TRANSACTION_TYPE_TRANSACTION_ACCESS_REQUEST
        description_string = "User: " + user.username
        description_string = description_string + ",Action: requests access to external non-critical transaction"
        description_string = description_string + ",Transaction ID: " +  str(external_transaction.id)
        transaction = InternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
        transaction.save()
        return True
    except:
        return False

def create_internal_transcaction_for_access(user, external_user, page_to_view):
    try:
        type_of_transaction = TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST
        description_string = "User: " + user.username
        description_string = description_string + ",Action: requests access to external user page"
        description_string = description_string + ",External User: " +  str(external_user.id)
        description_string = description_string + ",Page: " +  page_to_view
        transaction = InternalNoncriticalTransaction.objects.create(status=TRANSACTION_STATUS_UNRESOLVED, time_created=timezone.now(), type_of_transaction=type_of_transaction, description=description_string, initiator_id=user.id)
        transaction.save()
        return True
    except:
        return False

def create_payment_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    try:
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
    except:
        return False

def create_payment_on_behalf_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    try:
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
    except:
        return False

def create_transfer_transaction(sender, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiver, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    try:
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
    except:
        return False

def credit_or_debit_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    user = request.user
    if type_of_transaction == TRANSACTION_TYPE_CREDIT:
        amount = float(request.POST['credit_amount'])
    if type_of_transaction == TRANSACTION_TYPE_DEBIT:
        amount = float(request.POST['debit_amount'])
    if not validate_amount(amount):
        return HttpResponseRedirect(reverse(error_redirect))
    if is_individual_customer(user) and account_type == ACCOUNT_TYPE_CHECKING:
        account =  user.individualcustomer.checking_account
        user_type = INDIVIDUAL_CUSTOMER
    elif is_individual_customer(user) and account_type == ACCOUNT_TYPE_SAVINGS:
        account =  user.individualcustomer.savings_account
        user_type = INDIVIDUAL_CUSTOMER
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_CHECKING:
        account =  user.merchantorganization.checking_account
        user_type = MERCHANT_ORGANIZATION
    elif is_merchant_organization(user) and account_type == ACCOUNT_TYPE_SAVINGS:
        account =  user.merchantorganization.savings_account
        user_type = MERCHANT_ORGANIZATION
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if type_of_transaction == TRANSACTION_TYPE_CREDIT:
        starting_balance = account.active_balance
        check = max(float(account.active_balance), float(account.current_balance)) + amount
        new_balance = float(starting_balance) + amount
        if validate_amount(check):
            account.active_balance = new_balance
            account.save()
            create_debit_or_credit_transaction(user=user, type_of_transaction=type_of_transaction, userType=user_type, accountType=account_type, accountID=account.id, routingID=account.routing_number, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    elif type_of_transaction == TRANSACTION_TYPE_DEBIT:
        starting_balance = account.active_balance
        check = min(float(account.active_balance), float(account.current_balance)) - amount
        new_balance = float(starting_balance) - amount
        if validate_amount(check):
            account.active_balance = new_balance
            account.save()
            create_debit_or_credit_transaction(user=user, type_of_transaction=type_of_transaction, userType=user_type, accountType=account_type, accountID=account.id, routingID=account.routing_number, amount=amount, starting_balance=starting_balance, ending_balance=new_balance)
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    return HttpResponseRedirect(reverse(success_redirect))

def deny_transaction(transaction, user):
    type_of_transaction = transaction.type_of_transaction
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        result = deny_transaction_credit_or_debit(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        result = deny_transaction_payment(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        result = deny_transaction_transfer(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSACTION_ACCESS_REQUEST:
        result = deny_transaction_internal_noncritical(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST:
        result = deny_transaction_internal_transcaction_for_access(transaction=transaction, user=user)
    elif type_of_transaction == TRANSACTION_TYPE_EXTERNAL_USER_PROFILE_EDIT_REQUEST:
        result = deny_transaction_external_user_profile_edit_request(transaction=transaction, user=user)
    else:
        result = False
    if result:
        pass # remove to test email
        """
        recipients = get_all_emails(transaction.participants.all())
        #send_notification_transaction(subject=TRANSACTION_SUBJECT_DENIED, message=TRANSACTION_MESSAGE, transaction=transaction, status=TRANSACTION_STATUS_DENIED, email_template=None, recipients=[get_user_email(transaction.initiator)])
        send_templated_mail(
            template_name='transaction_denial',
            from_email='group3sbs@gmail.com',
            recipient_list=recipients,
            context={
                'username':"user_name",
            },
            # Optional:
            # cc=['cc@example.com'],
            # bcc=['bcc@example.com'],
            # headers={'My-Custom-Header':'Custom Value'},
            # template_prefix="my_emails/",
            # template_suffix="email",
        )"""
    return result

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

def deny_transaction_external_user_profile_edit_request(transaction, user):
    try:
        save_transaction(transaction=transaction, user=user)
        return True
    except:
        return False

def deny_transaction_internal_noncritical(transaction, user):
    try:
        save_transaction(transaction=transaction, user=user)
        return True
    except:
        return False

def deny_transaction_internal_transcaction_for_access(transaction, user):
    try:
        save_transaction(transaction=transaction, user=user)
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
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
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

def does_internal_access_transaction_already_exists(user, page_to_view):
    result = False
    transactions = InternalNoncriticalTransaction.objects.filter(initiator_id=user.id, status=TRANSACTION_STATUS_UNRESOLVED, type_of_transaction=TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST)
    if transactions.exists():
        for transaction in transactions:
            if transaction.type_of_transaction == TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST:
                data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=transaction.type_of_transaction)
                if 'page_to_view' in data:
                    if data['page_to_view'] == page_to_view:
                        result =  True
                        return True
    return result

def does_user_have_external_user_permission(user, external_user, page_to_view):
    verify = False
    if is_regular_employee(user):
        try:
            if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE:
                permission_codename = 'can_internal_user_edit_external_user_profile_' + str(external_user.id)
            else:
                permission_codename = 'can_view_external_user_' + page_to_view + '_' + str(external_user.id)
            permission = Permission.objects.filter(codename=permission_codename).first()
            permission_codename = 'internal.' + permission_codename
            if permission is None and not does_internal_access_transaction_already_exists(user=user, page_to_view=page_to_view):
                if create_internal_transcaction_for_access(user=user, external_user=external_user, page_to_view=page_to_view):
                    verify = False
            else:
                if user.has_perm(permission_codename):
                    verify = True
                elif not does_internal_access_transaction_already_exists(user=user, page_to_view=page_to_view):
                    if create_internal_transcaction_for_access(user=user, external_user=external_user, page_to_view=page_to_view):
                        pass
        except:
            pass
    elif is_system_manager(user) or is_administrator(user):
        verify = True
    return verify

def get_all_emails(queryset):
    emails = []
    for user in queryset:
        emails.append(get_user_email(user))
    return emails

def get_any_user_profile(username, email=None):
    profile = None
    try:
        user = User.objects.get(username=username)
    except:
        return profile
    if email == None:
        if is_individual_customer(user):
            profile = user.individualcustomer
        elif is_merchant_organization(user):
            profile = user.merchantorganization
        elif is_regular_employee(user):
            profile = user.regularemployee
        elif is_system_manager(user):
            profile = user.systemmanager
        elif is_administrator(user):
            profile = user.administrator
    else:
        if is_individual_customer(user):
            if user.individualcustomer.email == email:
                profile = user.individualcustomer
        elif is_merchant_organization(user):
            if user.merchantorganization.email == email:
                profile = user.merchantorganization
        elif is_regular_employee(user):
            if user.regularemployee.email == email:
                profile = user.regularemployee
        elif is_system_manager(user):
            if user.systemmanager.email == email:
                profile = user.systemmanager
        elif is_administrator(user):
            if user.administrator.email == email:
                profile = user.administrator
    return profile

def get_external_user_account(user, account_type):
    account = None
    if is_external_user(user):
        profile = get_any_user_profile(username=user.username)
        if account_type == ACCOUNT_TYPE_CHECKING and has_checking_account(user):
            account = profile.checking_account
        elif account_type == ACCOUNT_TYPE_SAVINGS and has_savings_account(user):
            account = profile.savings_account
    return account

def get_external_noncritical_transaction(transaction):
    transaction_description = transaction.description
    data = parse_transaction_description(transaction_description=transaction_description, type_of_transaction=TRANSACTION_TYPE_TRANSACTION_ACCESS_REQUEST)
    return data['external_transaction']

def get_external_user(email=None, account_ID=None, routing_ID=None, account_type=None):
    user = None
    if email:
        try:
            user = User.objects.get(individualcustomer__email=email)
        except:
            try:
                user = User.objects.get(merchantorganization__email=email)
            except:
                user = None
    elif routing_ID and account_ID and account_type:
        if account_type == ACCOUNT_TYPE_CHECKING:
            try:
                user = User.objects.get(individualcustomer__checking_account__id=int(account_ID ), individualcustomer__checking_account__routing_number=int(routing_ID))
            except:
                try:
                    user = User.objects.get(merchantorganization__checking_account__id=int(account_ID ), merchantorganization__checking_account__routing_number=int(routing_ID))
                except:
                    user = None
        elif account_type == ACCOUNT_TYPE_SAVINGS:
            try:
                user = User.objects.get(individualcustomer__savings_account__id=int(account_ID ), individualcustomer__savings_account__routing_number=int(routing_ID))
            except:
                try:
                    user = User.objects.get(merchantorganization__savings_account__id=int(account_ID ), merchantorganization__savings_account__routing_number=int(routing_ID))
                except:
                    user = None
        else:
            return user
    else:
        return user
    return user

def get_new_credit_card_number():
    size = CREDIT_CARD_NUMBER_LENGTH
    chars = string.digits
    #
    ccnumber = ''
    for _ in range(size):
        ccnumber += random.choice(chars)

    while(User.objects.filter(merchantorganization__credit_card__creditcard_number=ccnumber) or
          User.objects.filter(individualcustomer__credit_card__creditcard_number=ccnumber)):
        ccnumber = ''
        for _ in range(size):
            ccnumber += random.choice(chars)

    return ccnumber

def get_new_routing_number():
    size = ROUTING_NUMBER_LENGTH - 1
    firstchar = '123456789'
    chars = string.digits

    routing = ''
    routing += random.choice(firstchar)
    for _ in range(size):
        routing += random.choice(chars)

    while(User.objects.filter(merchantorganization__checking_account__routing_number=int(routing)) or
          User.objects.filter(individualcustomer__checking_account__routing_number=int(routing))):
        routing = ''
        routing += random.choice(firstchar)
        for _ in range(size):
            routing += random.choice(chars)

    return int(routing)

def get_user_det(user):
    list = []
    if is_regular_employee(user):
        list.append(user.regularemployee.first_name)
        list.append(user.regularemployee.last_name)
        list.append(REGULAR_EMPLOYEE)
    elif is_system_manager(user):
        list.append(user.systemmanager.first_name)
        list.append(user.systemmanager.last_name)
        list.append(SYSTEM_MANAGER)
    elif is_administrator(user):
        list.append(user.administrator.first_name)
        list.append(user.administrator.last_name)
        list.append(ADMINISTRATOR)
    return list

def get_user_email(user):
    if is_individual_customer(user):
        return user.individualcustomer.email
    elif is_merchant_organization(user):
        return user.merchantorganization.email
    elif is_regular_employee(user):
        return user.regularemployee.email
    elif is_system_manager(user):
        return user.systemmanager.email
    elif is_administrator(user):
        return user.administrator.email
    else:
        return ""

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

def has_permission_to_edit_profile(user):
    if is_external_user(user):
        try:
            permission_codename = 'can_external_user_edit_own_profile_' + str(user.id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'external.' + permission_codename
            if user.has_perm(permission_codename):
                return True
            else:
                return False
        except:
            return False
    else:
        return False

def has_savings_account(user):
    if is_external_user(user) and is_individual_customer(user) and hasattr(user.individualcustomer, SAVINGS_ACCOUNT_ATTRIBUTE):
        return True
    elif is_external_user(user) and is_merchant_organization(user) and hasattr(user.merchantorganization, SAVINGS_ACCOUNT_ATTRIBUTE):
        return True
    else:
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

def otpGenerator(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def parse_transaction_description(transaction_description, type_of_transaction):
    if type_of_transaction == TRANSACTION_TYPE_CREDIT or type_of_transaction == TRANSACTION_TYPE_DEBIT:
        return parse_transaction_description_credit_or_debit(transaction_description=transaction_description)
    elif type_of_transaction == TRANSACTION_TYPE_PAYMENT or type_of_transaction ==  TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        return parse_transaction_description_transfer(transaction_description=transaction_description)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        return parse_transaction_description_transfer(transaction_description=transaction_description)
    elif type_of_transaction == TRANSACTION_TYPE_TRANSACTION_ACCESS_REQUEST:
        return parse_transaction_description_internal_noncritical(transaction_description=transaction_description)
    elif type_of_transaction == TRANSACTION_TYPE_ACCESS_EXTERNAL_USER_REQUEST:
        return parse_transaction_description_internal_transaction_for_access(transaction_description=transaction_description)
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

def parse_transaction_description_internal_noncritical(transaction_description):
    try:
        contents = transaction_description.split(',')
        username = contents[0].split(': ')[1]
        description = contents[1].split(': ')[1]
        external_transaction_id = int(contents[2].split(': ')[1])
        external_transaction = ExternalNoncriticalTransaction.objects.get(id=external_transaction_id)
        return {
            'external_transaction': external_transaction,
        }
    except:
        return {}

def parse_transaction_description_internal_transaction_for_access(transaction_description):
    try:
        contents = transaction_description.split(',')
        contents = transaction_description.split(',')
        username = contents[0].split(': ')[1]
        description = contents[1].split(': ')[1]
        external_user_id = int(contents[2].split(': ')[1])
        page_to_view = contents[3].split(': ')[1]
        external_user = User.objects.get(id=external_user_id)
        return {
            'external_user': external_user,
            'page_to_view' : page_to_view,
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
    if type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
        amount = float(request.POST['payment_on_behalf_amount'])
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if request.POST.get('email_address'):
        email_address = request.POST['email_address']
        sender = get_external_user(email=email_address)
        if sender is None:
            return HttpResponseRedirect(reverse(error_redirect))
        sender_account = get_external_user_account(user=sender, account_type=sender_user_type)
        if sender_account is None:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        sender_account_ID = request.POST['account_number']
        sender_routing_ID = request.POST['route_number']
        if not validate_account_number(account_number=sender_account_ID) or not validate_routing_number(routing_number=sender_routing_ID):
            return HttpResponseRedirect(reverse(error_redirect))
        sender = get_external_user(account_ID=sender_account_ID, routing_ID=sender_routing_ID, account_type=sender_account_type)
        if sender is None:
            return HttpResponseRedirect(reverse(error_redirect))
        sender_account = get_external_user_account(user=sender, account_type=sender_user_type)
        if sender_account is None:
            return HttpResponseRedirect(reverse(error_redirect))
    if sender_account_type == ACCOUNT_TYPE_CHECKING or sender_account_type == ACCOUNT_TYPE_SAVINGS:
        if is_individual_customer(sender):
            sender_user_type = INDIVIDUAL_CUSTOMER
        else:
            return HttpResponseRedirect(reverse(error_redirect))
        sender_check = min(float(sender_account.active_balance), float(sender_account.current_balance)) - amount
        sender_starting_balance = sender_account.active_balance
        sender_new_balance = float(sender_starting_balance) - amount
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if not validate_amount(amount):
        return HttpResponseRedirect(reverse(error_redirect))
    if is_merchant_organization(receiver) and receiver_account_type == ACCOUNT_TYPE_CHECKING:
        receiver_account = receiver.merchantorganization.checking_account
    elif is_merchant_organization(receiver) and receiver_account_type == ACCOUNT_TYPE_SAVINGS:
        receiver_account = receiver.merchantorganization.savings_account
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    receiver_check = max(float(receiver_account.active_balance), float(receiver_account.current_balance)) + amount
    receiver_starting_balance = receiver_account.active_balance
    receiver_user_type = MERCHANT_ORGANIZATION
    receiver_new_balance = float(receiver_starting_balance) + amount
    if validate_amount(sender_check) and validate_amount(receiver_check) and not sender.id == receiver.id:
        sender_account.active_balance = sender_new_balance
        receiver_account.active_balance = receiver_new_balance
        sender_account.save()
        receiver_account.save()
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT_ON_BEHALF:
            create_payment_on_behalf_transaction(sender=sender, senderType=sender_user_type, senderID=sender.id, senderAccountType=sender_account_type, senderAccountID=sender_account.id, senderRoutingID=sender_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
        else:
            sender_account.active_balance = sender_starting_balance
            receiver_account.active_balance = receiver_starting_balance
            sender_account.save()
            receiver_account.save()
            return HttpResponseRedirect(reverse(error_redirect))
        return HttpResponseRedirect(reverse(success_redirect))

def payment_or_transfer_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    user = request.user
    sender_account_type = account_type
    receiver_account_type = request.POST['account_type']
    if type_of_transaction == TRANSACTION_TYPE_PAYMENT:
        amount = float(request.POST['payment_amount'])
    elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
        amount = float(request.POST['transfer_amount'])
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if request.POST.get('email_address'):
        email_address = request.POST['email_address']
        receiver = get_external_user(email=email_address)
        if receiver is None:
            return HttpResponseRedirect(reverse(error_redirect))
        receiver_account = get_external_user_account(user=receiver, account_type=receiver_account_type)
        if receiver_account is None:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        receiver_account_ID = request.POST['account_number']
        receiver_routing_ID = request.POST['route_number']
        if not validate_account_number(account_number=receiver_account_ID) or not validate_routing_number(routing_number=receiver_routing_ID):
            return HttpResponseRedirect(reverse(error_redirect))
        receiver = get_external_user(account_ID=receiver_account_ID, routing_ID=receiver_routing_ID, account_type=receiver_account_type)
        if receiver is None:
            return HttpResponseRedirect(reverse(error_redirect))
        receiver_account = get_external_user_account(user=receiver, account_type=receiver_account_type)
        if receiver_account is None:
            return HttpResponseRedirect(reverse(error_redirect))
    if receiver_account_type == ACCOUNT_TYPE_CHECKING or receiver_account_type == ACCOUNT_TYPE_SAVINGS:
        if is_individual_customer(receiver):
            receiver_user_type = INDIVIDUAL_CUSTOMER
        elif is_merchant_organization(receiver):
            receiver_user_type = MERCHANT_ORGANIZATION
        else:
            return HttpResponseRedirect(reverse(error_redirect))
        receiver_check = max(float(receiver_account.active_balance), float(receiver_account.current_balance)) + amount
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
    sender_check = min(float(user_account.active_balance), float(user_account.current_balance)) - amount
    sender_starting_balance = user_account.active_balance
    sender_new_balance = float(sender_starting_balance) - amount
    if validate_amount(sender_new_balance) and validate_amount(receiver_new_balance) and not user.id == receiver.id:
        user_account.active_balance = sender_new_balance
        receiver_account.active_balance = receiver_new_balance
        user_account.save()
        receiver_account.save()
        if type_of_transaction == TRANSACTION_TYPE_PAYMENT:
            create_payment_transaction(sender=user, senderType=sender_user_type, senderID=user.id, senderAccountType=sender_account_type, senderAccountID=user_account.id, senderRoutingID=user_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
        elif type_of_transaction == TRANSACTION_TYPE_TRANSFER:
            create_transfer_transaction(sender=user, senderType=sender_user_type, senderID=user.id, senderAccountType=sender_account_type, senderAccountID=user_account.id, senderRoutingID=user_account.routing_number, receiver=receiver, receiverType=receiver_user_type, receiverID=receiver.id, receiverAccountType=receiver_account_type, receiverAccountID=receiver_account.id, receiverRoutingID=receiver_account.routing_number, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_new_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_new_balance)
        else:
            user_account.active_balance = sender_starting_balance
            receiver_account.active_balance = receiver_starting_balance
            user_account.save()
            receiver_account.save()
            return HttpResponseRedirect(reverse(error_redirect))
    return HttpResponseRedirect(reverse(success_redirect))

def save_transaction(transaction, user):
    transaction.participants.add(user)
    transaction.resolver = user
    transaction.status = TRANSACTION_STATUS_RESOLVED
    transaction.time_resolved = timezone.now()
    transaction.save()

def send_notification(subject, message, email_template, recipients):
    email = EmailMessage(
        subject=subject,
        body=message,
        to=recipients,
    )
    email.send()

def send_notification_transaction(subject, message, transaction, status, email_template, recipients):
    message = message + status + ':\n'
    message = message + 'Transaction ID: ' + str(transaction.id) + '\n'
    message = message + 'Transaction Type: ' + str(transaction.type_of_transaction) + '\n'
    message = message + 'Transaction Description: ' + str(transaction.description) + '\n'
    email = EmailMessage(
        subject=subject,
        body=message,
        to=recipients,
    )
    email.send()

def transfer_validate(request, type_of_transaction, account_type, success_redirect, error_redirect):
    return payment_or_transfer_validate(request=request, type_of_transaction=type_of_transaction, account_type=account_type, success_redirect=success_redirect, error_redirect=error_redirect)

def validate_account_info(user_type, username, email, first_name, last_name, address, city, state, zipcode, personal_code):
    validate = False
    if validate_user_type_category(user_type=user_type):
        if validate_username(username=username) and validate_email(email=email) and validate_name(name=first_name) and validate_name(name=last_name) and validate_street_address(street_address=address) and validate_city(city=city) and validate_state(state=state) and validate_zipcode(zipcode=zipcode):
            if user_type == INDIVIDUAL_CUSTOMER:
                if validate_ssn(ssn=personal_code):
                    validate = True
            elif user_type == MERCHANT_ORGANIZATION:
                if validate_business_code(business_code=personal_code):
                    validate = True
    return validate

def validate_account_number(account_number):
    validated = False
    try:
        number_string = str(account_number)
        number_string = number_string.zfill(ACCOUNT_NUMBER_LENGTH)
        if len(number_string) == ACCOUNT_NUMBER_LENGTH:
            if re.search('^[0-9]+$', number_string):
                #print('Valid name')
                validated = True
    except:
        pass
    return validated

def validate_credit_card_number(credit_card_number):
    validated = False
    try:
        number_string = str(credit_card_number)
        number_string = number_string.zfill(CREDIT_CARD_NUMBER_LENGTH)
        if len(number_string) == CREDIT_CARD_NUMBER_LENGTH:
            if re.search('^[0-9]+$', number_string):
                #print('Valid name')
                validated = True
    except:
        pass
    return validated

def validate_amount(amount):
    if amount > MAX_BALANCE or amount < MIN_BALANCE:
        return False
    else:
        return True

def validate_business_code(business_code):
    validate = False
    if len(business_code) == BUSINESS_CODE_LENGTH:
        if re.search('^[0-9]+$', business_code):
            try:
                merchant = MerchantOrganization.objects.filter(business_code=business_code)
                if not merchant.exists():
                    validate = True
            except:
                pass
    return validate

def validate_city(city):
    validated = False
    if len(city) <= CITY_LENGTH_MAX and len(city) >= CITY_LENGTH_MIN:
        if re.search('^([a-zA-Z0-9]| )+$', city):
            validated = True
            #print('Valid city')
    return validated

def validate_email(email):
    validated = False
    if len(email) <= EMAIL_LENGTH_MAX and len(email) >= EMAIL_LENGTH_MIN:
        parts = email.strip('\r').strip('\n').split('@')
        if len(parts) == 2:
            local = parts[0]
            domain = parts[1]
            if re.search("^([a-zA-Z0-9]|!|#|\$|%|&|'|\*|\+|-|\/|=|\?|\^\_|`|{|\||}|~|\.|,)+$", local):
                if re.search("^([a-zA-Z0-9]|\.|-)+$", domain):
                    validated = True
    return validated

def validate_name(name):
    validated = False
    if len(name) <= NAME_LENGTH_MAX and len(name) >= NAME_LENGTH_MIN:
        if re.search('^[a-zA-Z]+$', name):
            #print('Valid name')
            validated = True
    return validated

def validate_first_name_save(profile, first_name):
    validated = False
    if len(first_name) <= NAME_LENGTH_MAX and len(first_name) >= NAME_LENGTH_MIN:
        if re.search('^[a-zA-Z]+$', first_name):
            #print('Valid name')
            validated = True
            profile.first_name = first_name
            profile.save()
    return validated

def validate_password(password):
    validated = False
    #print(password)
    if len(password) <= PASSWORD_LENGTH_MAX and len(password) >= PASSWORD_LENGTH_MIN:
        if re.search(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*(~|`|!|@|#|\$|%|\^|&|\*|\(|\)|_|-|\+|=|{|}|\[|\]|\||\\|;|:|\'|\"|,|<|\.|>|\?|\/))([a-zA-Z0-9]|~|`|!|@|#|\$|%|\^|&|\*|\(|\)|_|-|\+|=|{|}|\[|\]|\||\\|;|:|\'|\"|,|<|\.|>|\?|\/)+$', password):
            validated = True
    return validated

def validate_profile_change(profile, first_name, last_name, street_address, city, state, zipcode):
    if validate_name(name=first_name) and validate_name(name=last_name) and validate_street_address(street_address=street_address) and validate_city(city=city) and validate_state(state=state) and validate_zipcode(zipcode=zipcode):
        profile.first_name = first_name
        profile.last_name = last_name
        profile.street_address = street_address
        profile.city = city
        profile.state = state
        profile.zipcode = zipcode
        profile.save()
        return True
    else:
        return False

def validate_routing_number(routing_number):
    validated = False
    try:
        number_string = str(routing_number)
        number_string = number_string.zfill(ROUTING_NUMBER_LENGTH)
        if len(number_string) == ROUTING_NUMBER_LENGTH:
            if re.search('^[0-9]+$', number_string):
                #print('Valid name')
                validated = True
    except:
        pass
    return validated

def validate_ssn(ssn):
    validate = False
    if len(ssn) == SSN_LENGTH:
        if re.search('^[0-9]+$', ssn):
            try:
                customer = IndividualCustomer.objects.filter(ssn=ssn)
                if not customer.exists():
                    validate = True
            except:
                pass
    return validate

def validate_state(state):
    validated = False
    if state in STATES:
        #print('Valid state')
        validated = True
    return validated

def validate_street_address(street_address):
    validated = False
    if len(street_address) <= STREET_ADDRESS_LENGTH_MAX and len(street_address) >= STREET_ADDRESS_LENGTH_MIN:
        if re.search('^([a-zA-Z0-9]| )+$', street_address):
            validated = True
            #print('Valid street address')
    return validated

def validate_user_type(user, user_type):
    if is_individual_customer(user) and user_type == INDIVIDUAL_CUSTOMER:
        return True
    elif is_merchant_organization(user) and user_type == MERCHANT_ORGANIZATION:
        return True
    elif is_regular_employee(user) and user_type == REGULAR_EMPLOYEE:
        return True
    elif is_system_manager(user) and user_type == SYSTEM_MANAGER:
        return True
    elif is_administrator(user) and user_type == ADMINISTRATOR:
        return True
    else:
        return False

def validate_user_type_category(user_type):
    if user_type == INDIVIDUAL_CUSTOMER or user_type == MERCHANT_ORGANIZATION or user_type == REGULAR_EMPLOYEE or user_type == SYSTEM_MANAGER or user_type == ADMINISTRATOR:
        return True
    else:
        return False

def validate_username(username):
    validated = False
    if len(username) <= USERNAME_ADDRESS_LENGTH_MAX and len(username) >= USERNAME_ADDRESS_LENGTH_MIN:
        if re.search('^([a-zA-Z0-9]|_|@|\+|-|\.)+$', username):
            validated = True
    return validated

def validate_zipcode(zipcode):
    validated = False
    if len(zipcode) == ZIPCODE_LENGTH:
        if re.search('^[0-9]+$', zipcode):
            #print('Valid zipcode')
            validated = True
    return validated
