from django.db import models
from user.models import UserAccount


class Notification(models.Model):
    user = models.ForeignKey(
        UserAccount, related_name='user', on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=50)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.message[:50]}"
