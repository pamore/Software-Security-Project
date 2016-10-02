from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.decorators.cache import never_cache
from external.models import ExternalNoncriticalTransaction, ExternalCriticalTransaction
from internal.models import Administrator, RegularEmployee, SystemManager, InternalNoncriticalTransaction, InternalCriticalTransaction
from global_templates.common_functions import can_view_noncritical_transaction, can_resolve_internal_noncritical_transaction, can_resolve_noncritical_transaction, create_internal_noncritical_transaction, commit_transaction, deny_transaction, get_external_noncritical_transaction, is_administrator, is_individual_customer, is_internal_user, is_merchant_organization, is_regular_employee, is_system_manager, has_no_account
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, ADMINISTRATOR, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, REGULAR_EMPLOYEE, SYSTEM_MANAGER, TRANSACTION_STATUS_RESOLVED, TRANSACTION_STATUS_UNRESOLVED

@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_critical_transaction_approval(request, transaction_id):
    user = request.user
    success_page = 'internal/critical_transactions.html'
    success_page_reverse = 'internal:critical_transactions'
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if top_noncritical_transaction is None and not top_critical_transaction is None:
        if commit_transaction(transaction=top_critical_transaction, user=user):
            return HttpResponseRedirect(reverse(success_page_reverse))
        else:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Approved transaction not commmited"})
    elif top_critical_transaction is None:
        return render(request, success_page, {'transactions': transactions, 'error_message': "No critical transactions to approve"})
    if top_critical_transaction.time_created > top_noncritical_transaction.time_created:
        return render(request, success_page, {'transactions': transactions, 'error_message': "Non-critical transaction requested before this critical transaction must be resolved"})
    else:
        if int(transaction_id) != top_critical_transaction.id:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Given critical transaction does not match oldest critical transaction to be resolved"})
        else:
            if commit_transaction(transaction=top_critical_transaction, user=user):
                return HttpResponseRedirect(reverse(success_page_reverse))
            else:
                return render(request, success_page, {'transactions': transactions, 'error_message': "Approved transaction not commmited"})

# Deny Criticial Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_critical_transaction_denial(request, transaction_id):
    user = request.user
    success_page = 'internal/critical_transactions.html'
    success_page_reverse = 'internal:critical_transactions'
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if top_noncritical_transaction is None and not top_critical_transaction is None:
        if deny_transaction(transaction=top_critical_transaction, user=user):
            return HttpResponseRedirect(reverse(success_page_reverse))
        else:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Denied transaction not commmited"})
    elif top_critical_transaction is None:
        return render(request, success_page, {'transactions': transactions, 'error_message': "No critical transactions to approve"})
    if top_critical_transaction.time_created > top_noncritical_transaction.time_created:
        return render(request, success_page, {'transactions': transactions, 'error_message': "Non-critical transaction requested before this critical transaction must be resolved"})
    else:
        if int(transaction_id) != top_critical_transaction.id:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Given critical transaction does not match oldest critical transaction to be resolved"})
        else:
            if deny_transaction(transaction=top_critical_transaction, user=user):
                return HttpResponseRedirect(reverse(success_page_reverse))
            else:
                return render(request, success_page, {'transactions': transactions, 'error_message': "Denied transaction not commmited"})

# Approve Non-criticial Transactions
@never_cache
@login_required
@user_passes_test(can_view_noncritical_transaction)
def validate_noncritical_transaction_approval(request, transaction_id):
    user = request.user
    success_page = 'internal/noncritical_transactions.html'
    success_page_reverse = 'internal:noncritical_transactions'
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        return render(request, success_page, {'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if top_critical_transaction is None and not top_noncritical_transaction is None:
        if commit_transaction(transaction=top_noncritical_transaction, user=user):
            return HttpResponseRedirect(reverse(success_page_reverse))
        else:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Approved transaction not commmited"})
    elif top_noncritical_transaction is None:
        return render(request, success_page, {'transactions': transactions, 'error_message': "No critical transactions to approve"})
    if top_critical_transaction.time_created < top_noncritical_transaction.time_created:
        return render(request, success_page, {'transactions': transactions, 'error_message': "System manager must resolve of critical transaction requested before this non-critical transaction"})
    else:
        if int(transaction_id) != top_noncritical_transaction.id:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Given non-critical transaction does not match oldest non-critical transaction to be resolved"})
        else:
            if commit_transaction(transaction=top_noncritical_transaction, user=user):
                return HttpResponseRedirect(reverse(success_page_reverse))
            else:
                return render(request, success_page, {'transactions': transactions, 'error_message': "Approved transaction not commmited"})

# Deny Non-criticial Transactions
@never_cache
@login_required
@user_passes_test(can_view_noncritical_transaction)
def validate_noncritical_transaction_denial(request, transaction_id):
    user = request.user
    success_page = 'internal/noncritical_transactions.html'
    success_page_reverse = 'internal:noncritical_transactions'
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        return render(request, success_page, {'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if top_critical_transaction is None and not top_noncritical_transaction is None:
        if deny_transaction(transaction=top_noncritical_transaction, user=user):
            return HttpResponseRedirect(reverse(success_page_reverse))
        else:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Approved transaction not commmited"})
    elif top_noncritical_transaction is None:
        return render(request, success_page, {'transactions': transactions, 'error_message': "No critical transactions to approve"})
    if top_critical_transaction.time_created < top_noncritical_transaction.time_created:
        return render(request, success_page, {'transactions': transactions, 'error_message': "System manager must resolve of critical transaction requested before this non-critical transaction"})
    else:
        if int(transaction_id) != top_noncritical_transaction.id:
            return render(request, success_page, {'transactions': transactions, 'error_message': "Given non-critical transaction does not match oldest non-critical transaction to be resolved"})
        else:
            if deny_transaction(transaction=top_critical_transaction, user=user):
                return HttpResponseRedirect(reverse(success_page_reverse))
            else:
                return render(request, success_page, {'transactions': transactions, 'error_message': "Denied transaction not commmited"})
