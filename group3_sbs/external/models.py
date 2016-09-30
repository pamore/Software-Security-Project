from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator
from django.db import models
from global_templates.models import Transaction
from login.models import UserProfile

# Create your models here.
class BankAccount(models.Model):
    interest_rate = models.DecimalField(validators=[MinValueValidator(0.00), MaxValueValidator(1.00)], max_digits=3, decimal_places=2)
    # Inner class to define meta attributes about class
    class Meta:
        # This class is abstract so no table will be created in database
        abstract = True

# Interface
class AccountFunctionality(models.Model):
    routing_number = models.IntegerField(unique=True)
    current_balance = models.DecimalField(validators=[MinValueValidator(0.00)], max_digits=9, decimal_places=2)
    active_balance = models.DecimalField(validators=[MinValueValidator(0.00)], max_digits=9, decimal_places=2)

    class Meta:
        abstract = True

class SavingsAccount(BankAccount, AccountFunctionality):
    pass

class CheckingAccount(BankAccount, AccountFunctionality):
    pass

class CreditCard(BankAccount):
    creditcard_number = models.CharField(validators=[MinLengthValidator(16)], max_length=16, unique=True)
    charge_limit = models.DecimalField(validators=[MinValueValidator(0.00), MaxValueValidator(1000.00)], max_digits=6, decimal_places=2)
    remaining_credit = models.DecimalField(validators=[MinValueValidator(0.00), MaxValueValidator(1000.00)], max_digits=6, decimal_places=2)
    late_fee = models.DecimalField(validators=[MinValueValidator(0.00), MaxValueValidator(15.00)], max_digits=5, decimal_places=2)
    days_late = models.IntegerField(validators=[MinValueValidator(0)])

class ExternalEmployee(UserProfile):
    # ForeignKey Relationships
    checking_account = models.OneToOneField(CheckingAccount, on_delete=models.CASCADE, blank=True, null=True)
    credit_card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, blank=True, null=True)
    savings_account = models.OneToOneField(SavingsAccount, on_delete=models.CASCADE, blank=True, null=True)

    # Inner class to define meta attributes about class
    class Meta:
        # This class is abstract so no table will be created in database
        abstract = True

class IndividualCustomer(ExternalEmployee):
     ssn = models.CharField(validators=[MinLengthValidator(2)], max_length=100, unique=True)

class MerchantOrganization(ExternalEmployee):
    business_code = models.CharField(validators=[MinLengthValidator(2)], max_length=100, unique=True)

class ExternalNoncriticalTransaction(Transaction):
    pass

class ExternalCriticalTransaction(Transaction):
    pass

class MerchantPaymentRequest(models.Model):
    merchantCheckingsAccountNum = models.IntegerField()
    accountType = models.CharField(max_length=30)
    clientAccountNum = models.IntegerField()
    clientRoutingNum = models.IntegerField()
    requestAmount = models.DecimalField(validators=[MinValueValidator(0.00), MaxValueValidator(1000.00)], max_digits=6, decimal_places=2)

