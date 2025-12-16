import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.sentry import init_sentry
init_sentry()

from celery import Celery

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()