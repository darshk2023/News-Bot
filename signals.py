from slacky.scheduler import start
from django.dispatch import receiver
from django.db.models.signals import post_migrate

@receiver(post_migrate)
def start_schedule(sender, **kwargs):
    start()