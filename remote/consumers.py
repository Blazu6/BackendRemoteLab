from urllib.parse import parse_qs
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
            try:
                await self._client.send_raw(text_data)
            except (ConnectionResetError, OSError):
                print("[DEBUG] guacd connection lost, closing WebSocket")
                await self.close()

    async def connect(self):
        await self.accept(subprotocol='guacamole')
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        print(f"Query string {query_string}")
        params = parse_qs(query_string)
        print(f"Po sprarsowaniu {params}")
        protocol = params.get('protocol', ['ssh'])[0]
        hostname = params.get('hostname', ['172.17.0.1'])[0]
        port = params.get('port', ['22'])[0]
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]

        try:
            self._client = AsyncGuacamoleClient(
                settings.GUACD_HOST, 
                settings.GUACD_PORT, 
                self.handle_guacamole_data
            )
            print(f"[DEBUG] Connecting to guacd at {settings.GUACD_HOST}:{settings.GUACD_PORT}")
            await self._client.open()
            print(f"[DEBUG] Connected to guacd, starting handshake...")
            await self._client.handshake(
                protocol=protocol,
                hostname=hostname,
                port=port,
                username=username,
                password=password,
            )
            print(f"[DEBUG] Handshake completed successfully!")
        except Exception as e:
            import traceback
            print(f"[ERROR] Exception during connect: {e}")
            traceback.print_exc()
            await self.close()

    async def disconnect(self, close_code):
        if self._client is not None:
            await self._client.close()

    async def handle_guacamole_data(self, instruction: GuacamoleProtocol):
        await self.send(text_data=instruction.encode())

    