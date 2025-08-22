from django.urls import path
from .views import *


urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/mark-as-read/', NotificationMarkAsReadView.as_view(),
         name='notification-mark-read'),
    path('mark-all-as-read/', NotificationMarkAllAsReadView.as_view(),
         name='notification-mark-all-read'),
]
