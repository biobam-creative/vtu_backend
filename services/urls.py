from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('cabletvplan', CableTVPlanListView.as_view()),
    path('mobiledataplan', MobileDataPlanListView.as_view()),
    path('electricity_providers', ElectricityProviderListView.as_view()),
    path('upload_data', UploadDataVariations.as_view())

]
