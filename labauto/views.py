from django.http import HttpResponse


def health_check(request):
    return HttpResponse("ok\n", content_type="text/plain")
