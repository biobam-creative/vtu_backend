from django.db import models


class MobileDataPlan(models.Model):
    network = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    data_cap = models.CharField(max_length=100, blank=True, null=True)
    validity = models.CharField(max_length=100, blank=True, null=True)
    _type = models.CharField(max_length=100, blank=True, null=True)
    vt_pass_variation_code = models.CharField(
        max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.data_cap} === N{self.price} {self.validity}'


class CableTVPlan(models.Model):

    cable_tv_provider = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    vt_pass_variation_code = models.CharField(
        max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.cable_tv_provider} {self.name} === N{self.price}'


class ElectricityPayment(models.Model):
    disco = models.CharField(max_length=100)

    def __str__(self):
        return self.disco


class Exams(models.Model):
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    vt_pass_variation_code = models.CharField(
        max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.name} === N{self.price}'
