from django.shortcuts import render

from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions, status
from django_filters.rest_framework import DjangoFilterBackend

from .models import *
from .serializers import *
from .vtpass_data import data_variations


class MobileDataPlanListView(ListAPIView):
    serializer_class = MobileDataPlanSerializer

    filterset_fields = ['network']
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return MobileDataPlan.objects.all()


class ElectricityProviderListView(ListAPIView):
    serializer_class = ElectricityPaymentSerializer

    filterset_fields = ['disco']
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return ElectricityPayment.objects.all()


class CableTVPlanListView(ListAPIView):
    serializer_class = CableTVPlanSerializer

    filterset_fields = ['cable_tv_provider']
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return CableTVPlan.objects.all()


class UploadDataVariations(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        for variation in data_variations:
            name = variation.get("name")
            variation_code = variation.get("variation_code")
            variation_amount = variation.get("variation_amount")

            network = variation.get("network")
            data_cap = variation.get("data_cap")
            validity = variation.get("validity")
            price = int(variation_amount.split(".")[0])

            data = {
                "network": network,
                "price": price,
                "data_cap": data_cap,
                "validity": validity,
                "vt_pass_variation_code": variation_code,
                "name": name
            }
            serializer = MobileDataPlanSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                print(name)
        return Response({"message": "Success"}, status=200)
