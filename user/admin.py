from django.contrib import admin
from .models import UserAccount



class UserAdmin(admin.ModelAdmin):
    model = UserAccount
    list_display = ("email", "name", "wallet", "verified", "is_superuser")
    
admin.site.register(UserAccount, UserAdmin)
