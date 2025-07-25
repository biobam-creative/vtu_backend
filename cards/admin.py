from django.contrib import admin

from .models import *


class CardAdmin(admin.ModelAdmin):
    list_display = ("card_holder", "card_id")


class CardHolderAdmin(admin.ModelAdmin):
    list_display = ("user", "card_holder_id")


class DollarToNairaAdmin(admin.ModelAdmin):
    list_display = ("rate", "last_updated")


admin.site.register(DollarToNaira, DollarToNairaAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(CardHolder, CardHolderAdmin)

# Register your models here.
