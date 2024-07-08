from channels.generic.websocket import AsyncWebsocketConsumer
import json


class MapConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.map_id = self.scope['url_route']['kwargs']['map_id']
        self.map_group_name = f'map_{self.map_id}_updates'

        # Присоединяемся к группе комнаты
        await self.channel_layer.group_add(
            self.map_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.map_group_name,
            self.channel_name
        )

    async def send_update(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))
