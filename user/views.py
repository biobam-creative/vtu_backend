import json
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Subquery, OuterRef
from django.conf import settings


from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import permissions, status

from .user_utilities import token_check, send_confirmation_email
from .serializers import *
from .models import *
from transactions.models import Transactions, PersonalAccount
from transactions.serializers import TransactionsSerializer, PersonalAccountSerializer, MonthlyTransactionSerializer
from transactions.transaction_utilites import compute_sha512
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
                return Response({'message': 'User already exist'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if len(password) < 6:
                    return Response({'message': 'Password Should not be less than 6 characters'}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    user = User.objects.create_user(
                        email=email, password=password, name=name)
                    user.save()

                    return Response({'message': 'User crated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Password do not match'}, status=status.HTTP_400_BAD_REQUEST)


class MyObtainTokenPairWithView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


class GetUser(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return (serializer.data)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):

        data = request.data
        email = data['email']
        password = data['password']
        print(data)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({"message": "Email or password is incorrect"}, status=status.HTTP_404_NOT_FOUND)
        elif not user.verified:
            send_confirmation_email(user=user, message="click to verify your email",
                                    subject='User Verification', mail_type='user_verification')
            return Response({"message": "User in not yet verified"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            user_info = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            }

            return Response(user_info, status=status.HTTP_200_OK)

        return Response({
            'message': 'something went wrong',
            'data': serializer.errors
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
        user_queryset = Transactions.objects.filter(user=user)
        months = user_queryset.annotate(month=TruncMonth('date')).values(
            'month').distinct().order_by('-month')
        result = []
        for month_data in months:
            month = month_data['month']
            queryset = user_queryset.filter(
                date__year=month.year, date__month=month.month).order_by('-date')
            result.append({
                "month": month,
                "items": queryset
            })

        user_setaializer = UserSerializer(user).data
        transaction_serializer = MonthlyTransactionSerializer(
            result, many=True).data

        data = {
            'user': user_setaializer,
            'transactions': transaction_serializer,
        }
        return Response(data, status=status.HTTP_200_OK)


class WalletRechargeView(APIView):
    def post(self, request, format=None):

        data = self.request.data

        email = data['email']
        amount = data['amount']

        user = UserAccount.objects.get(email=email)
        wallet = Wallet.objects.get(owner=user)
        wallet.balance += amount
        wallet.save()
        serializer = WalletSerializer(wallet)

        return Response(serializer.data)

# view for verifying verification sent


class VerificationMailCheck(APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request, uidb64, token, mail_type):

        id = smart_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=id)
        check = token_check(uidb64, token)
        if check:
            if mail_type == 'password_reset':
                return Response({'success': True, 'message': 'Email Checked', 'uidb64': uidb64, 'token': token, 'mail_type': mail_type}, status=status.HTTP_200_OK)
            elif mail_type == "user_verification":
                user.verified = True
                user.save()
                return Response({'success': True, 'message': 'Email Verified', 'uidb64': uidb64, 'token': token, 'mail_type': mail_type}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)


class RequestPassordChangeEmail(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        email = request.data['email']
        try:
            user = User.objects.get(email=email)
            send_confirmation_email(user, message='Click to Verify your email',
                                    subject='Password Reset', mail_type='password_reset')
            return Response({'success': 'An email to reset your password has been sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class PasswordTokenCheckAPIView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request, uidb64, token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error': 'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'success': True, 'message': 'Credential Valid', 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)
        except DjangoUnicodeDecodeError:
            return Response({'error': 'Token is not valid, please request another one'}, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordAPIView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


class SavePin(APIView):
    # permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            data = self.request.data
            user = self.request.user

            pin = data["pin"]

            encrypted_pin = compute_sha512(
                secret=settings.SECRET_KEY, data=pin)

            user.transaction_pin = encrypted_pin
            user.save()

            print(user.transaction_pin)
            data = {
                "success": "Pin created successfully"
            }

            return Response(data, status=status.HTTP_200_OK)
        except (ValueError):
            print(ValueError)
            return Response({"error": ValueError}, status=status.HTTP_400_BAD_REQUEST)
