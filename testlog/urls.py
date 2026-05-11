from django.urls import path

from .views import form_page, form_create, list_page, delete_page, data_page, download_pdf
urlpatterns = [
    path("", list_page),
    path("form/", form_create),
    path("form/<int:pk>/", form_page),
    path("data/<int:pk>/", data_page),
    path("delete/<int:pk>/", delete_page),
	path("download/<int:pk>/", download_pdf),
]
