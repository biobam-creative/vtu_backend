import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous or isinstance(self.user, AnonymousUser):
            await self.close()
        else:
            self.group_name = f'notifications_{getattr(self.user, "id")}'
            if not self.channel_layer:
                print("No channel layer configured!")
                await self.close()
                return
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name') and self.channel_layer:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        print("Received from client:", text_data)
        # ...existing code...

    async def send_notification(self, event):
        print("Sending notification:", event['data'])
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(user=self.user, is_read=False).count()
