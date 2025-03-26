import hashlib
import hmac
import json
import os
import random
import string
import json
import requests

from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from rest_framework import permissions, status



from .models import Transactions
from .serializers import TransactionsSerializer

from user.models import UserAccount
from user.serializers import UserSerializer

class SaveTransactionView(APIView):
    
    def post(self, request, format=None):
        data = request.data
        amount = int(data['amount'])
        transaction_type = data['transaction_type']
        number = data['number']
        status = data['status']
        user = request.user

        transaction = Transactions.objects.create(user=user, transaction_type=transaction_type, amount=amount, number=number, status=status)

        if transaction_type == 'Fund Wallet':
            user.wallet += amount
            user.save()

            transaction.is_successful = True
            transaction.save()
            user_serializer = UserSerializer(user)
            transaction_serialiser = TransactionsSerializer(transaction)
            response_data = {'transaction':transaction_serialiser.data,'wallet_balance':user.wallet}
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            if user.wallet >= amount:
                #make call to get service the customer wants

                #if call is successful
                user.wallet -= amount
                user.save()

                transaction.is_successful = True
                transaction.status = "success"
                transaction.save()
                transaction_serialiser = TransactionsSerializer(transaction)
                response_data = {'transaction':transaction_serialiser.data,'wallet_balance':user.wallet}
                return Response(response_data)
                #if the call is not successful
            else:
                transaction.is_successful = False
                transaction.status = "failed"
                transaction.save()
                transaction_serialiser = TransactionsSerializer(transaction)
                response_data = {'transaction':transaction_serialiser.data,'wallet_balance':user.wallet}
                return Response(response_data)

class InitializePaystackPayment(APIView):
    def post(self, request):
        # print(request.data)
        amount = request.data['amount']
        email = request.data['email']
        user = request.user

        transaction = Transactions.objects.create(user=user, transaction_type='Fund Wallet', amount=amount, status='pending')
        transaction_serialiser = TransactionsSerializer(transaction)
        

        paystack_secret_key = os.environ.get('PAYSTACK_TEST_SECRET') 

        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'email': email,
            'amount': int(amount)*100,
            'metadata': {
                'transaction_id': transaction.id
            }
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))
        

        response_data = response.json()
        
        print(response_data)
        return Response(response_data, status=status.HTTP_200_OK)
#Webhooks
@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhook(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        headers = request.headers
        data = request.data

        secret = os.environ.get('PAYSTACK_TEST_SECRET')
        if not secret:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            data_string = json.dumps(request.data)
            body = json.loads(data_string)
            body_unicode = json.dumps(body, separators=(',', ':'))
            computed_hash = hmac.new(
                secret.encode('utf-8'),
                msg=body_unicode.encode('utf-8'),
                digestmod=hashlib.sha512
            ).hexdigest()

            paystack_hash = request.headers.get('x-paystack-signature')
            

            if computed_hash == paystack_hash:
                # Process the event
                event = body
                print(event)
                # Do something with the event (e.g., update database, trigger tasks)
                # Example:
                if event.get('event') == 'charge.success':
                    transaction = Transactions.objects.get(id=event.get('data').get('metadata').get('transaction_id'))
                    transaction.is_successful = True
                    transaction.status = "success"
                    transaction.save()

                    user = transaction.user
                    user.wallet += transaction.amount
                    user.save()
           
                return Response(status=status.HTTP_200_OK)

            else:
                return Response("Invalid signature", status=status.HTTP_400_BAD_REQUEST)

        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
            return Response(f"Invalid request: {e}", status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     return Response(f"An unexpected error occurred: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        
            
