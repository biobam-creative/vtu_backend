from django.urls import path
from .views import *


urlpatterns = [
    path('cards', CardView.as_view()),
    path('cardholder', CardHolderCreationView.as_view()),
    path('bridge_webhook', BridgeCardWebhookView.as_view()),
    path('dollar_card', DollarCardView.as_view()),
    path('dollar_cards_details/<str:card_id>', DollarCardDetailsView.as_view()),
    path('fund_card/<str:card_id>', FundDollarCardView.as_view()),
    path('rate', RateView.as_view(),)

]
