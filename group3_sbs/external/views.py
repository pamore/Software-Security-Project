from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
MAX_BALANCE = 9999999.99
MIN_BALANCE = 0.00

# External User Home Page
@login_required
def index(request):
    user = request.user
    if hasattr(user, 'individualcustomer'):
        if (not hasattr(user.individualcustomer, 'checking_account')) and (not hasattr(user.individualcustomer, 'savings_account')) and (not hasattr(user.individualcustomer, 'credit_card')):
            return render(request, 'external/error.html')
        else:
            return render(request, 'external/index.html', {'user_type': "Individual Customer", 'first_name': user.individualcustomer.first_name, 'last_name': user.individualcustomer.last_name, 'checkingaccount': user.individualcustomer.checking_account, 'savingsaccount': user.individualcustomer.savings_account, 'creditcard': user.individualcustomer.credit_card})
    elif hasattr(user, 'merchantorganization'):
        if (not hasattr(user.merchantorganization, 'checking_account')) and (not hasattr(user.merchantorganization, 'savings_account')) and (not hasattr(user.merchantorganization, 'credit_card')):
            return render(request, 'external/error.html')
        else:
            return render(request, 'external/index.html', {'user_type': "Merchant / Organization", 'first_name': user.merchantorganization.first_name, 'last_name': user.merchantorganization.last_name, 'checkingaccount': user.merchantorganization.checking_account, 'savingsaccount': user.merchantorganization.savings_account, 'creditcard': user.merchantorganization.credit_card})
    else:
        return render(request, 'external/error.html')

# Checking Account Page
@login_required
def checking_account(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        return render(request, 'external/checking_account.html', {'checking_account': user.individualcustomer.checking_account})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        return render(request, 'external/checking_account.html', {'checking_account': user.merchantorganization.checking_account})
    else:
        return render(request, 'external/error.html')

# Savings Account Page
@login_required
def savings_account(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        return render(request, 'external/savings_account.html', {'savings_account': user.individualcustomer.savings_account})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        return render(request, 'external/savings_account.html', {'savings_account': user.merchantorganization.savings_account})
    else:
        return render(request, 'external/error.html')

# Credit Card Page
@login_required
def credit_card(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'credit_card'):
        return render(request, 'external/credit_card.html', {'credt_card': user.individualcustomer.credit_card})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'credit_card'):
        return render(request, 'external/credit_card.html', {'credt_card': user.merchantorganization.credit_card})
    else:
        return render(request, 'external/error.html')

# Credit Checking Page
@login_required
def credit_checking(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        return render(request, 'external/credit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Debit Checking Page
@login_required
def debit_checking(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        return render(request, 'external/debit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        return render(request, 'external/debit.html', {'checking_account': user.merchantorganization.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Credit Savings Page
@login_required
def credit_savings(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        return render(request, 'external/credit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Debit Savings Page
@login_required
def debit_savings(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        return render(request, 'external/debit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        return render(request, 'external/debit.html', {'savings_account': user.merchantorganization.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Validate Credit Checking Transaction
@login_required
def credit_checking_validate(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        new_balance = float(user.individualcustomer.checking_account.active_balance) + float(request.POST['credit_amount'])
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        new_balance = float(user.merchantorganization.checking_account.active_balance) + float(request.POST['credit_amount'])
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Validate Debit Checking Transaction
@login_required
def debit_checking_validate(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'checking_account'):
        new_balance = float(user.individualcustomer.checking_account.active_balance) - float(request.POST['debit_amount'])
        if new_balance >= MIN_BALANCE:
            user.individualcustomer.checking_account.active_balance = new_balance
            user.individualcustomer.checking_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'checking_account'):
        new_balance = float(user.merchantorganization.checking_account.active_balance) - float(request.POST['debit_amount'])
        if new_balance >= MIN_BALANCE:
            user.merchantorganization.checking_account.active_balance = new_balance
            user.merchantorganization.checking_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'checking_account': user.individualcustomer.checking_account, "account_type": "Checking"})
    else:
        return render(request, 'external/error.html')

# Validate Credit Savings Transaction
@login_required
def credit_savings_validate(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        new_balance = float(user.individualcustomer.savings_account.active_balance) + float(request.POST['credit_amount'])
        if new_balance <= MAX_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        new_balance = float(user.merchantorganization.savings_account.active_balance) + float(request.POST['credit_amount'])
        if new_balance <= MAX_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')

# Validate Debit Savings Transaction
@login_required
def debit_savings_validate(request):
    user = request.user
    if hasattr(user, 'individualcustomer') and hasattr(user.individualcustomer, 'savings_account'):
        new_balance = float(user.individualcustomer.savings_account.active_balance) - float(request.POST['debit_amount'])
        if new_balance >= MIN_BALANCE:
            user.individualcustomer.savings_account.active_balance = new_balance
            user.individualcustomer.savings_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    elif hasattr(user, 'merchantorganization') and hasattr(user.merchantorganization, 'savings_account'):
        new_balance = float(user.merchantorganization.savings_account.active_balance) - float(request.POST['debit_amount'])
        if new_balance >= MIN_BALANCE:
            user.merchantorganization.savings_account.active_balance = new_balance
            user.merchantorganization.savings_account.save()

            # To do: Create Transaction

            return HttpResponseRedirect(reverse('external:index'))
        else:
            return render(request, 'external/credit.html', {'savings_account': user.individualcustomer.savings_account, "account_type": "Savings"})
    else:
        return render(request, 'external/error.html')
