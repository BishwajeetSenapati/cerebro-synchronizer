import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CerebroConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group = f'room_{self.room_code}'
        self.role = None
        self.name = 'Unknown'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
    # If broadcaster leaves, notify everyone with special message
        if self.role == 'broadcaster':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'broadcaster_left',
                    'name': self.name,
                }
            )
        else:
        # Normal peer left
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'peer_left',
                    'name': self.name,
                    'role': self.role,
                }
            )
    # Leave room group
        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name
        )
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'join':
            self.name = data.get('name', 'Unknown')
            self.role = data.get('role', 'listener')
            # Notify everyone in room
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'peer_joined',
                    'name': self.name,
                    'role': self.role,
                }
            )

        elif msg_type == 'play':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'sync_play',
                    'time'      : data.get('time', 0),
                    'sender'    : self.name,
                }
            )

        elif msg_type == 'pause':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'sync_pause',
                    'time'      : data.get('time', 0),
                    'sender'    : self.name,
                }
            )

        elif msg_type == 'seek':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'sync_seek',
                    'time'      : data.get('time', 0),
                    'sender'    : self.name,
                }
            )

        elif msg_type == 'stop':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'sync_stop',
                    'sender'    : self.name,
                }
            )

        elif msg_type == 'chat':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'chat_message',
                    'message'   : data.get('message', ''),
                    'sender'    : self.name,
                    'role'      : self.role,
                }
            )

        elif msg_type == 'video_url':
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type'      : 'sync_video_url',
                    'url'       : data.get('url', ''),
                    'sender'    : self.name,
                }
            )

    # ================================================================
    # GROUP MESSAGE HANDLERS
    # These fire on every client in the room group
    # ================================================================

    async def peer_joined(self, event):
        await self.send(text_data=json.dumps({
            'type'  : 'peer_joined',
            'name'  : event['name'],
            'role'  : event['role'],
        }))

    async def peer_left(self, event):
        await self.send(text_data=json.dumps({
            'type'  : 'peer_left',
            'name'  : event['name'],
            'role'  : event['role'],
        }))

    async def sync_play(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'play',
            'time'      : event['time'],
            'sender'    : event['sender'],
        }))

    async def sync_pause(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'pause',
            'time'      : event['time'],
            'sender'    : event['sender'],
        }))

    async def sync_seek(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'seek',
            'time'      : event['time'],
            'sender'    : event['sender'],
        }))

    async def sync_stop(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'stop',
            'sender'    : event['sender'],
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'chat',
            'message'   : event['message'],
            'sender'    : event['sender'],
            'role'      : event['role'],
        }))

    async def sync_video_url(self, event):
        await self.send(text_data=json.dumps({
            'type'      : 'video_url',
            'url'       : event['url'],
            'sender'    : event['sender'],
        }))
    async def broadcaster_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'broadcaster_left',
            'name': event['name'],
        }))