from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import *
from user.models import UserAccount


def send_notification_to_user(user_id, message, notification_type="info", extra_data=None):
    user = UserAccount.objects.get(id=user_id)
    notification = Notification.objects.create(
        user=user, message=message, notification_type=notification_type, extra_data=extra_data or {})
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'notification_{user_id}',
                                            {
                                                'type': 'send_notification',
                                                'data': {
                                                    'id': notification.id,
                                                    'message': message,
                                                    'notification_type': notification_type,
                                                    'created_at': notification.created_at.isoformat(),
                                                    'extra_data': extra_data or {},
                                                    'unread_count': Notification.objects.filter(user=user, is_read=False).count()}})
    return notification
