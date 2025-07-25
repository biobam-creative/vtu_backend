from django.urls import path
from .views import *

urlpatterns = [
    path('signup', SignupView.as_view()),
    path('token/obtain', LoginView.as_view()),
    path('dashboard', Dashboard.as_view()),
    path('token_pair', MyObtainTokenPairWithView.as_view()),
    path('wallet', WalletRechargeView.as_view()),
    path('save_transaction_pin', SavePin.as_view(), name='save_pin'),
    path('token_check/<uidb64>/<token>/<mail_type>',
         VerificationMailCheck.as_view(), name='verification_mail_check'),
    path('request_Password_change', RequestPassordChangeEmail.as_view(),
         name='request_reset_email'),
    path('password_reset_check/<uidb64>/<token>',
         PasswordTokenCheckAPIView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete', SetNewPasswordAPIView.as_view(),
         name='password_reset_complete'),
]
