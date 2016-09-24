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
from internal.models import Administrator, RegularEmployee, SystemManager
from global_templates.common_functions import can_view_noncritical_transaction, commit_transaction, deny_transaction, is_administrator, is_individual_customer, is_internal_user, is_merchant_organization, is_regular_employee, is_system_manager, has_no_account
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, ADMINISTRATOR, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, REGULAR_EMPLOYEE, SYSTEM_MANAGER

# Create your views here.

# Internal User Home Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def index(request):
    user = request.user
    if is_regular_employee(user):
        return render(request, 'internal/index.html', {'user_type': REGULAR_EMPLOYEE, 'first_name': user.regularemployee.first_name, 'last_name': user.regularemployee.last_name})
    elif is_system_manager(user):
        return render(request, 'internal/index.html', {'user_type': SYSTEM_MANAGER, 'first_name': user.systemmanager.first_name, 'last_name': user.systemmanager.last_name})
    elif is_administrator(user):
        return render(request, 'internal/index.html', {'user_type': ADMINISTRATOR, 'first_name': user.administrator.first_name, 'last_name': user.administrator.last_name})
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# Internal User Error Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def error(request):
    return render(request, 'internal/error.html')

# View Noncritical Transactions
@never_cache
@login_required
@user_passes_test(is_internal_user)
def noncritical_transactions(request):
    user = request.user
    if is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_regular_employee(user) or is_system_manager(user):
        transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
        if top_noncritical_transaction is None:
            return render(request, 'internal/noncritical_transactions.html', {'transactions': transactions})
        elif top_critical_transaction is None:
            can_resolve = True
        elif top_critical_transaction.time_created < top_noncritical_transaction.time_created:
            can_resolve = False
        else:
            can_resolve = True
        return render(request, 'internal/noncritical_transactions.html', {'transactions': transactions, 'can_resolve': can_resolve })
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# View Critical Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def critical_transactions(request):
    user = request.user
    if is_regular_employee(user) or is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_system_manager(user):
        transactions = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
        if top_critical_transaction is None:
            return render(request, 'internal/critical_transactions.html', {'transactions': transactions})
        elif top_noncritical_transaction is None:
            can_resolve = True
        elif top_critical_transaction.time_created > top_noncritical_transaction.time_created:
            can_resolve = False
        else:
            can_resolve = True
        return render(request, 'internal/critical_transactions.html', {'transactions': transactions, 'can_resolve': can_resolve})
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# View External User Account Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_account(request, external_user_id):
    user = request.user
    permission_codename = 'internal.can_view_external_user_page_' + external_user_id
    permission = Permission.objects.get(codename='can_view_external_user_page_' + external_user_id)
    if user.has_perm(permission_codename):
        external_user = User.objects.get(id=int(external_user_id))
        if is_individual_customer(external_user) and not has_no_account(external_user):
            return_value = render(request, 'internal/view_external_account.html', {'user_type': INDIVIDUAL_CUSTOMER, 'first_name': external_user.individualcustomer.first_name, 'last_name': external_user.individualcustomer.last_name, 'checkingaccount': external_user.individualcustomer.checking_account, 'savingsaccount': external_user.individualcustomer.savings_account, 'creditcard': external_user.individualcustomer.credit_card})
        elif is_merchant_organization(external_user) and not has_no_account(external_user):
            return_value = render(request, 'internal/view_external_account.html', {'user_type': MERCHANT_ORGANIZATION, 'first_name': external_user.merchantorganization.first_name, 'last_name': external_user.merchantorganization.last_name, 'checkingaccount': external_user.merchantorganization.checking_account, 'savingsaccount': external_user.merchantorganization.savings_account, 'creditcard': external_user.merchantorganization.credit_card})
        else:
            return_value = render(request, 'internal/view_external_account.html', {'error_message': 'User is not an external user to be viewed'})
        user.user_permissions.remove(permission)
        return return_value
    else:
        return HttpResponseRedirect(reverse('internal:index'))

# External User Account Request Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def external_user_account_access_request(request):
    return render (request, 'internal/external_user_account_access_request.html')

# Request External User Account Access
@never_cache
@login_required
@user_passes_test(is_internal_user)
def validate_external_account_access_request(request):
    user = request.user
    external_user_id = request.POST['external_user_id']
    try:
        external_user = User.objects.get(id=int(external_user_id))
    except:
        return HttpResponseRedirect(reverse('internal:error'))
    if is_regular_employee(user):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    elif is_system_manager(user):
        content_type = ContentType.objects.get_for_model(SystemManager)
    elif is_administrator(user):
        content_type = ContentType.objects.get_for_model(Administrator)
    else:
        return HttpResponseRedirect(reverse('internal:error'))
    permission_codename = 'can_view_external_user_page_' + external_user_id
    permission_name = "Can view external user " + external_user_id + "'s page"
    try:
        permission = Permission.objects.get(codename=permission_codename, name=permission_name, content_type=content_type)
    except:
        permission = Permission.objects.create(codename=permission_codename,name=permission_name, content_type=content_type)
    user.user_permissions.add(permission)
    user.save()
    return HttpResponseRedirect(reverse('internal:index'))

# Approve Criticial Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_critical_transaction_approval(request, transaction_id):
    user = request.user
    success_page = 'internal/critical_transactions.html'
    success_page_reverse = 'internal:critical_transactions'
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
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
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
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
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
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
    top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created').first()
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status="resolved").order_by('time_created')
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
