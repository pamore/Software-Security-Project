# Transaction Description Strings

def debit_description(userType, userID, accountType, accountID, routingID, amount):
    return 'Transaction Type: debit,User Type: {0},User ID: {1},Account Type: {2},Account ID: {3},Routing ID:{4},Amount:{5}'.format(unicode(userType,'utf-8'), unicode(userID,'utf-8'), unicode(accountType,'utf-8'), unicode(accountID,'utf-8'), unicode(routingID,'utf-8')))

def credit_description(userType, userID, accountType, accountID, routingID, amount):
    return 'Transaction Type: credit,User Type: {0},User ID: {1},Account Type: {2},Account ID: {3},Routing ID:{4},Amount:{5}'.format(unicode(userType,'utf-8'), unicode(userID,'utf-8'), unicode(accountType,'utf-8'), unicode(accountID,'utf-8'), unicode(routingID,'utf-8'), unicode(amount,'utf-8')))

def transfer_description(senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount):
    return 'Transaction Type: transfer,Sender Type: {0},Sender ID: {1},Transaction Type: transfer,Sender Account Type: {2},Sender Account ID: {3},Sender Routing ID:{4},Receiver Type: {5},Receiver ID: {6},Receiver Account Type: {7},Receiver Account ID: {8},Receiver Routing ID:{9},Amount: {10}'.format(unicode(senderType,'utf-8'), unicode(str(senderID),'utf-8'), unicode(senderAccountType,'utf-8'), unicode(senderAccountID,'utf-8'), unicode(senderRoutingID,'utf-8'), unicode(receiverType,'utf-8'), unicode(receiverID,'utf-8'), unicode(receiverAccountType,'utf-8'), unicode(receiverAccountID,'utf-8'), unicode(receiverRoutingID,'utf-8'), unicode(amount,'utf-8')))

def payment_description(senderType, senderID, senderAccountType, senderAccountID, senderRoutingID, receiverType, receiverID, receiverAccountType, receiverAccountID, receiverRoutingID, amount):
    return 'Transaction Type: payment,Sender Type: {0},Sender ID: {1},Transaction Type: transfer,Sender Account Type: {2},Sender Account ID: {3},Sender Routing ID:{4},Receiver Type: {5},Receiver ID: {6},Receiver Account Type: {7},Receiver Account ID: {8},Receiver Routing ID:{9},Amount: {10}'.format(unicode(senderType,'utf-8'), unicode(str(senderID),'utf-8'), unicode(senderAccountType,'utf-8'), unicode(senderAccountID,'utf-8'), unicode(senderRoutingID,'utf-8'), unicode(receiverType,'utf-8'), unicode(receiverID,'utf-8'), unicode(receiverAccountType,'utf-8'), unicode(receiverAccountID,'utf-8'), unicode(receiverRoutingID,'utf-8'), unicode(amount,'utf-8')))

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

def any_description(transactionType, userType, userID, accountType, accountID, routingID, amount):
    return 'Transaction Type: {0},User Type: {1},User ID: {2},Account Type: {3},Account ID: {4},Routing ID:{5},Amount:{6}'.format(unicode(transactionType, 'utf-8'), unicode(userType,'utf-8'), unicode(userID,'utf-8'), unicode(accountType,'utf-8'), unicode(accountID,'utf-8'), unicode(routingID,'utf-8')))
