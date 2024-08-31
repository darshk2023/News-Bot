import os
from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # Avoid running the scheduler during migrations and other management commands
        if os.environ.get('RUN_MAIN') == 'true':
            from slacky import scheduler
            scheduler.start()
