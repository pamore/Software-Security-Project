from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from global_templates.common_functions import *
from global_templates.constants import *
from django.test import TestCase, Client
from create.models import *
import create.views
from external.models import *
import external.views
from internal.models import *
import internal.views
from login.models import *
import login.views
from reset.models import *
import reset.views


""" Write Helper Functions Here """
def createIndividualCustomer(ID_NUMBER, ROUTE_NUMBER, CREDIT_CARD_NUMBER):
    user1 = User.objects.create_user(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER))
    checkingaccount1 = CheckingAccount.objects.create(interest_rate=0.03, routing_number=ROUTE_NUMBER, current_balance=0.00, active_balance=0.00)
    savingsaccount1 = SavingsAccount.objects.create(interest_rate=0.03, routing_number=ROUTE_NUMBER, current_balance=0.00, active_balance=0.00)
    creditcard1 = CreditCard.objects.create(interest_rate=0.03, creditcard_number=str(CREDIT_CARD_NUMBER).zfill(16), charge_limit=1000.00, remaining_credit=1000.00, late_fee=15.00, days_late=0)
    individualcustomer = IndividualCustomer.objects.create(first_name="user"+str(ID_NUMBER), last_name="user"+str(ID_NUMBER), email="user"+str(ID_NUMBER)+"@group3sbs.com", street_address="1234 Abbey Road", city="Liverpool", state="AZ", zipcode="12345", ssn=str(ID_NUMBER).zfill(9), session_key="None", checking_account_id=checkingaccount1.id, savings_account_id=savingsaccount1.id, credit_card_id=creditcard1.id, user_id=user1.id)
    user1.save()
    creditcard1.save()
    savingsaccount1.save()
    checkingaccount1.save()
    individualcustomer.save()
    ID_NUMBER = ID_NUMBER + 1
    ROUTE_NUMBER = ROUTE_NUMBER + 1
    CREDIT_CARD_NUMBER = CREDIT_CARD_NUMBER + 1
    return user1

def createMerchantOrganization(ID_NUMBER, ROUTE_NUMBER, CREDIT_CARD_NUMBER):
    user1 = User.objects.create_user(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER))
    checkingaccount1 = CheckingAccount.objects.create(interest_rate=0.03, routing_number=ROUTE_NUMBER, current_balance=0.00, active_balance=0.00)
    savingsaccount1 = SavingsAccount.objects.create(interest_rate=0.03, routing_number=ROUTE_NUMBER, current_balance=0.00, active_balance=0.00)
    creditcard1 = CreditCard.objects.create(interest_rate=0.03, creditcard_number=str(CREDIT_CARD_NUMBER).zfill(16), charge_limit=1000.00, remaining_credit=1000.00, late_fee=15.00, days_late=0)
    merchantorganization = MerchantOrganization.objects.create(first_name="user"+str(ID_NUMBER), last_name="user"+str(ID_NUMBER), email="user"+str(ID_NUMBER)+"@group3sbs.com", street_address="1234 Abbey Road", city="Liverpool", state="AZ", zipcode="12345", business_code=str(ID_NUMBER).zfill(9), session_key="None", checking_account_id=checkingaccount1.id, savings_account_id=savingsaccount1.id, credit_card_id=creditcard1.id, user_id=user1.id)
    user1.save()
    creditcard1.save()
    savingsaccount1.save()
    checkingaccount1.save()
    merchantorganization.save()
    ID_NUMBER = ID_NUMBER + 1
    ROUTE_NUMBER = ROUTE_NUMBER + 1
    CREDIT_CARD_NUMBER = CREDIT_CARD_NUMBER + 1
    return user1

""" Write Test Case Modules (Classes) Here """

# Test Case Class for Checking Account Operations
class CheckingTest(TestCase):

    """ Write Test Cases Here. Must start with keyword test """
    # Test to see if the credit page is rendered
    def test_show_checking_credit_page(self):
        ID_NUMBER = 1

        # Populate test database
        user = createIndividualCustomer(ID_NUMBER=ID_NUMBER, ROUTE_NUMBER=ID_NUMBER, CREDIT_CARD_NUMBER=ID_NUMBER)

        # Create a sample client
        client = Client()

        # Login as a user
        self.assertEqual(client.login(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER)), True)

        # Perform a GET, POST, PUT, DELETE, or HEAD HTTP request
        response = client.get(path='/external/account/credit/checking/')

        self.assertEqual(response.resolver_match.func, external.views.credit_checking)

    # Test to see if the credit checking account works
    def test_validate_checking_credit(self):
        ID_NUMBER = 2
        amount = 100.00

        # Populate test database
        user = createIndividualCustomer(ID_NUMBER=ID_NUMBER, ROUTE_NUMBER=ID_NUMBER, CREDIT_CARD_NUMBER=ID_NUMBER)

        # Create a sample client
        client = Client()

        # Login as a user
        self.assertEqual(client.login(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER)), True)

        # Make very post request value such as amount
        data = {
            'amount' : amount,
        }
        # Perform a GET, POST, PUT, DELETE, or HEAD HTTP request
        response = client.post(path='/external/account/credit/checking/', data=data)

        self.assertEqual(response.resolver_match.func, external.views.credit_checking)

        # Refresh the user object
        user = User.objects.get(username="iamuser"+str(ID_NUMBER))
        checking_account = user.individualcustomer.checking_account

        # Check if the active balance was correctly updated
        self.assertEqual(float(checking_account.active_balance), amount)

    # Test to see if incorrect page is rendered
    def test_show_redirect_page(self):
        ID_NUMBER = 3

        # Populate test database
        user = createIndividualCustomer(ID_NUMBER=ID_NUMBER, ROUTE_NUMBER=ID_NUMBER, CREDIT_CARD_NUMBER=ID_NUMBER)

        # Create a sample client
        client = Client()

        # Login as a user
        self.assertEqual(client.login(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER)), True)

        # Perform a GET, POST, PUT, DELETE, or HEAD HTTP request
        response = client.get(path='/external/account/debit/checking/fsdafasfafs/')

        self.assertRedirects(response, '/loggedin/')

    # Test to see if the debit page is rendered
    def test_show_checking_debit_page(self):
        ID_NUMBER = 4

        # Populate test database
        user = createIndividualCustomer(ID_NUMBER=ID_NUMBER, ROUTE_NUMBER=ID_NUMBER, CREDIT_CARD_NUMBER=ID_NUMBER)

        # Create a sample client
        client = Client()

        # Login as a user
        self.assertEqual(client.login(username="iamuser"+str(ID_NUMBER), password="Iamthepassword!"+str(ID_NUMBER)), True)

        # Perform a GET, POST, PUT, DELETE, or HEAD HTTP request
        response = client.get(path='/external/account/debit/checking/')

        self.assertEqual(response.resolver_match.func, external.views.debit_checking)
