from django.contrib import admin
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.urls import include, path

from .views import health_check


def csrf_probe(request):
    return HttpResponse(get_token(request))


urlpatterns = [
    path("health/", health_check, name="health"),
    path("_test/csrf/", csrf_probe),
    path("app/testlog/", include("testlog.urls")),
    path("", admin.site.urls),
]
