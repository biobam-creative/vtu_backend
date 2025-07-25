from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import *


User = get_user_model()

# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ('email')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ('__all__')


class UserSerializerWithToken(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('token', 'email', 'paassword')


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)
        # wallet = WalletSerializer(Wallet.objects.get(owner=self.user))
        user = UserSerializer(UserAccount.objects.get(email=self.user))

        # data.update({'wallet':wallet.data})
        data.update({'user': user.data})
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ('email')


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=100, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ('password', 'token', 'uidb64')

    def validate(self, attrs):
        print(attrs)
        password = attrs.get('password')
        token = attrs.get('token')
        uidb64 = attrs.get('uidb64')
        print(password, token, uidb64)

        id = int(force_str(urlsafe_base64_decode(uidb64)))
        user = User.objects.get(id=id)
        print(id, user)

        print(PasswordResetTokenGenerator().check_token(user=user, token=token))

        if not PasswordResetTokenGenerator().check_token(user, token):
            print('token')
            raise AuthenticationFailed('The reset link is invalid', 401)

        user.set_password(password)
        user.save()

        return super().validate(attrs)
