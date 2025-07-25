import code
import hashlib
import hmac
import json
import os
import random
import string
import json
import requests
import datetime

from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from rest_framework import permissions, status


from .models import Transactions, PersonalAccount
from .serializers import PersonalAccountSerializer, TransactionsSerializer
from .transaction_utilites import monnify_encode_base64, monnify_base_url, compute_sha512, VTPassAPI

from user.models import UserAccount
from user.serializers import UserSerializer


class SaveTransactionView(APIView):

    def post(self, request, format=None):
        data = request.data
        amount = int(data['amount'])
        transaction_type = data['transaction_type']
        number = data['number']
        transaction_status = data['status']
        user = request.user

        transaction = Transactions.objects.create(
            user=user, transaction_type=transaction_type, amount=amount, number=number, status=transaction_status)

        if transaction_type == 'Fund Wallet':
            user.wallet += amount
            user.save()

            transaction.is_successful = True
            transaction.save()
            user_serializer = UserSerializer(user)
            transaction_serialiser = TransactionsSerializer(transaction)
            response_data = {
                'transaction': transaction_serialiser.data, 'wallet_balance': user.wallet}
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            try:
                transaction_pin = data['transaction_pin']
            except KeyError:
                return Response({"message": "Enter transaction pin"}, status=status.HTTP_400_BAD_REQUEST)
            encrypted_pin = compute_sha512(
                secret=settings.SECRET_KEY, data=transaction_pin)
            if encrypted_pin != user.transaction_pin:
                return Response(data={"message": "Incorrect transaction pin", "is_successful": False}, status=status.HTTP_400_BAD_REQUEST)
            if user.wallet >= amount:
                # make call to get service the customer wants
                vtpass_api = VTPassAPI(
                    api_key=os.environ.get('VTPASS_API_KEY'),
                    public_key=os.environ.get('VTPASS_PUBLIC_KEY'),
                    secret_key=os.environ.get('VTPASS_SECRET_KEY')
                )

                vt_response = vtpass_api.buy_service(
                    service_id=data['serviceID'],
                    amount=amount,
                    phone=data['number'],
                    variation_code=data.get('variation_code'),
                    biller_code=data.get('biller_code'),
                    type=data.get('type')
                )
                # print(vt_response)

                code = vt_response.get('code')

                description = vt_response.get('response_description')
                print(code, description)

                if code == '000' and description == 'TRANSACTION SUCCESSFUL':
                    # if call is successful
                    user.wallet -= amount
                    user.save()

                    transaction.is_successful = True
                    transaction.status = "success"
                    transaction.save()
                    transaction_serialiser = TransactionsSerializer(
                        transaction)
                    response_data = {
                        'transaction': transaction_serialiser.data, 'wallet_balance': user.wallet}
                    return Response(response_data, status=status.HTTP_200_OK)
                elif code == '000' and description == 'TRANSACTION PROCESSING - PENDING':
                    # if call is processing
                    print("pending transaction")
                    requery = vtpass_api.query_transaction(
                        request_id=vt_response.get('requestId')
                    )
                    print(requery)
                    # data = json.loads(requery)
                    # print(data["response_description"])
                    if requery["response_description"] == "TRANSACTION SUCCESSFUL":
                        user.wallet -= amount
                        user.save()
                        transaction.is_successful = True
                        transaction.status = "success"
                        transaction.save()
                        transaction_serialiser = TransactionsSerializer(
                            transaction)
                        response_data = {
                            'transaction': transaction_serialiser.data, 'wallet_balance': user.wallet}

                        return Response(response_data, status=status.HTTP_200_OK)
                    else:
                        transaction.is_successful = False
                        transaction.status = "processing"
                        transaction.save()
                        return Response(
                            {"message": "Transaction is still processing, please check back later"},
                            status=status.HTTP_202_ACCEPTED
                        )
                else:
                    # if call is not successful
                    pass

            else:
                transaction.is_successful = False
                transaction.status = "failed"
                transaction.save()
                transaction_serialiser = TransactionsSerializer(transaction)
                response_data = {
                    'transaction': transaction_serialiser.data, 'wallet_balance': user.wallet}
                return Response(response_data, status=status.HTTP_403_FORBIDDEN)


class InitializePaystackPayment(APIView):
    def post(self, request):
        amount = request.data['amount']
        email = request.data['email']
        user = request.user

        transaction = Transactions.objects.create(
            user=user, transaction_type='Fund Wallet', amount=amount, status='pending')
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

        try:
            response = requests.post(
                'https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))

            response_data = response.json()

            return Response(response_data, status=status.HTTP_200_OK)
        except (error):
            return Response("error from paystack", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Webhooks


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhook(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        data = request.data

        secret = os.environ.get('PAYSTACK_TEST_SECRET')
        if not secret:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            data_string = json.dumps(data)
            body = json.loads(data_string)
            # body_unicode = json.dumps(body, separators=(',', ':'))
            # computed_hash = hmac.new(
            #     secret.encode('utf-8'),
            #     msg=body_unicode.encode('utf-8'),
            #     digestmod=hashlib.sha512
            # ).hexdigest()
            computed_hash = compute_sha512(secret, data)

            paystack_hash = request.headers.get('x-paystack-signature')

            if computed_hash == paystack_hash:
                # Process the event
                event = body
                # Do something with the event (e.g., update database, trigger tasks)
                # Example:
                if event.get('event') == 'charge.success':
                    transaction = Transactions.objects.get(id=event.get(
                        'data').get('metadata').get('transaction_id'))
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


@method_decorator(csrf_exempt, name='dispatch')
class MonnifyWebhook(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        headers = request.headers
        data = request.data

        monnify_secret = os.environ.get('MONNIFY_TEST_SECRET')

        try:
            data_string = json.dumps(data)
            body = json.loads(data_string)

            computed_hash = compute_sha512(monnify_secret, data)
            monnify_hash = headers.get('monnify-signature')
            # print('computed_hash',computed_hash)
            # print('monnify_hash',monnify_hash)
            if computed_hash == monnify_hash:
                # print(body)
                email = body['eventData']['customer']['email']
                amount = float(body['eventData']
                               ['settlementAmount'].split('.')[0])
                reference = body['eventData']['transactionReference']

                if body['eventType'] == "SUCCESSFUL_TRANSACTION":
                    user = UserAccount.objects.get(email=email)
                    Transactions.objects.create(user=user, transaction_type="Fund Wallet", is_successful=True,
                                                amount=amount, number="", status="success", reference=f"Monnify{reference}")
                    user.wallet += amount
                    user.save()
                    return Response(status=status.HTTP_200_OK)
            else:
                print('hash do not match')
                return Response(status=status.HTTP_400_BAD_REQUEST)

        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
            return Response(f"Invalid request: {e}", status=status.HTTP_400_BAD_REQUEST)

        # print(headers)
        # print(data)


class PersonalAccountView(APIView):
    def get(self, request):
        user = request.user
        account_details = PersonalAccount.objects.filter(user=user)

        serializer = PersonalAccountSerializer(account_details, many=True)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        body = request.data
        user = request.user

        email = body['email']
        account_name = body['account_name']
        nin = body['nin']

        monnify_secret = os.environ.get('MONNIFY_TEST_SECRET')
        monnify_api_key = os.environ.get('MONNIFY_TEST_API_KEY')
        monnify_contract_code = os.environ.get('MONNIFY_CONTRACT_CODE')

        b64 = monnify_encode_base64(monnify_api_key, monnify_secret)
        headers = {
            'Authorization': b64
        }
        print(headers)
        monnify_login = requests.post(
            f"{monnify_base_url}/api/v1/auth/login", headers=headers, data={})

        print(monnify_login.json())

        if monnify_login.json()["requestSuccessful"] != True:
            return Response(monnify_login.json(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        monnify_access_token = monnify_login.json()[
            'responseBody']['accessToken']

        personal_account_url = f"{monnify_base_url}/api/v2/bank-transfer/reserved-accounts"

        personal_account_headers = {
            'Authorization': f"Bearer {monnify_access_token}",
            'Content-Type': 'application/json'
        }

        now = datetime.datetime.now()
        now_str = now.strftime("%Y%m%d%H%M%S")
        random_string = ''.join(random.choices(
            string.ascii_letters + string.digits, k=5))

        personal_account_data = {
            "accountReference": f"{now_str}{random_string}",
            "accountName": account_name,
            "currencyCode": "NGN",
            "contractCode": monnify_contract_code,
            "customerEmail": user.email,
            "nin": nin,
            "customerName": user.name,
            "getAllAvailableBanks": True,
        }
        try:
            personal_account_response = requests.post(
                f"{personal_account_url}", headers=personal_account_headers, data=json.dumps(personal_account_data))
            print(personal_account_response.json())
            if personal_account_response.json()["requestSuccessful"] == True:
                account_details = personal_account_response.json()

                for account in account_details['responseBody']['accounts']:
                    account_number = account['accountNumber']
                    account_name = account['accountName']
                    bank_name = account['bankName']
                    PersonalAccount.objects.create(
                        user=user, account_number=account_number, bank=bank_name, account_name=account_name)
                return Response(account_details, status=status.HTTP_200_OK)
            else:
                return Response(personal_account_response.json(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except requests.exceptions.RequestException as e:
            return Response(f"Error: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountDetails(APIView):
    def get(request):
        user = request.user
        account_details = PersonalAccount.objects.filter(user=user)
        serializer = PersonalAccountSerializer(account_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
