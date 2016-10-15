from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator
from django.db import models
from global_templates.models import Transaction
from login.models import UserProfile

# Create your models here.
class InternalEmployee(UserProfile):
    # Inner class to define meta attributes about class
    class Meta:
        # This class is abstract so no table will be created in database
        abstract = True

class RegularEmployee(InternalEmployee):
    pass

class SystemManager(InternalEmployee):
    pass

class Administrator(InternalEmployee):
    pass

class InternalNoncriticalTransaction(Transaction):
    pass

class InternalCriticalTransaction(Transaction):
    pass

class TransactionLog(models.Model):
    external_critical_transaction = models.ManyToManyField('external.ExternalCriticalTransaction')
    external_noncritical_transaction = models.ManyToManyField('external.ExternalNoncriticalTransaction')
    internal_critical_transaction = models.ManyToManyField(InternalCriticalTransaction)
    internal_noncritical_transaction = models.ManyToManyField(InternalNoncriticalTransaction)

class CreditPaymentManager(models.Model):
    last_day_late_fee_date_executed = models.DateTimeField()
    last_month_late_fee_date_executed = models.DateTimeField()
