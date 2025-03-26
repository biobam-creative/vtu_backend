from django.urls import path
from .views import SaveTransactionView, PaystackWebhook,InitializePaystackPayment

urlpatterns = [
     path('save_transaction', SaveTransactionView.as_view()),
     path('paystack_webhook', PaystackWebhook.as_view()),
     path('paystack_intialize', InitializePaystackPayment.as_view()),
]