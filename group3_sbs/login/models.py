from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator
from django.db import models

# Create your models here.
class UserProfile(models.Model):
    # ForeignKey Relationships
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Attributes
    first_name = models.CharField(validators=[MinLengthValidator(2)], max_length=100)
    last_name = models.CharField(validators=[MinLengthValidator(2)], max_length=100)
    email = models.CharField(validators=[MinLengthValidator(3)], max_length=100, unique=True)
    street_address = models.CharField(validators=[MinLengthValidator(4)], max_length=100)
    city = models.CharField(validators=[MinLengthValidator(2)], max_length=100)
    state = models.CharField(validators=[MinLengthValidator(2)], max_length=2)
    zipcode = models.CharField(validators=[MinLengthValidator(5)], max_length=5)
    session_key = models.CharField(max_length=100)

    # Inner class to define meta attributes about class
    class Meta:
        # This class is abstract so no table will be created in database
        abstract = True
