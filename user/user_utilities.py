from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from rest_framework.response import Response
from rest_framework import status

from .models import *

from datetime import datetime, timedelta  

from mailjet_rest import Client
import os


def send_confirmation_email(user,  message, subject, mail_type):
    if user:

        uidb64 = urlsafe_base64_encode(str(user.id).encode('utf-8'))
        token = PasswordResetTokenGenerator().make_token(user)
        # current_site = get_current_site(request=request).domain
        # relative_link = reverse('password_reset_confirm',kwargs={'uidb64':uidb64,'token':reset_password_token})
        absurl = f'http://127.0.0.1:5173/token-check/{uidb64}/{token}/{mail_type}'
        # absurl = 'http://'+current_site + relative_link
        email_body = f'{message} \n' + absurl

        data = {
            'Messages': [
                {
                "From": {
                    "Email": "emmanueltesting2712@gmail.com",
                    "Name": "Emmanuel"
                },
                "To": [
                    {
                    "Email": user.email,
                    "Name": user.name
                    }
                ],
                "Subject": subject,
                "TextPart": email_body,
                "HTMLPart": email_body,
                "CustomID": "AppGettingStartedTest"
                }
            ]
                }
        # Util.send_mail(data)
        print(data)
    return Response({'success':'An email has been sent'} ,status=status.HTTP_200_OK)

api_key = os.environ.get('MAILJET_API_KEY')
api_secret = os.environ.get('MAILJET_API_SECRET')
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

class Util:
    @staticmethod
    def send_mail(data):
        result = mailjet.send.create(data=data)
        

def token_check(uidb64, token):
    try:
        id=smart_str(urlsafe_base64_decode(uidb64))
        user=UserAccount.objects.get(id=id)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return False
        else:
            return True
    except DjangoUnicodeDecodeError:
        return False