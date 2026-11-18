from django.urls import path

from .views import RecognizeDocumentView

urlpatterns = [
    path("documents/recognize/<str:kind>/", RecognizeDocumentView.as_view(), name="recognize-document"),
]
