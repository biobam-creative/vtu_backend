from rest_framework import serializers
from .models import *
from user.serializers import UserSerializer


class CardHolderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CardHolder
        fields = "__all__"


class CardSerializer(serializers.ModelSerializer):
    card_holder = CardHolderSerializer(read_only=True)

    class Meta:
        model = Card
        fields = "__all__"


class DollarToNairaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DollarToNaira
        fields = "__all__"
