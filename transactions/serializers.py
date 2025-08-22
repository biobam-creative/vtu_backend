from rest_framework import serializers
from .models import Ads, Transactions, PersonalAccount


class TransactionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transactions
        fields = ('__all__')


class PersonalAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = PersonalAccount
        fields = ('__all__')


class AdsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ads
        fields = ('__all__')


class MonthlyTransactionSerializer(serializers.Serializer):

    month = serializers.DateTimeField(format="%Y-%m")
    items = TransactionsSerializer(many=True)
