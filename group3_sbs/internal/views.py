from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from easy_pdf.rendering import render_to_pdf_response
from external.models import *
from internal.models import *
from global_templates.common_functions import *
from global_templates.constants import *
from group3_sbs.settings import BASE_DIR
from datetime import date
import datetime, os

""" Render Web Pages """

@never_cache
@login_required
@user_passes_test(is_administrator)
def bineeta_cron_job_late_charge(request):
    return render(request, 'internal/monthly_cron.html')

# View Critical Transactions
@never_cache
@login_required
@user_passes_test(is_system_manager)
def critical_transactions(request):
    user = request.user
    if is_regular_employee(user) or is_administrator(user):
        return render(request, 'internal/index.html')
    elif is_system_manager(user):
        transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
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

# Edit External User Profile Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def edit_external_user_profile(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_EDIT_PROFILE
    success_page = "internal/edit_external_user_profile.html"
    error_redirect = "internal:index"
    if can_edit_external_user_page(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=int(external_user_id))
            if not is_external_user(external_user):
                raise Exception
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        profile = get_any_user_profile(username=external_user.username)
        return render(request, success_page, {"external_user": external_user, "profile": profile, 'STATES': STATES})
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Edit Internal User Profile Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def edit_internal_user_profile(request, internal_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_EDIT_PROFILE
    success_page = "internal/edit_internal_user_profile.html"
    error_redirect = "internal:index"
    try:
        internal_user = User.objects.get(id=int(internal_user_id))
        if not is_internal_user(internal_user):
            raise Exception
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    profile = get_any_user_profile(username=internal_user.username)
    return render(request, success_page, {"internal_user": internal_user, "profile": profile, 'STATES': STATES})

# # Edit Noncritical Transaction
# @never_cache
# @login_required
# @user_passes_test(is_system_manager)
# def edit_noncritical_transaction(request, transaction_id):
#     user = request.user
#     try:
#         transaction = ExternalNoncriticalTransaction.objects.get(id=int(transaction_id))
#         return render(request, 'internal/edit_noncritical_transaction.html', {'transaction': transaction})
#     except:
#         return HttpResponseRedirect(reverse('internal:error'))

# Internal User Error Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def error(request):
    return render(request, 'internal/error.html')

# External User Account Request Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def external_user_access_request(request):
    user = request.user
    list = get_user_det(user)
    return render(request, 'internal/external_user_access_request.html',{'user_type': list[2], 'first_name': list[0],'last_name':list[1] })

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

# Internal Noncritical Transactions Page
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
def internal_noncritical_transactions(request):
    user = request.user
    success_page = 'internal/internal_noncritical_transactions.html'
    transactions = InternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    return render(request, success_page, {'transactions': transactions})

# Internal Critical Transactions Page
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
def internal_critical_transactions(request):
    user = request.user
    success_page = 'internal/internal_critical_transactions.html'
    transactions = InternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    return render(request, success_page, {'transactions': transactions})

# Internal Noncritical Transactions Page
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
def internal_noncritical_transactions(request):
    user = request.user
    list = get_user_det(user)
    success_page = 'internal/internal_noncritical_transactions.html'
    transactions = InternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions})

# Request Access to Internal User Personal Account Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def internal_user_access_request(request):
    user = request.user
    list = get_user_det(user)
    return render(request, 'internal/internal_user_access_request.html',{'user_type': list[2], 'first_name': list[0],'last_name':list[1] })

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

# Create Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_create_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/create_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# External Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_external_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/external_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# View External User Checking Account Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_user_checking_account(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_CHECKING_ACCOUNT
    success_page = "internal/view_external_user_" + page_to_view + ".html"
    error_redirect = "internal:index"
    if can_view_external_user_page(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=int(external_user_id))
            if not is_external_user(external_user):
                raise Exception
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        checking_account = get_external_user_account(user=external_user, account_type=ACCOUNT_TYPE_CHECKING)
        return render(request, success_page, {"user": external_user, "checking_account": checking_account})
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# View External User Credit Card Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_user_credit_card(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_CREDIT_CARD
    success_page = "internal/view_external_user_" + page_to_view + ".html"
    error_redirect = "internal:index"
    if can_view_external_user_page(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=int(external_user_id))
            if not is_external_user(external_user):
                raise Exception
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        credit_card = get_external_user_account(user=external_user, account_type=CREDIT_CARD)
        return render(request, success_page, {"user": external_user, "credit_card": credit_card})
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# View External User Profile Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_user_profile(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_PROFILE
    success_page = "internal/view_external_user_" + page_to_view + ".html"
    error_redirect = "internal:index"
    admin_privilege = False
    if can_view_external_user_page(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=int(external_user_id))
            if not is_external_user(external_user):
                raise Exception
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        profile = get_any_user_profile(username=external_user.username)
        if is_administrator(user):
            admin_privilege = True
        return render(request, success_page, {"user": external_user, "profile": profile, 'admin_privilege': admin_privilege})
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# View External User Savings Account Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def view_external_user_savings_account(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_SAVINGS_ACCOUNT
    success_page = "internal/view_external_user_" + page_to_view + ".html"
    error_redirect = "internal:index"
    if can_view_external_user_page(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=int(external_user_id))
            if not is_external_user(external_user):
                raise Exception
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        savings_account = get_external_user_account(user=external_user, account_type=ACCOUNT_TYPE_SAVINGS)
        return render(request, success_page, {"user": external_user, "savings_account": savings_account})
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Internal Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_internal_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/internal_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Login Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_login_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/login_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# View Internal User Profile Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_internal_user_profile(request, internal_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_PROFILE
    success_page = "internal/view_internal_user_" + page_to_view + ".html"
    error_redirect = "internal:index"
    try:
        internal_user = User.objects.get(id=internal_user_id)
        if not is_internal_user(internal_user):
            raise Exception
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    profile = get_any_user_profile(username=internal_user.username)
    return render(request, success_page, {"user": internal_user, "profile": profile})

# Reset Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_reset_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/reset_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Server Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_server_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/server_log.log')
        print('Base Dir', BASE_DIR)
        print('File Name', file_name)
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        return HttpResponseRedirect(reverse('internal:error'))

""" Validate Webpages """

@never_cache
@login_required
@user_passes_test(is_administrator)
def bineeta_cron_job_late_charge_validate(request):
    if request.method == "POST" and date(date.today().year, date.today().month, 1) == date.today():
        new_date = False
        credit_payment_manager = CreditPaymentManager.objects.all().first()
        if not credit_payment_manager:
            credit_payment_manager = CreditPaymentManager.objects.create(last_day_late_fee_date_executed=timezone.now(), last_month_late_fee_date_executed=timezone.now())
            new_date = True
        current_time = timezone.now()
        last_executed = credit_payment_manager.last_month_late_fee_date_executed
        if not (current_time.year == last_executed.year and last_executed.month < current_time.month) and not new_date:
            return render(request, 'internal/monthly_cron.html', {'message': "Unsuccessfully charged any late cards. Can only update charges once on a month."})
        late_credit_card = CreditCard.objects.filter(remaining_credit__lt = 1000)
        for card in late_credit_card:
            card.days_late = card.days_late + 1
            fee = CREDIT_CARD_INTEREST_RATE * card.days_late
            card.late_fee = min(1000.00, fee)
            card.save()
        return render(request, 'internal/monthly_cron.html', {'message': "Successfully charged any late cards this month."})
    else:
        return render(request, 'internal/monthly_cron.html', {'message': "Unsuccessfully charged any late cards. Can only update charges once on a month on the first day of the month."})

@never_cache
@login_required
@user_passes_test(is_administrator)
def bineeta_cron_job_daily_late_charge_validate(request):
    min_time = datetime.time(23, 59, 00)
    max_time = datetime.time(23, 59, 59)
    if request.method == "POST" and datetime.datetime.time(datetime.datetime.now()) >= max_time and request.method == "POST" and datetime.datetime.time(datetime.datetime.now()) <= max_time:
        new_date = False
        credit_payment_manager = CreditPaymentManager.objects.all().first()
        if not credit_payment_manager:
            credit_payment_manager = CreditPaymentManager.objects.create(last_day_late_fee_date_executed=timezone.now(), last_month_late_fee_date_executed=timezone.now())
            new_date = True
        current_time = timezone.now()
        last_executed = credit_payment_manager.last_month_late_fee_date_executed
        if not (current_time.year == last_executed.year and last_executed.month == current_time.month and last_executed.day < current_time.day) and not new_date:
            return render(request, 'internal/monthly_cron.html', {'message': "Did not update late charges. Can only update charges once on a day."})
        late_credit_card = CreditCard.objects.filter(Q(late_fee__gt=0) | Q(days_late__gt=0))
        no_longer_late = CreditCard.objects.filter(Q(late_fee=0) | Q(days_late__gt=0))
        for card in late_credit_card:
            card.days_late = card.days_late + 1
            fee = CREDIT_CARD_INTEREST_RATE * card.days_late
            card.late_fee = min(1000.00, fee)
            card.save()
        for card in no_longer_late:
            card.days_late = 0
            card.save()
        return render(request, 'internal/monthly_cron.html', {'message': "Updated late charges today."})
    else:
        return render(request, 'internal/monthly_cron.html', {'message': "Did not update late charges. Can only update charges between 23:00 and 23:59."})

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

# Validate deactivate external user account
@never_cache
@login_required
@user_passes_test(is_internal_user)
def validate_deactivate_external_user(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_DEACTIVATE
    success_page = "internal:index"
    error_redirect = "internal:error"
    if can_activate_deactivate_external_user(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=external_user_id)
            if is_external_user(external_user) and user.id != external_user_id:
                external_user.is_active = False
                external_user.save()
                return HttpResponseRedirect(reverse(success_page))
            else:
                return HttpResponseRedirect(reverse(error_redirect))
        except:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Validate reactivate external user account
@never_cache
@login_required
@user_passes_test(is_internal_user)
def validate_reactivate_external_user(request, external_user_id):
    user = request.user
    page_to_view = PAGE_TO_VIEW_REACTIVATE
    success_page = "internal:index"
    error_redirect = "internal:error"
    if can_activate_deactivate_external_user(user=user, external_user_id=external_user_id, page_to_view=page_to_view):
        try:
            external_user = User.objects.get(id=external_user_id)
            if is_external_user(external_user) and user.id != external_user_id:
                external_user.is_active = True
                external_user.save()
                return HttpResponseRedirect(reverse(success_page))
            else:
                return HttpResponseRedirect(reverse(error_redirect))
        except:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Validate deactivate internal user account
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_deactivate_internal_user(request, internal_user_id):
    user = request.user
    try:
        internal_user = User.objects.get(id=internal_user_id)
        if is_internal_user(internal_user) and user.id != internal_user_id:
            internal_user.is_active = False
            internal_user.save()
            return HttpResponseRedirect(reverse('internal:index'))
        else:
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Validate reactivate internal user account
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_reactivate_internal_user(request, internal_user_id):
    user = request.user
    try:
        internal_user = User.objects.get(id=internal_user_id)
        if is_internal_user(internal_user) and user.id != internal_user_id:
            internal_user.is_active = True
            internal_user.save()
            return HttpResponseRedirect(reverse('internal:index'))
        else:
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Validate delete critical transaction
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_delete_critical_transaction(request, transaction_id):
    user = request.user
    try:
        transaction = ExternalCriticalTransaction.objects.get(id=int(transaction_id))
        if deny_transaction(transaction, user):
            transaction.delete()
            return HttpResponseRedirect(reverse('internal:critical_transactions'))
        else:
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Validate delete noncritical transaction
@never_cache
@login_required
@user_passes_test(is_system_manager)
def validate_delete_noncritical_transaction(request, transaction_id):
    user = request.user
    try:
        transaction = ExternalNoncriticalTransaction.objects.get(id=int(transaction_id))
        if deny_transaction(transaction, user):
            transaction.delete()
            return HttpResponseRedirect(reverse('internal:noncritical_transactions'))
        else:
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        return HttpResponseRedirect(reverse('internal:error'))

# Edit External Noncritical Transaction
# @never_cache
# @login_required
# @user_passes_test(is_system_manager)
# def validate_edit_noncritical_transaction(request, transaction_id):
#     user = request.user
#     try:
#         transaction = ExternalNoncriticalTransaction.objects.get(id=int(transaction_id))
#         type_of_transaction = request.POST['type_of_transaction']
#         status = request.POST['status']
#         description = request.POST['description']
#         if validate_noncritical_transaction_modification(description=description, status=status, type_of_transaction=type_of_transaction, transaction=transaction, user=user):
#             return HttpResponseRedirect(reverse('internal:noncritical_transactions'))
#         else:
#             return HttpResponseRedirect(reverse('internal:error'))
#     except:
#         return HttpResponseRedirect(reverse('internal:error'))

# Request External User Transaction Access
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
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
@user_passes_test(can_resolve_internal_transaction)
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
def validate_external_user_access_request(request):
    user = request.user
    error_redirect = "internal:error"
    external_user_id = request.POST['external_user_id']
    page_to_view = request.POST['page_to_view']
    if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE and not is_administrator(user):
        success_redirect = "internal:edit_external_user_profile"
    elif (page_to_view == PAGE_TO_VIEW_DEACTIVATE or page_to_view == PAGE_TO_VIEW_REACTIVATE) and not is_administrator(user):
        success_redirect = "internal:validate_" + page_to_view + "_external_user"
    elif page_to_view == PAGE_TO_VIEW_EDIT_PROFILE and is_administrator(user):
        return HttpResponseRedirect(reverse(error_redirect))
    elif (page_to_view == PAGE_TO_VIEW_DEACTIVATE or page_to_view == PAGE_TO_VIEW_REACTIVATE) and is_administrator(user):
        return HttpResponseRedirect(reverse(error_redirect))
    else:
        success_redirect = "internal:view_external_user_" + page_to_view
    pending_approval_redirect = "internal:index"
    try:
        external_user = User.objects.get(id=int(external_user_id))
        if not is_external_user(external_user):
            raise Exception
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    access_granted = does_user_have_external_user_permission(user=user, external_user=external_user, page_to_view=page_to_view)
    if access_granted:
        return HttpResponseRedirect(reverse(success_redirect, kwargs={'external_user_id': external_user.id}))
    elif is_regular_employee(user) and not access_granted:
        accessRequestObject = accessRequests.objects.create(internalUserId=user.id, externalUserId=external_user_id , pageToView=page_to_view)
        accessRequestObject.save()
        return HttpResponseRedirect(reverse(pending_approval_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Validate Internal Critical Transactions Reqeust
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
def validate_internal_critical_transaction_access_request_approval(request, transaction_id):
    user = request.user
    success_redirect = "internal:internal_critical_transactions"
    error_redirect = "internal:error"
    try:
        internal_transaction = InternalCriticalTransaction.objects.get(id=int(transaction_id))
        initiator = internal_transaction.initiator
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    if is_regular_employee(initiator):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if commit_transaction(transaction=internal_transaction, user=user):
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Validate Internal Critical Transactions Reqeust
@never_cache
@login_required
@user_passes_test(can_resolve_internal_transaction)
def validate_internal_critical_transaction_access_request_denial(request, transaction_id):
    user = request.user
    success_redirect = "internal:internal_critical_transactions"
    error_redirect = "internal:error"
    try:
        internal_transaction = InternalCriticalTransaction.objects.get(id=int(transaction_id))
        initiator = internal_transaction.initiator
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    if is_regular_employee(initiator):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    else:
        return HttpResponseRedirect(reverse(error_redirect))
    if deny_transaction(transaction=internal_transaction, user=user):
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

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

# Validate Internal User Profile Edit Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_internal_profile_edit(request, internal_user_id):
    user = request.user
    success_redirect = 'internal:index'
    error_redirect = 'internal:error'
    username = request.POST['username']
    profile = get_any_user_profile(username=username)
    if int(profile.user.id) != int(internal_user_id):
        return HttpResponseRedirect(reverse(error_redirect))
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    street_address = request.POST['street_address']
    city = request.POST['city']
    state = request.POST['state']
    zipcode = request.POST['zipcode']
    if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))

# Request Internal User Account Access
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_internal_user_access_request(request):
    user = request.user
    error_redirect = "internal:error"
    internal_user_id = request.POST['internal_user_id']
    page_to_view = request.POST['page_to_view']
    if page_to_view == PAGE_TO_VIEW_EDIT_PROFILE:
        success_redirect = "internal:edit_internal_user_profile"
    elif (page_to_view == PAGE_TO_VIEW_DEACTIVATE or page_to_view == PAGE_TO_VIEW_REACTIVATE):
        success_redirect = "internal:validate_" + page_to_view + "_internal_user"
    else:
        success_redirect = "internal:view_internal_user_" + page_to_view
    try:
        internal_user = User.objects.get(id=int(internal_user_id))
        if not is_internal_user(internal_user):
            raise Exception
    except:
        return HttpResponseRedirect(reverse(error_redirect))
    return HttpResponseRedirect(reverse(success_redirect, kwargs={'internal_user_id': internal_user.id}))

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

# Validate Profile Edit Page
@never_cache
@login_required
@user_passes_test(is_internal_user)
def validate_profile_edit(request, external_user_id):
    user = request.user
    success_redirect = 'internal:index'
    error_redirect = 'internal:error'
    username = request.POST['username']
    profile = get_any_user_profile(username=username)
    if int(profile.user.id) != int(external_user_id):
        return HttpResponseRedirect(reverse(error_redirect))
    first_name = request.POST['first_name']
    """ This preserves PII privilege of editing profile
    last_name = request.POST['last_name']
    street_address = request.POST['street_address']
    city = request.POST['city']
    state = request.POST['state']
    zipcode = request.POST['zipcode']
    """
    if is_system_manager(user):
        """ This preserves PII privilege of editing profile
        if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
        """
        if validate_first_name_save(profile=profile, first_name=first_name):
            return HttpResponseRedirect(reverse(success_redirect))
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    elif is_regular_employee(user):
        try:
            permission_codename = 'can_internal_user_edit_external_user_profile_' + str(external_user_id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'internal.' + permission_codename
        except:
            return HttpResponseRedirect(reverse(error_redirect))
        if user.has_perm(permission_codename):
            """ This preserves PII privilege of editing profile
            if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
            """
            if validate_first_name_save(profile=profile, first_name=first_name):
                user.user_permissions.remove(permission)
                user.save()
                return HttpResponseRedirect(reverse(success_redirect))
            else:
                return HttpResponseRedirect(reverse(error_redirect))
        else:
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        return HttpResponseRedirect(reverse(error_redirect))
