from django.urls import path, include
from rest_framework import routers
from .views import signature, setSignatureView, index_page, getUserView, getCarView, getTestLogByVinView 

urlpatterns = [
    path('setsignature/', setSignatureView.as_view()),
	path('getuser/', getUserView.as_view()),
	path('getcar/', getCarView.as_view()),
	path('signature/', signature),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	path('backup/', index_page),
	path('gettestlog/', getTestLogByVinView.as_view()), 
]