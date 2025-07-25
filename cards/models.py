from operator import is_
from django.db import models
from user.models import UserAccount


class CardHolder(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    id_image = models.ImageField(upload_to="media/id")
    card_holder_id = models.CharField(max_length=250, blank=True, null=True)
    identity_verification_status = models.CharField(
        max_length=250, default="PENDING")
    is_active = models.BooleanField(default=True)
    livemode = models.BooleanField(default=False)


class Card(models.Model):
    card_holder = models.ForeignKey(CardHolder, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(auto_now_add=True)
    card_id = models.CharField(max_length=250)
    is_active = models.BooleanField(default=True)
    card_type = models.CharField(max_length=250, default="VIRTUAL")
    card_currency = models.CharField(max_length=250, default="USD")
    last_four = models.CharField(max_length=4, blank=True, null=True)
    card_name = models.CharField(max_length=250, blank=True, null=True)
    card_expiry = models.CharField(max_length=250, blank=True, null=True)


class DollarToNaira(models.Model):
    rate = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
