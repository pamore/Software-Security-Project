from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Transaction(models.Model):

    # Attributes
    status = models.CharField(max_length=200)
    time_created = models.DateTimeField(auto_now_add=True)
    type_of_transaction = models.CharField(max_length=200)
    time_resolved = models.DateTimeField(auto_now_add=True)

    # ForeignKey Relationships
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_initiator')
    participants = models.ManyToManyField(User, related_name='%(class)s_participants')
    resolver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_resolver')

    # Inner class to define meta attributes about class
    class Meta:
        # This class is abstract so no table will be created in database
        abstract = True


# To Do
class CertificateAuthority():
    pass

# To Do
class PreviousPassword():
    previous_password = models.CharField(max_length=200)
    associated_user = models.ForeignKey(User, on_delete=models.CASCADE)
