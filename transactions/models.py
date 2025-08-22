from turtle import title
from django.db import models
from user.models import UserAccount
from datetime import datetime


class Transactions(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    number = models.CharField(max_length=100, blank=True, null=True)
    transaction_type = models.CharField(max_length=100)
    amount = models.FloatField()
    is_successful = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_type} {self.amount} {self.date} by {self.user}'


class PersonalAccount(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    bank = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user} account number {self.account_number}'


class Ads(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="media/ads")
    active = models.BooleanField()

    def __str__(self):
        return self.title
