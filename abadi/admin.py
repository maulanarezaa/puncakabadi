from django.contrib import admin
from . import models
from django.apps import apps
from django.contrib.admin.models import LogEntry

app_models = apps.get_app_config('abadi').get_models()
admin.site.register(LogEntry)
for model in app_models:
    admin.site.register(model)
