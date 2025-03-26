from django.contrib import admin
from .models import UserAccount



class UserAdmin(admin.ModelAdmin):
    model = UserAccount
    
admin.site.register(UserAccount, UserAdmin)
