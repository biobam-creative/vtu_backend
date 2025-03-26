from rest_framework import serializers
from .models import *



class CableTVPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = CableTVPlan
        fields = ('cable_tv_provider','name','price')

class ElectricityPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectricityPayment
        fields = ('__all__')

class MobileDataPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = MobileDataPlan
        fields = ('__all__')