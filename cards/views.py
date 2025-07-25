from time import sleep
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from AesEverywhere import aes256
from transactions.transaction_utilites import compute_sha512
from user.user_utilities import send_confirmation_email

from .models import Card, CardHolder, DollarToNaira
from .serializers import CardSerializer, CardHolderSerializer, DollarToNairaSerializer
from .tokens import base_url

import os
import requests
import json
from user.models import UserAccount

from datetime import datetime

today = datetime.now()


class CardView(APIView):
    def get(self, request):
        user = request.user
        cardholder = CardHolder.objects.get(user=user)
        cards = Card.objects.filter(cardholder=cardholder)
        serializer = CardSerializer(cards, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data

        serializer = CardSerializer(data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Incorrect data supplied"}, status=status.HTTP_400_BAD_REQUEST)


class CardHolderCreationView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        try:
            card_holder = CardHolder.objects.get(user=user)
            serializer = CardHolderSerializer(card_holder)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):

        data = request.data
        user = request.user
        files = request.FILES

        print(files["id_image"])

        # Check if the user already has a card holder
        try:
            card_holder = CardHolder.objects.get(user=user)
            if card_holder.identity_verification_status == "Success":
                # if the user already has a card holder and the verification is successful, return the card holder
                return Response({"message": "Card holder already exists"}, status=status.HTTP_400_BAD_REQUEST)
            elif card_holder.identity_verification_status == "Failed":
                # if the user already has a card holder and the verification failed, delete the card holder
                card_holder.delete()
        except CardHolder.DoesNotExist:
            # if the user does not have a card holder, create one
            if "id_image" not in files:
                return Response({"message": "ID image is required"}, status=status.HTTP_400_BAD_REQUEST)
            card_holder = CardHolder.objects.create(
                user=user, id_image=files["id_image"], is_active=False)
        # Create the card holder

        test_authorization_token = os.environ.get(
            'BRIDGE_TEST_AUTHORIZATION_TOKEN')
        url = base_url + "cardholder/register_cardholder"

        payload = json.dumps({
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "address": {
                "address": data.get("address"),
                "city": data.get("city"),
                "state": data.get("state"),
                "country": data.get("country"),
                "postal_code": data.get("postal_code"),
                "house_no": data.get("house_no"),
            },
            "phone": data.get("phone"),
            "email_address": user.email,
            "identity": {
                "id_type": data.get("id_type"),
                "id_no": data.get("id_no"),
                "id_image": f"http://127.0.0.1:8000{card_holder.id_image.url}" if card_holder.id_image else None,
                "bvn": data.get("bvn"),
            },
            "meta_data": {"user_email": user.email}}
        )

        # print(payload)

        headers = {
            'token': f'Bearer {test_authorization_token}',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
        print(response.status_code)
        # Check if the card holder was created successfully
        if response.status_code != 201:
            return Response({"message": "Card holder creation failed"}, status=status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        cardholder = CardHolder.objects.get(
            user=user,
        )
        cardholder.card_holder_id = response_data.get(
            "data").get("cardholder_id")
        cardholder.save()
        serializer = CardHolderSerializer(cardholder)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DollarCardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            card_holder = CardHolder.objects.get(user=user)
            if card_holder.identity_verification_status != "Success":
                return Response({"message": "KYC verification not successful"}, status=status.HTTP_400_BAD_REQUEST)
        except CardHolder.DoesNotExist:
            return Response({"message": "Card holder does not exist"}, status=status.HTTP_404_NOT_FOUND)

        cards = Card.objects.filter(
            card_holder=card_holder, card_currency="USD", card_type="VIRTUAL")
        if not cards:
            return Response({"message": "No dollar cards found"}, status=status.HTTP_404_NOT_FOUND)
        test_authorization_token = os.environ.get(
            'BRIDGE_TEST_AUTHORIZATION_TOKEN')
        headers = {
            'token': f'Bearer {test_authorization_token}',
            'Content-Type': 'application/json'
        }

        # for card in cards:
        # response = requests.get(
        # f"{base_url}cards/get_card_details?card_id={card.card_id}", headers=headers)

        # response = requests.get(
        #     f"https://issuecards-api-bridgecard-co.relay.evervault.com/v1/issuing/sandbox/cards/get_card_details?card_id={card.card_id}", headers=headers)
        # sleep(3)  # To avoid rate limiting

        # print(json.loads(response.text))
        serializer = CardSerializer(cards, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        print(data)
        try:
            card_holder = CardHolder.objects.get(user=user)
            if card_holder.identity_verification_status != "Success":
                print("KYC verification not successful")
                return Response({"message": "KYC verification not successful"}, status=status.HTTP_400_BAD_REQUEST)
        except CardHolder.DoesNotExist:
            return Response({"message": "Card holder does not exist"}, status=status.HTTP_404_NOT_FOUND)

        secret_key = os.environ.get('BRIDGE_TEST_SECRET_KEY')

        encrypted = aes256.encrypt(data.get("pin"), secret_key)
        encrypted_pin = encrypted.decode()
        print(encrypted)

        # url = "https://issuecards.api.bridgecard.co/v1/issuing/sandbox/cards/create_card"

        test_authorization_token = os.environ.get(
            'BRIDGE_TEST_AUTHORIZATION_TOKEN')
        url = base_url + "cards/create_card"

        payload = json.dumps({
            "cardholder_id": card_holder.card_holder_id,
            "card_type": "virtual",
            "card_brand": "Mastercard",
            "card_currency": "USD",
            "card_limit": data.get("limit"),
            # Assuming funding_amount is in dollars and needs to be converted to cents
            "funding_amount": str(int(data.get("funding_amount"))*100),
            "pin": encrypted_pin,
            "transaction_reference": f"{today.strftime('%Y%m%d%H%M%S')}",
            "meta_data": {
                "user_id": card_holder.card_holder_id,
                "user_email": user.email, }
        })
        headers = {
            'token': f'Bearer {test_authorization_token}',
            'Content-Type': 'application/json'
        }

        print(payload)

        response = requests.post(url, headers=headers, data=payload)

        response = json.loads(response.text)

        print(response)
        if response.get("status") != "success":
            return Response({"message": "Card creation failed"}, status=status.HTTP_400_BAD_REQUEST)

        details = requests.get(
            f"https://issuecards-api-bridgecard-co.relay.evervault.com/v1/issuing/sandbox/cards/get_card_details?card_id={response.get('data').get('card_id')}", headers=headers)
        details = json.loads(details.text)

        def format_expiry(month, year):
            if len(str(month)) == 1:
                return f'0{month}/{str(year)[2:]}'
            else:
                f'{month}/{str(year)[2:]}'
            return f'0{month}/{str(year)[2:]}'

        card = Card.objects.create(card_holder=card_holder,
                                   card_id=response.get("data").get("card_id"),
                                   card_type="VIRTUAL",
                                   card_currency="USD",
                                   is_active=True,
                                   last_four=details.get(
                                       "data").get("last_4"),
                                   card_name=details.get(
                                       "data").get("card_name"),
                                   card_expiry=format_expiry(
                                       details.get("data").get("expiry_month"), details.get("data").get("expiry_year"))
                                   )

        serializer = CardSerializer(card)
        return Response(serializer.data, status=status.HTTP_200_OK)
        # else:
        #     return Response({"message": "Incorrect data supplied"}, status=status.HTTP_400_BAD_REQUEST)


class RateView(APIView):
    def get(self, request):
        rate = DollarToNaira.objects.order_by("-last_updated")[0]
        serializer = DollarToNairaSerializer(rate)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FundDollarCardView(APIView):
    def post(self, request, card_id):
        user = request.user
        data = request.data

        rate = DollarToNaira.objects.order_by("-last_updated")[0].rate
        print(rate)
        print(user.wallet)
        print(data.get("amount"))

        if user.wallet is None or user.wallet <= int(data.get("amount")) * rate:
            return Response({"message": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
        # Check if the card exists and belongs to the user
        try:
            card = Card.objects.get(card_id=card_id, card_holder__user=user)
        except Card.DoesNotExist:
            return Response({"message": "Card not found"}, status=status.HTTP_404_NOT_FOUND)

        test_authorization_token = os.environ.get(
            'BRIDGE_TEST_AUTHORIZATION_TOKEN')
        url = base_url + "cards/fund_card_asynchronously"

        payload = json.dumps({
            "card_id": card_id,
            "amount": str(int(data.get("amount"))*100),  # Convert to cents
            "transaction_reference": f"{today.strftime('%Y%m%d%H%M%S')}",
            "currency": "USD",
        })

        headers = {
            'token': f'Bearer {test_authorization_token}',
            'Content-Type': 'application/json'
        }

        response = requests.patch(url, headers=headers, data=payload)
        response_data = json.loads(response.text)

        print(response_data)

        if response_data.get("status") != "success":
            return Response({"message": "Funding failed"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Card funding in progress"}, status=status.HTTP_200_OK)


class DollarCardDetailsView(APIView):

    def get(self, request, card_id):
        user = request.user

        test_authorization_token = os.environ.get(
            'BRIDGE_TEST_AUTHORIZATION_TOKEN')

        headers = {
            'token': f'Bearer {test_authorization_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f"https://issuecards-api-bridgecard-co.relay.evervault.com/v1/issuing/sandbox/cards/get_card_details?card_id={card_id}", headers=headers)

        response = json.loads(response.text)
        print(response)
        return Response(response, status=status.HTTP_200_OK)


class BridgeCardWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_data = request.data
        headers = request.headers

        signature = headers.get("x-webhook-signature")
        print(event_data)

        secret_key = os.environ.get('BRIDGE_TEST_SECRET_KEY')
        webhook_secret = os.environ.get("BRIDGE_TEST_WEBHOOK_SECRET")
        # decrypted_signature = compute_sha512(secret_key, signature)
        decrypted = aes256.decrypt(signature, secret_key).decode('utf-8')
        # print("decrypted:"decrypted)
        print(decrypted != webhook_secret)
        signature = request.headers.get('X-webhook-Signature')
        if not signature or decrypted != webhook_secret:
            print("Invalid signature")
            return Response({"message": "Invalid signature"}, status=status.HTTP_200_OK)

        # Process the webhook data
        data = event_data.get("data")
        event = event_data.get("event")

        print("event:", event, "data:", data)
        print(event == "cardholder_verification.successful")
        if event == "cardholder_verification.successful":
            cardholder_id = data.get("cardholder_id")
            try:

                card_holder = CardHolder.objects.get(
                    card_holder_id=cardholder_id)
                card_holder.identity_verification_status = "Success"
                card_holder.is_active = True
                card_holder.save()
                send_confirmation_email(
                    card_holder.user, message="Your KYC verification successful", subject="KYC verifivation successful", mail_type=None)
                return Response(status=status.HTTP_200_OK)
            except CardHolder.DoesNotExist:
                return Response(status=status.HTTP_200_OK)
        elif event == "cardholder_verification.failed":
            cardholder_id = data.get("cardholder_id")
            error_description = data.get("error_description")
            try:
                card_holder = CardHolder.objects.get(
                    card_holder_id=cardholder_id)
                send_confirmation_email(
                    card_holder.user, message=f"User KYC verification failed this is probably because {error_description}", subject="KYC verifivation failed", mail_type=None)
                return Response(status=status.HTTP_200_OK)
            except CardHolder.DoesNotExist:
                return Response(status=status.HTTP_200_OK)
        elif event == "card_credit_event.successful":
            cardholder_id = data.get("cardholder_id")
            try:
                cardholder = CardHolder.objects.get(
                    card_holder_id=cardholder_id)
                rate = DollarToNaira.objects.order_by("-last_updated")[0].rate
                user = cardholder.user
                print("User wallet before funding:", user.wallet)
                user.wallet -= int(data.get("amount")) / \
                    100 * rate  # Convert to naira
                user.save()
                print(user.wallet)
                return Response(status=status.HTTP_200_OK)
            except Card.DoesNotExist:
                return Response(status=status.HTTP_200_OK)

        elif event == "card_credit_event.failed":
            cardholder_id = data.get("cardholder_id")
            try:
                cardholder = CardHolder.objects.get(
                    card_holder_id=cardholder_id)
                send_confirmation_email(
                    cardholder.user, message="Your latest attempt to fund your card with card ID: {card_id} failed please try later", subject="Card funding failed", mail_type=None)
                return Response(status=status.HTTP_200_OK)
            except CardHolder.DoesNotExist:
                return Response(status=status.HTTP_200_OK)
