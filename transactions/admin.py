from django.contrib import admin
from .models import *

class TransactionAdminArea(admin.ModelAdmin):
    list_display = ("user", "number", "transaction_type", "amount", "is_successful", "status", "reference",)
    
    
class PersonalAccountAdminArea(admin.ModelAdmin):
    list_display = ("user", "account_number", "bank", "account_name",)

admin.site.register(Transactions, TransactionAdminArea)
admin.site.register(PersonalAccount, PersonalAccountAdminArea)
