from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .user_utilities import *


User = get_user_model()

@receiver(post_save, sender=User)
def send_Verification_mail(sender, instance, created, **kwargs):
    if created:
        print(instance)
        send_confirmation_email(user=instance, message='Click to Verify your email', subject='User Verification', mail_type='user_verification')