from django.urls import path
from .views import *

urlpatterns = [
    path('save_transaction', SaveTransactionView.as_view()),
    path('paystack_webhook', PaystackWebhook.as_view()),
    path('paystack_intialize', InitializePaystackPayment.as_view()),
    path('personal_account', PersonalAccountView.as_view()),
    path('monnify_webhook', MonnifyWebhook.as_view()),
    path('get_account_details', AccountDetails.as_view()),
]
