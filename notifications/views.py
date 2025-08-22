from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from .models import *
from .serializer import *
from user.models import UserAccount


class NotificationListView(APIView):

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user).order_by('-created_at') or []
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationMarkAsReadView(APIView):
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllAsReadView(APIView):
    def Post(self, request):
        updated = Notification.objects.filter(
            user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'success', 'updated_count': updated}, status=status.HTTP_200_OK)
