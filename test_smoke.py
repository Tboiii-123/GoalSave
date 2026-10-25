
from django.conf import settings


def test_django_settings_are_configured():
    assert settings.configured
    assert settings.SECRET_KEY


def test_installed_apps_are_configured():
    assert "django.contrib.auth" in settings.INSTALLED_APPS
    assert "rest_framework" in settings.INSTALLED_APPS