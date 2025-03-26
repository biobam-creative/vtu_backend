

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import permissions, status

from .user_utilities import Util, token_check
from .serializers import *
from .models import *
from transactions.models import Transactions
from transactions.serializers import TransactionsSerializer

User = get_user_model()

class SignupView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format=None):
        data = request.data

        name = data['name']
        email = data['email']
        password = data['password']
        password2 = data['password2'] 

        if password == password2:
            if User.objects.filter(email=email).exists():
                return Response({'error':'User already exist'},status=status.HTTP_400_BAD_REQUEST)
            else:
                if len(password) < 6:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                    
                else:
                    user = User.objects.create_user(email=email, password=password, name=name)
                    user.save()
                    
                    return Response({'message':'User crated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error':'Password do not match'}, status=status.HTTP_400_BAD_REQUEST)
        


class MyObtainTokenPairWithView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


class LoginView(APIView):
    permission_classes = (permissions.AllowAny, )
    def post(self, request):
        data = request.data
        email = data['email']
        password = data['password']

        user = authenticate(email=email, password=password)

        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif not user.verified:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        else:
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            user_info = {
                'refresh':str(refresh),
                'access':str(refresh.access_token),
                'user':user_data
            }

            return Response(user_info, status=status.HTTP_200_OK)

        
        return Response({
            'message':'something went wrong',
            'data':serializer.errors
        })

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_number'
    max_page_size = 10

class Dashboard(APIView):
    # pagination_class = StandardResultsSetPagination
    serializer_class = TransactionsSerializer
    
    def get(self, request):
        data = request.data
        user = request.user
        queryset = Transactions.objects.filter(user=user).order_by('-time')[:10]
        user_setaializer = UserSerializer(user).data
        transaction_serializer = TransactionsSerializer(queryset, many=True).data
        data = {
            'user':user_setaializer,
            'transactions':transaction_serializer
        }
        return Response(data)
        

class WalletRechargeView(APIView):
    def post(self, request, format=None):

        data = self.request.data
        print(self.request.headers['Authorization'])

        email = data['email']
        amount = data['amount']

        user = UserAccount.objects.get(email=email)
        wallet = Wallet.objects.get(owner=user)
        wallet.balance += amount
        wallet.save()
        serializer = WalletSerializer(wallet)

        return Response(serializer.data)

#view for verifying verification sent
class VerificationMailCheck(APIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, uidb64, token, mail_type):

        id=smart_str(urlsafe_base64_decode(uidb64))
        user=User.objects.get(id=id)
        check = token_check(uidb64, token)
        if check:
            if mail_type == 'password_reset':
                return Response({'success':True,'message':'Email Checked', 'uidb64':uidb64,'token':token, 'mail_type':mail_type}, status=status.HTTP_200_OK)
            elif mail_type == "user_verification":
                user.verified = True
                user.save()
                return Response({'success':True,'message':'Email Verified', 'uidb64':uidb64,'token':token, 'mail_type':mail_type}, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class RequestPasswordResetEmail(APIView):
    permission_classes = (permissions.AllowAny, )
    # serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email=request.data['email']
        user = User.objects.get(email=email)
        if user:
            uidb64 = urlsafe_base64_encode(str(user.id).encode('utf-8'))
            reset_password_token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relative_link = reverse('password_reset_confirm',kwargs={'uidb64':uidb64,'token':reset_password_token})
            absurl = f'http://localhost:3000/set-new-password/{uidb64}/{reset_password_token}'
            # absurl = 'http://'+current_site + relative_link
            email_body = 'Hello, \n Use the link below to reset your password \n' + absurl

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
                    "Subject": "Password reset",
                    "TextPart": email_body,
                    "HTMLPart": email_body,
                    "CustomID": "AppGettingStartedTest"
                    }
                ]
                }
            Util.send_mail(data)
        return Response({'success':'An email to reset your password has been sent'} ,status=status.HTTP_200_OK)

class PasswordTokenCheckAPIView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, uidb64, token):
        try:
            id=smart_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error':'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'success':True,'message':'Credential Valid', 'uidb64':uidb64,'token':token}, status=status.HTTP_200_OK)
        except DjangoUnicodeDecodeError:
            return Response({'error':'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)

class SetNewPasswordAPIView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer=self.serializer_class(data=request.data)
        print(request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success':True, 'message':'Password reset success'}, status=status.HTTP_200_OK)

