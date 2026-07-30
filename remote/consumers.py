from channels.generic.websocket import AsyncWebsocketConsumer

from django.conf import settings

from .client_async import AsyncGuacamoleClient
from .protocol import GuacamoleProtocol

class GuacamoleConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None
                

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None and self._client is not None:
            await self._client.send_raw(text_data)

    async def connect(self):
        await self.accept(subprotocol='guacamole')
        self._client = AsyncGuacamoleClient(
            settings.GUACD_HOST, 
            settings.GUACD_PORT, 
            self.handle_guacamole_data
        )
        await self._client.open()
        await self._client.handshake(
            protocol="ssh",
            hostname="172.17.0.1",
            port="22",
            username="pass",
            password="pass",
        )

    async def disconnect(self, close_code):
        if self._client is not None:
            await self._client.close()

    async def handle_guacamole_data(self, instruction: GuacamoleProtocol):
        await self.send(text_data=instruction.encode())

    