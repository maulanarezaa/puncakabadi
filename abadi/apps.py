from django.apps import AppConfig


class AbadiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'abadi'

    def ready(self):
        from . import viewssignal
