from django.conf import settings
from core.settings import dev as dev_settings
from core.settings import prod as prod_settings
from ipaddress import ip_address

def test_lab_app_installed():
    assert 'lab' in settings.INSTALLED_APPS 

def test_dev_settings_debug_is_true():
    assert dev_settings.DEBUG is True

def test_prod_settings_debug_is_false():
    assert prod_settings.DEBUG is False

def test_secret_key_is_set():
    assert settings.SECRET_KEY != ''
    assert not settings.SECRET_KEY.startswith('django-insecure-')
    assert len(settings.SECRET_KEY) >= 30

def test_allowed_hosts_is_set_properly():
    assert isinstance(settings.ALLOWED_HOSTS, list)
    assert len(settings.ALLOWED_HOSTS) > 0
    for host in settings.ALLOWED_HOSTS:
        if host[0].isdigit():
            assert ip_address(host)
