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
from global_templates.common_functions import can_view_noncritical_transaction, can_resolve_internal_noncritical_transaction, can_resolve_noncritical_transaction, create_internal_noncritical_transaction, commit_transaction, deny_transaction, get_external_noncritical_transaction, is_administrator, is_individual_customer, is_internal_user, is_merchant_organization, is_regular_employee, is_system_manager, has_no_account, get_user_det
from global_templates.constants import ACCOUNT_TYPE_CHECKING, ACCOUNT_TYPE_SAVINGS, ADMINISTRATOR, INDIVIDUAL_CUSTOMER, MERCHANT_ORGANIZATION, REGULAR_EMPLOYEE, SYSTEM_MANAGER, TRANSACTION_STATUS_RESOLVED, TRANSACTION_STATUS_UNRESOLVED

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
    list = get_user_det(user)
    if is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_regular_employee(user) or is_system_manager(user):
        can_request = False
        transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        already_exists = InternalNoncriticalTransaction.objects.filter(initiator_id=user.id, status=TRANSACTION_STATUS_UNRESOLVED)
        if not already_exists.exists():
            can_request = True
        if top_noncritical_transaction is None:
            return render(request, 'internal/noncritical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions})
        elif top_critical_transaction is None:
            can_resolve = True
        elif top_critical_transaction.time_created < top_noncritical_transaction.time_created:
            can_resolve = False
        else:
            can_resolve = True
        if is_system_manager(user):
            access_to_resolve = True
        else:
            access_to_resolve = False
            permission_codename = 'internal.can_resolve_external_noncritical_transaction_' + str(top_noncritical_transaction.id)
            if user.has_perm(permission_codename):
                access_to_resolve = True
        return render(request, 'internal/noncritical_transactions.html', {'user_type': list[2],'first_name':list[0],'last_name':list[1],'transactions': transactions, 'can_resolve': can_resolve, 'access_to_resolve': access_to_resolve, 'can_request': can_request})
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# View Critical Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def critical_transactions(request):
    user = request.user
    list = get_user_det(user)
    if is_regular_employee(user) or is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_system_manager(user):
        transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        if top_critical_transaction is None:
            return render(request, 'internal/critical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions})
        elif top_noncritical_transaction is None:
            can_resolve = True
        elif top_critical_transaction.time_created > top_noncritical_transaction.time_created:
            can_resolve = False
        else:
            can_resolve = True
        return render(request, 'internal/critical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'can_resolve': can_resolve})
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# View External User Account Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_account(request, external_user_id):
    user = request.user
    list = get_user_det(user)
    permission_codename = 'internal.can_view_external_user_page_' + external_user_id
    permission = Permission.objects.get(codename='can_view_external_user_page_' + external_user_id)
    if user.has_perm(permission_codename):
        external_user = User.objects.get(id=int(external_user_id))
        if is_individual_customer(external_user) and not has_no_account(external_user):
            return_value = render(request, 'internal/view_external_account.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'int_user_type': INDIVIDUAL_CUSTOMER, 'int_first_name': external_user.individualcustomer.first_name, 'int_last_name': external_user.individualcustomer.last_name, 'checkingaccount': external_user.individualcustomer.checking_account, 'savingsaccount': external_user.individualcustomer.savings_account, 'creditcard': external_user.individualcustomer.credit_card})
        elif is_merchant_organization(external_user) and not has_no_account(external_user):
            return_value = render(request, 'internal/view_external_account.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'int_user_type': MERCHANT_ORGANIZATION, 'int_first_name': external_user.merchantorganization.first_name, 'int_last_name': external_user.merchantorganization.last_name, 'checkingaccount': external_user.merchantorganization.checking_account, 'savingsaccount': external_user.merchantorganization.savings_account, 'creditcard': external_user.merchantorganization.credit_card})
        else:
            return_value = render(request, 'internal/view_external_account.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'error_message': 'User is not an external user to be viewed'})
        user.user_permissions.remove(permission)
        user.save()
        return return_value
    else:
        return HttpResponseRedirect(reverse('internal:index'))

# External User Account Request Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def external_user_account_access_request(request):
    user = request.user
    list = get_user_det(user)
    return render (request, 'internal/external_user_account_access_request.html',{'user_type': list[2], 'first_name': list[0],'last_name':list[1] })


# Internal Noncritical Transactions Page
@never_cache
@login_required
@user_passes_test(can_resolve_internal_noncritical_transaction)
def internal_noncritical_transactions(request):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/internal_noncritical_transactions.html'
    transactions = InternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions})

# Approve Criticial Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_critical_transaction_approval(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/critical_transactions.html'
    success_page_reverse = 'internal:critical_transactions'
    try:
        top_critical_transaction = ExternalCriticalTransaction.objects.get(id=transaction_id)
    except:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if commit_transaction(transaction=top_critical_transaction, user=user):
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Approved transaction not commmited"})

# Deny Criticial Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_critical_transaction_denial(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/critical_transactions.html'
    success_page_reverse = 'internal:critical_transactions'
    try:
        top_critical_transaction = ExternalCriticalTransaction.objects.get(id=transaction_id)
    except:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if deny_transaction(transaction=top_critical_transaction, user=user):
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Denied transaction not commmited"})

# Request External User Transaction Access
@never_cache
@login_required
@user_passes_test(can_resolve_internal_noncritical_transaction)
def validate_external_noncritical_transaction_access_request_approval(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    try:
        internal_transaction = InternalNoncriticalTransaction.objects.get(id=int(transaction_id))
        external_transaction = get_external_noncritical_transaction(internal_transaction)
        initiator = internal_transaction.initiator
    except:
        return HttpResponseRedirect(reverse('internal:error'))
    if is_regular_employee(initiator):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    else:
        return HttpResponseRedirect(reverse('internal:error'))
    permission_codename = 'can_resolve_external_noncritical_transaction_' + str(external_transaction.id)
    permission_name = "Can resolve external noncritical transaction " + str(external_transaction.id)
    try:
        permission = Permission.objects.get(codename=permission_codename, name=permission_name, content_type=content_type)
    except:
        permission = Permission.objects.create(codename=permission_codename,name=permission_name, content_type=content_type)
    if commit_transaction(transaction=internal_transaction, user=user):
        initiator.user_permissions.add(permission)
        initiator.save()
        return HttpResponseRedirect(reverse('internal:internal_noncritical_transactions'))
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# Request External User Transaction Access
@never_cache
@login_required
@user_passes_test(can_resolve_internal_noncritical_transaction)
def validate_external_noncritical_transaction_access_request_denial(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    try:
        transaction = InternalNoncriticalTransaction.objects.get(id=transaction_id)
        if deny_transaction(transaction=transaction, user=user):
            return HttpResponseRedirect(reverse('internal:internal_noncritical_transactions'))
        else:
            return render(request, 'internal/internal_noncritical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'error_message': 'Denied transaction not committed'})
    except:
        return HttpResponseRedirect(reverse('internal:error'))

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

# Validate Internal Noncritical Transactions Reqeust
@never_cache
@login_required
@user_passes_test(is_regular_employee)
def validate_internal_noncritical_transaction_request(request, transaction_id):
    user = request.user
    try:
        external_transaction = ExternalNoncriticalTransaction.objects.get(id=int(transaction_id))
        already_exists = InternalNoncriticalTransaction.objects.filter(initiator_id=user.id, status=TRANSACTION_STATUS_UNRESOLVED)
        if already_exists.exists():
            raise Exception
    except:
        return HttpResponseRedirect(reverse('internal:index'))
    if create_internal_noncritical_transaction(user=user, external_transaction=external_transaction):
        return HttpResponseRedirect(reverse('internal:noncritical_transactions'))
    else:
        return HttpResponseRedirect(reverse('internal:error'))

# Approve Non-criticial Transactions
@never_cache
@login_required
@user_passes_test(can_view_noncritical_transaction)
def validate_noncritical_transaction_approval(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/noncritical_transactions.html'
    success_page_reverse = 'internal:noncritical_transactions'
    try:
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.get(id=transaction_id)
    except:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if commit_transaction(transaction=top_noncritical_transaction, user=user):
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Approved transaction not commmited"})

# Deny Non-criticial Transactions
@never_cache
@login_required
@user_passes_test(can_view_noncritical_transaction)
def validate_noncritical_transaction_denial(request, transaction_id):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/noncritical_transactions.html'
    success_page_reverse = 'internal:noncritical_transactions'
    try:
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.get(id=transaction_id)
    except:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if deny_transaction(transaction=top_noncritical_transaction, user=user):
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Denied transaction not commmited"})
