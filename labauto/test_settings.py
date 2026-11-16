from .settings import *  # noqa: F403


INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "subuser.apps.SubuserConfig",
    "actus.apps.ActusConfig",
    "cert.apps.CertConfig",
    "testlog",
]

DATABASES = {
    "default": {
        "ENGINE": "labauto.test_sqlite",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
ROOT_URLCONF = "labauto.test_urls"
UNFOLD = {}
