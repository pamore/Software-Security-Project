from global_templates.constants import TRANSACTION_TYPE_CREDIT, TRANSACTION_TYPE_DEBIT, TRANSACTION_TYPE_PAYMENT, TRANSACTION_TYPE_TRANSFER

# Transaction Description Strings

def credit_or_debit_description_helper(transactionType, userType, userID, accountType, accountID, routingID, amount, starting_balance, ending_balance):
    userID = str(userID)
    accountID = str(accountID)
    routingID = str(routingID)
    amount = str(amount)
    starting_balance = str(starting_balance)
    ending_balance = str(ending_balance)
    return 'Transaction Type: {0},User Type: {1},User ID: {2},Account Type: {3},Account ID: {4},Routing ID: {5},Amount: {6},Starting Balance: {7},Ending Balance: {8}'.format(unicode(transactionType,'utf-8'), unicode(userType,'utf-8'), unicode(userID,'utf-8'), unicode(accountType,'utf-8'), unicode(accountID,'utf-8'), unicode(routingID,'utf-8'), unicode(amount,'utf-8'), unicode(starting_balance,'utf-8'), unicode(ending_balance,'utf-8'))

def debit_description(userType, userID, accountType, accountID, routingID, amount, starting_balance, ending_balance):
    transactionType = TRANSACTION_TYPE_DEBIT
    return credit_or_debit_description_helper(transactionType=transactionType, userType=userType, userID=userID, accountType=accountType, accountID=accountID, routingID=routingID, amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)

def credit_description(userType, userID, accountType, accountID, routingID, amount, starting_balance, ending_balance):
    transactionType = TRANSACTION_TYPE_DEBIT
    return credit_or_debit_description_helper(transactionType=transactionType, userType=userType, userID=userID, accountType=accountType, accountID=accountID, routingID=routingID, amount=amount, starting_balance=starting_balance, ending_balance=ending_balance)

def transfer_or_payment_description_helper(transactionType, senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    transactionType = str(transactionType)
    senderID = str(senderID)
    senderType = str(senderType)
    senderAccountType = str(senderAccountType)
    senderAccountID = str(senderAccountID)
    senderRoutingID = str(senderRoutingID)
    receiverID = str(receiverID)
    receiverType = str(receiverType)
    receiverAccountType = str(receiverAccountType)
    receiverAccountID = str(receiverAccountID)
    receiverRoutingID = str(receiverRoutingID)
    amount = str(amount)
    sender_starting_balance = str(sender_starting_balance)
    sender_ending_balance = str(sender_ending_balance)
    receiver_starting_balance = str(receiver_starting_balance)
    receiver_ending_balance = str(receiver_ending_balance)
    return 'Transaction Type: {0},Sender Type: {1},Sender ID: {2},Sender Account Type: {3},Sender Account ID: {4},Sender Routing ID: {5},Receiver Type: {6},Receiver ID: {7},Receiver Account Type: {8},Receiver Account ID: {9},Receiver Routing ID: {10},Amount: {11},Sender Starting Balance: {12},Sender Ending Balance: {13},Receiver Starting Balance: {14},Receiver Ending Balance: {15}'.format(unicode(transactionType,'utf-8'), unicode(senderType,'utf-8'), unicode(senderID,'utf-8'), unicode(senderAccountType,'utf-8'), unicode(senderAccountID,'utf-8'), unicode(senderRoutingID,'utf-8'), unicode(receiverType,'utf-8'), unicode(receiverID,'utf-8'), unicode(receiverAccountType,'utf-8'), unicode(receiverAccountID,'utf-8'), unicode(receiverRoutingID,'utf-8'), unicode(amount,'utf-8'), unicode(sender_starting_balance,'utf-8'), unicode(sender_ending_balance,'utf-8'),unicode(receiver_starting_balance,'utf-8'), unicode(receiver_ending_balance,'utf-8'))

def payment_description(senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    transactionType = TRANSACTION_TYPE_PAYMENT
    return transfer_or_payment_description_helper(transactionType=transactionType, senderType=senderType, senderID=senderID, senderAccountType=senderAccountType, senderAccountID=senderAccountID, senderRoutingID=senderRoutingID, receiverType=receiverType, receiverID=receiverID, receiverAccountType=receiverAccountType, receiverAccountID=receiverAccountID, receiverRoutingID=receiverRoutingID, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_ending_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_ending_balance)


def transfer_description(senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount, sender_starting_balance, sender_ending_balance, receiver_starting_balance, receiver_ending_balance):
    transactionType = TRANSACTION_TYPE_TRANSFER
    return transfer_or_payment_description_helper(transactionType=transactionType, senderType=senderType, senderID=senderID, senderAccountType=senderAccountType, senderAccountID=senderAccountID, senderRoutingID=senderRoutingID, receiverType=receiverType, receiverID=receiverID, receiverAccountType=receiverAccountType, receiverAccountID=receiverAccountID, receiverRoutingID=receiverRoutingID, amount=amount, sender_starting_balance=sender_starting_balance, sender_ending_balance=sender_ending_balance, receiver_starting_balance=receiver_starting_balance, receiver_ending_balance=receiver_ending_balance)

def payment_on_behalf_description():
    return ""

def credit_card_payment_description():
    return ""

def credit_card_charge_description():
    return ""

def credit_card_late_fee_description():
    return ""

def modify_account_description():
    return ""
