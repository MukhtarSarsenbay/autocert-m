from django.urls import path, include
from .views import getStoreQR

urlpatterns = [
    path('qr/<str:code>', getStoreQR),
]