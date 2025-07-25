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
