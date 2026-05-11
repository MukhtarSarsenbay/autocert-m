from django.apps import AppConfig


class TestlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "testlog"
    verbose_name = "Запись об испытаниях"
