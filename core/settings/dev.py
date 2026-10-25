from .base import *

DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
INSTALLED_APPS += ['django_extensions']