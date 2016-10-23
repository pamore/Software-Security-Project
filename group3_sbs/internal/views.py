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
import datetime, logging, os

logger = logging.getLogger('internal')

""" Render Web Pages """

@never_cache
@login_required
@user_passes_test(is_administrator)
def bineeta_cron_job_late_charge(request):
    return render(request, 'internal/monthly_cron.html')

# Page to allow admin to clear logs
@never_cache
@login_required
@user_passes_test(is_administrator)
def clear_log(request):
    return render(request, 'internal/clear_log.html')

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
        can_resolve = True
        return render(request, 'internal/critical_transactions.html', {'transactions': transactions, 'can_resolve': can_resolve})
    else:
        logger.info("User %s tried to access external critical transaction page but is not an system manager" % (request.user.username))
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
            logger.info("User %s tried to edit non-existant external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
        profile = get_any_user_profile(username=external_user.username)
        logger.info("User %s is editing external user %s's profile " % (request.user.username, external_user.username))
        return render(request, success_page, {"external_user": external_user, "profile": profile, 'STATES': STATES})
    else:
        logger.info("User %s does not have permission to edit external user %s's profile" % (request.user.username, str(external_user_id)))
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
        logger.info("User %s tried to edit a non-existant internal user %s " % (request.user.username, str(internal_user_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    profile = get_any_user_profile(username=internal_user.username)
    logger.info("User %s is editing interal user %s's profile " % (request.user.username, internal_user.username))
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
        logger.info("User %s tried to access internal user page without being an internal user" % (request.user.username))
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
        #can_request = False
        can_request = True
        transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
        top_critical_transaction = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        top_noncritical_transaction = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created').first()
        already_exists = InternalNoncriticalTransaction.objects.filter(initiator_id=user.id, status=TRANSACTION_STATUS_UNRESOLVED)
        if not already_exists.exists():
            #can_request = True
            can_request = True
        if top_noncritical_transaction is None:
            return render(request, 'internal/noncritical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions})
        elif top_critical_transaction is None:
            can_resolve = True
        elif top_critical_transaction.time_created < top_noncritical_transaction.time_created:
            #can_resolve = False
            can_resolve = True
        else:
            can_resolve = True
        if is_system_manager(user):
            access_to_resolve = True
            can_request = False
        else:
            access_to_resolve = False
            permission_codename = 'internal.can_resolve_external_noncritical_transaction_' + str(top_noncritical_transaction.id)
            if user.has_perm(permission_codename):
                access_to_resolve = True
        return render(request, 'internal/noncritical_transactions.html', {'user_type': list[2],'first_name':list[0],'last_name':list[1],'transactions': transactions, 'can_resolve': can_resolve, 'access_to_resolve': access_to_resolve, 'can_request': can_request})
    else:
        logger.info("User %s tried to access noncritical transaction page without being an internal employee" % (request.user.username))
        return HttpResponseRedirect(reverse('internal:error'))

# Create Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_create_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/create_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view create log " % (request.user.username))
        return HttpResponseRedirect(reverse('internal:error'))

# External Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_external_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/external_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view external log " % (request.user.username))
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
            logger.info("User %s tried to view checking account of non-existant external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
        checking_account = get_external_user_account(user=external_user, account_type=ACCOUNT_TYPE_CHECKING)
        logger.info("User %s is viewing external user %s's checking account" % (request.user.username, str(external_user.username)))
        return render(request, success_page, {"user": external_user, "checking_account": checking_account})
    else:
        logger.info("User %s has no permission to view external user %s's checking account" % (request.user.username, str(external_user_id)))
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
            logger.info("User %s tried to view credit card of non-existant external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
        logger.info("User %s is viewing external user %s's credit card" % (request.user.username, str(external_user.username)))
        credit_card = get_external_user_account(user=external_user, account_type=CREDIT_CARD)
        return render(request, success_page, {"user": external_user, "credit_card": credit_card})
    else:
        logger.info("User %s has no permission to view external user %s's credit card" % (request.user.username, str(external_user_id)))
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
            logger.info("User %s tried to view profile of non-existant external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
        profile = get_any_user_profile(username=external_user.username)
        if is_administrator(user):
            admin_privilege = True
        logger.info("User %s is viewing external user %s's profile" % (request.user.username, str(external_user.username)))
        return render(request, success_page, {"user": external_user, "profile": profile, 'admin_privilege': admin_privilege})
    else:
        logger.info("User %s has no permission to view external user %s's profile" % (request.user.username, str(external_user_id)))
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
            logger.info("User %s tried to view savings account of non-existant external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
        savings_account = get_external_user_account(user=external_user, account_type=ACCOUNT_TYPE_SAVINGS)
        logger.info("User %s is viewing external user %s's savings account" % (request.user.username, str(external_user.username)))
        return render(request, success_page, {"user": external_user, "savings account": savings_account})
    else:
        logger.info("User %s has no permission to view external user %s's savings account" % (request.user.username, str(external_user_id)))
        return HttpResponseRedirect(reverse(error_redirect))

# Internal Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_internal_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/internal_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view internal log " % (request.user.username))
        return HttpResponseRedirect(reverse('internal:error'))

# Login Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_login_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/login_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view login log " % (request.user.username))
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
        logger.info("User %s tried to view profile of non-existant internal user %s" % (request.user.username, str(internal_user_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    profile = get_any_user_profile(username=internal_user.username)
    logger.info("User %s is viewing internal user %s's profile" % (request.user.username, str(internal_user.username)))
    return render(request, success_page, {"user": internal_user, "profile": profile})

# Reset Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_reset_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/reset_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view reset log " % (request.user.username))
        return HttpResponseRedirect(reverse('internal:error'))

# Server Log Page
@never_cache
@login_required
@user_passes_test(is_administrator)
def view_server_log(request):
    try:
        file_name= os.path.join(BASE_DIR,'log/server_log.log')
        f = open(file_name, 'r')
        lines = f.readlines()
        f.close()
        if not lines:
            lines = ['Nothing to View']
        return render_to_pdf_response(request, 'internal/log.html', context={'content': lines}, filename=None, encoding=u'utf-8')
    except:
        logger.info("User %s encountered an error when trying to view server log " % (request.user.username))
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
            logger.info("User %s tried to charge late charges, but the card were already charged this month" % (request.user.username))
            return render(request, 'internal/monthly_cron.html', {'message': "Unsuccessfully charged any late cards. Can only update charges once on a month."})
        late_credit_card = CreditCard.objects.filter(remaining_credit__lt = 1000)
        for card in late_credit_card:
            card.days_late = card.days_late + 1
            fee = CREDIT_CARD_INTEREST_RATE * card.days_late
            card.late_fee = min(1000.00, fee)
            card.save()
        logger.info("User %s successfully charged any late cards this month" % (request.user.username))
        return render(request, 'internal/monthly_cron.html', {'message': "Successfully charged any late cards this month."})
    else:
        logger.info("User %s tried to charge late cards, but cards can only be charged on the first of each month " % (request.user.username))
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
            logger.info("User %s tried to update late charges, but charges were already updated today" % (request.user.username))
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
        logger.info("User %s successfully updated late charges" % (request.user.username))
        return render(request, 'internal/monthly_cron.html', {'message': "Updated late charges today."})
    else:
        logger.info("User %s tried to update late charges, but this can only occur once a day between 23:00 and 23:59" % (request.user.username))
        return render(request, 'internal/monthly_cron.html', {'message': "Did not update late charges. Can only update charges between 23:00 and 23:59."})

# Clear Create Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_create_log(request):
    user = request.user
    log_name = 'create'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

# Clear External Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_external_log(request):
    user = request.user
    log_name = 'external'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

# Clear Internal Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_internal_log(request):
    user = request.user
    log_name = 'internal'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

# Clear Login Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_login_log(request):
    user = request.user
    log_name = 'login'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

# Clear Login Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_reset_log(request):
    user = request.user
    log_name = 'reset'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

# Clear Server Log
@never_cache
@login_required
@user_passes_test(is_administrator)
def validate_clear_server_log(request):
    user = request.user
    log_name = 'server'
    success_redirect = 'internal:view_' + log_name + '_log'
    error_redirect = 'internal:error'
    file_name = os.path.join(BASE_DIR,'log/' + log_name + '_log.log')
    f = open(file_name, 'w')
    f.write('')
    f.close()
    return HttpResponseRedirect(reverse(success_redirect))

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
        logger.info("User %s tried to approve a non-existant external critical transaction %s" % (request.user.username, str(transaction_id)))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if commit_transaction(transaction=top_critical_transaction, user=user):
        logger.info("Critical transaction %s of type %s and description %s was approved by internal user %s " % (str(top_critical_transaction.id), str(top_critical_transaction.type_of_transaction), str(top_critical_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        logger.info("Critical transaction %s of type %s and description %s failed to be approved by internal user %s " % (str(top_critical_transaction.id), str(top_critical_transaction.type_of_transaction), str(top_critical_transaction.description), request.user.username))
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
        logger.info("User %s tried to deny a non-existant external critical transaction %s" % (request.user.username, str(transaction_id)))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalCriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if deny_transaction(transaction=top_critical_transaction, user=user):
        logger.info("Critical transaction %s of type %s and description %s was denied by internal user %s " % (str(top_critical_transaction.id), str(top_critical_transaction.type_of_transaction), str(top_critical_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        logger.info("Critical transaction %s of type %s and description %s failed to be denied by internal user %s " % (str(top_critical_transaction.id), str(top_critical_transaction.type_of_transaction), str(top_critical_transaction.description), request.user.username))
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
                logger.info("User %s deactivated external user %s" % (request.user.username, external_user.username))
                return HttpResponseRedirect(reverse(success_page))
            else:
                logger.info("User %s cannot deactivate external user %s" % (request.user.username, str(external_user_id)))
                return HttpResponseRedirect(reverse(error_redirect))
        except:
            logger.info("Error occurred when user %s tried to deactivate external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        logger.info("User %s has no permission to deactivate external user %s" % (request.user.username, str(external_user_id)))
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
                logger.info("User %s reactivated external user %s" % (request.user.username, external_user.username))
                return HttpResponseRedirect(reverse(success_page))
            else:
                logger.info("User %s cannot reactivate external user %s" % (request.user.username, str(external_user_id)))
                return HttpResponseRedirect(reverse(error_redirect))
        except:
            logger.info("Error occurred when user %s tried to reactivate external user %s" % (request.user.username, str(external_user_id)))
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        logger.info("User %s has no permission to reactivate external user %s" % (request.user.username, str(external_user_id)))
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
            logger.info("User %s deactivated internal user %s" % (request.user.username, internal_user.username))
            return HttpResponseRedirect(reverse('internal:index'))
        else:
            logger.info("User %s cannot deactivate internal user %s" % (request.user.username, str(internal_user_id)))
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        logger.info("Error occurred when user %s tried to deactivate user %s" % (request.user.username, str(internal_user_id)))
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
            logger.info("User %s reactivated internal user %s" % (request.user.username, internal_user.username))
            return HttpResponseRedirect(reverse('internal:index'))
        else:
            logger.info("User %s cannot reactivate internal user %s" % (request.user.username, str(internal_user_id)))
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        logger.info("Error occurred when user %s tried to reactivate user %s" % (request.user.username, str(internal_user_id)))
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
            logger.info("Critical transaction %s of type %s and description %s was deleted by internal user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return HttpResponseRedirect(reverse('internal:critical_transactions'))
        else:
            logger.info("Critical transaction %s of type %s and description %s failed to be deleted by user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        logger.info("Error occurred when critical transaction %s was trying to be deleted by internal user %s " % (str(transaction_id), request.user.username))
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
            logger.info("Noncritical transaction %s of type %s and description %s was deleted by internal user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return HttpResponseRedirect(reverse('internal:noncritical_transactions'))
        else:
            logger.info("Noncritical transaction %s of type %s and description %s failed to be deleted by user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return HttpResponseRedirect(reverse('internal:error'))
    except:
        logger.info("Error occurred when noncritical transaction %s was trying to be deleted by internal user %s " % (str(transaction_id), request.user.username))
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
        logger.info("Error occurred when internal %s tried to approve external noncritical transaction %s" % (request.user.username, str(transaction_id)))
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
        logger.info("Internal transaction %s of type %s and description %s for request to approve noncritical transaction %s was approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), str(external_transaction.id), request.user.username))
        return HttpResponseRedirect(reverse('internal:internal_noncritical_transactions'))
    else:
        logger.info("Internal transaction %s of type %s and description %s for request to approve noncritical transaction %s failed to be approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), str(external_transaction.id), request.user.username))
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
            logger.info("External transaction %s of type %s and description %s was denied by internal user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return HttpResponseRedirect(reverse('internal:internal_noncritical_transactions'))
        else:
            logger.info("External transaction %s of type %s and description %s failed to be denied by internal user %s " % (str(transaction.id), str(transaction.type_of_transaction), str(transaction.description), request.user.username))
            return render(request, 'internal/internal_noncritical_transactions.html', {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'error_message': 'Denied transaction not committed'})
    except:
        logger.info("Error occurred when transactino %s was being approved by internal user %s " % (str(transaction_id),request.user.username))
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
        logger.info("Admin %s attempted to edit an external user's profile"%(request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    elif (page_to_view == PAGE_TO_VIEW_DEACTIVATE or page_to_view == PAGE_TO_VIEW_REACTIVATE) and is_administrator(user):
        logger.info("Admin %s attempted to deactivate or recactivate an external user's profile"%(request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))
    else:
        success_redirect = "internal:view_external_user_" + page_to_view
    pending_approval_redirect = "internal:index"
    try:
        external_user = User.objects.get(id=int(external_user_id))
        if not is_external_user(external_user):
            raise Exception
    except:
        logger.info("User %s tried to access data of non-existant external user %s" % (request.user.username, str(external_user_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    access_granted = does_user_have_external_user_permission(user=user, external_user=external_user, page_to_view=page_to_view)
    if access_granted:
        logger.info("User %s has access to %s's %s" % (request.user.username, str(external_user.username), str(page_to_view)))
        return HttpResponseRedirect(reverse(success_redirect, kwargs={'external_user_id': external_user.id}))
    elif is_regular_employee(user) and not access_granted:
        accessRequestObject = accessRequests.objects.create(internalUserId=user.id, externalUserId=external_user_id , pageToView=page_to_view)
        accessRequestObject.save()
        logger.info("User %s is requesting approval to access %s's %s" % (request.user.username, str(external_user.username), str(page_to_view)))
        return HttpResponseRedirect(reverse(pending_approval_redirect))
    else:
        logger.info("User %s has no access to %s's %s" % (request.user.username, str(external_user.username), str(page_to_view)))
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
        logger.info("Internal user %s tried to approve non-existant critical internal transaction %s" % (request.user.username, str(transaction_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    if is_regular_employee(initiator):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    else:
        logger.info("Internal user %s tried to approve critical internal transaction not made by an internal user %s" % (request.user.username, str(transaction_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    if commit_transaction(transaction=internal_transaction, user=user):
        logger.info("Internal critical transaction %s of type %s and description %s was approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        logger.info("Internal critical transaction %s of type %s and description %s failed to be approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(error_redirect))

# Validate Internal Critical Transactions Request
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
        logger.info("Internal user %s tried to deny non-existant critical internal transaction %s" % (request.user.username, str(transaction_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    if is_regular_employee(initiator):
        content_type = ContentType.objects.get_for_model(RegularEmployee)
    else:
        logger.info("Internal user %s tried to deny critical internal transaction not made by an internal user %s" % (request.user.username, str(transaction_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    if deny_transaction(transaction=internal_transaction, user=user):
        logger.info("Internal critical transaction %s of type %s and description %s was approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        logger.info("Internal critical transaction %s of type %s and description %s failed to be approved by internal user %s " % (str(internal_transaction.id), str(internal_transaction.type_of_transaction), str(internal_transaction.description), request.user.username))
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
            for transaction in already_exists:
                data = parse_transaction_description(transaction_description=transaction.description, type_of_transaction=transaction.type_of_transaction)
                if data['external_transaction'].id == external_transaction.id:
                    raise Exception
    except:
        logger.info("Internal user %s tried to request for access to request access to resolve non-existant noncritical transaction %s" % (request.user.username, str(transaction_id)))
        return HttpResponseRedirect(reverse('internal:index'))
    if create_internal_noncritical_transaction(user=user, external_transaction=external_transaction):
        logger.info("External noncritical transaction %s of type %s and description %s was requested to be resolved by regular employee %s " % (str(external_transaction.id), str(external_transaction.type_of_transaction), str(external_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse('internal:noncritical_transactions'))
    else:
        logger.info("External noncritical transaction %s of type %s and description %s failed to be requested to be resolved regular employee %s " % (str(external_transaction.id), str(external_transaction.type_of_transaction), str(external_transaction.description), request.user.username))
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
        logger.info("User %s successfully edited internal user %s's profile"%(request.user.username, str(internal_user_id)))
        return HttpResponseRedirect(reverse(success_redirect))
    else:
        logger.info("User %s entered invalid values for modification of internal user %s's profile"%(request.user.username, str(internal_user_id)))
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
        logger.info("User %s tried to validate accesss request by non existant internal user %s "%(request.user.username, str(internal_user_id)))
        return HttpResponseRedirect(reverse(error_redirect))
    logger.info("User %s validated accesss request to %s for internal user %s "%(request.user.username, str(page_to_view), str(internal_user_id)))
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
        logger.info("User %s tried to approve a non-existant external noncritical transaction %s" % (request.user.username, str(transaction_id)))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        logger.info("Noncritical transaction %s of type %s and description %s cannot be approved by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if commit_transaction(transaction=top_noncritical_transaction, user=user):
        logger.info("Noncritical transaction %s of type %s and description %s was approved by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        logger.info("Noncritical transaction %s of type %s and description %s failed to be approved by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
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
        logger.info("User %s tried to deny a non-existant external noncritical transaction %s" % (request.user.username, str(transaction_id)))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Transaction does not exist"})
    transactions = ExternalNoncriticalTransaction.objects.filter().exclude(status=TRANSACTION_STATUS_RESOLVED).order_by('time_created')
    if not can_resolve_noncritical_transaction(user, transaction_id):
        logger.info("Noncritical transaction %s of type %s and description %s cannot be denied by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
        return render(request, success_page, {'user_type': list[2], 'first_name': list[0],'last_name':list[1],'transactions': transactions, 'error_message': "Do not have permission to resolve transaction"})
    if deny_transaction(transaction=top_noncritical_transaction, user=user):
        logger.info("Noncritical transaction %s of type %s and description %s was denied by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
        return HttpResponseRedirect(reverse(success_page_reverse))
    else:
        logger.info("Noncritical transaction %s of type %s and description %s failed to be denied by internal user %s " % (str(top_noncritical_transaction.id), str(top_noncritical_transaction.type_of_transaction), str(top_noncritical_transaction.description), request.user.username))
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
    last_name = request.POST['last_name']
    """ This preserves PII privilege of editing profile
    street_address = request.POST['street_address']
    city = request.POST['city']
    state = request.POST['state']
    zipcode = request.POST['zipcode']
    """
    if is_system_manager(user):
        """ This preserves PII privilege of editing profile
        if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
        """
        if validate_first_name_save(profile=profile, first_name=first_name) and validate_last_name_save(profile=profile, last_name=last_name):
            logger.info("System manager %s edited external user %s's profile"%(request.user.username, username))
            return HttpResponseRedirect(reverse(success_redirect))
        else:
            logger.info("System manager %s provided invalid values for modification of external user %s's profile"%(request.user.username, username))
            return HttpResponseRedirect(reverse(error_redirect))
    elif is_regular_employee(user):
        try:
            permission_codename = 'can_internal_user_edit_external_user_profile_' + str(external_user_id)
            permission = Permission.objects.get(codename=permission_codename)
            permission_codename = 'internal.' + permission_codename
        except:
            logger.info("Regular Employee %s has database permission error when trying to edit external user %s's profile"%(request.user.username, username))
            return HttpResponseRedirect(reverse(error_redirect))
        if user.has_perm(permission_codename):
            """ This preserves PII privilege of editing profile
            if validate_profile_change(profile=profile, first_name=first_name, last_name=last_name, street_address=street_address, city=city, state=state, zipcode=zipcode):
            """
            if validate_first_name_save(profile=profile, first_name=first_name) and validate_last_name_save(profile=profile, last_name=last_name):
                user.user_permissions.remove(permission)
                user.save()
                logger.info("Regular Employee %s edited external user %s's profile"%(request.user.username, username))
                return HttpResponseRedirect(reverse(success_redirect))
            else:
                logger.info("Regular Employee %s provided invalid values for modification of external user %s's profile"%(request.user.username, username))
                return HttpResponseRedirect(reverse(error_redirect))
        else:
            logger.info("Regular Employee %s has no permission to edit external user %s's profile"%(request.user.username, username))
            return HttpResponseRedirect(reverse(error_redirect))
    else:
        logger.info("User %s has no permission to edit external user %s's profile"%(request.user.username, username))
        return HttpResponseRedirect(reverse(error_redirect))
