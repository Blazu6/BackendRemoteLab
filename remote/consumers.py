from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer

from django.conf import settings
from django.core.cache import cache
from channels.db import database_sync_to_async
from .models import Machine
from .client_async import AsyncGuacamoleClient
from .protocol import GuacamoleProtocol


class GuacamoleConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None
        self.machine_id = None
        self.is_primary = False
                

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
        machine_id = params.get('machine_id', [None])[0]
        shadow = params.get('shadow', ['false'])[0]
        
        if not machine_id:
            print("[ERROR] No machine_id provided")
            await self.close()
            return
            
        self.machine_id = machine_id
            
        try:
            # Bezpieczne pobranie danych z bazy danych
            machine = await database_sync_to_async(Machine.objects.get)(id=machine_id)
        except Machine.DoesNotExist:
            print(f"[ERROR] Machine with id {machine_id} not found")
            await self.close()
            return
            
        protocol = machine.protocol
        hostname = machine.hostname
        port = str(machine.port)
        username = machine.username or ''
        password = machine.password or ''
        
        width = int(params.get('width', ['1024'])[0])
        height = int(params.get('height', ['768'])[0])

        # Dodatkowe parametry zależne od protokołu
        extras = {}
        if protocol == 'ssh':
            extras['ignore_host_key'] = 'true'
        elif protocol == 'rdp':
            extras['ignore_cert'] = 'true'
            extras['security'] = 'rdp'
            
        if shadow == 'readonly':
            extras['read_only'] = 'true'

        try:    
            self._client = AsyncGuacamoleClient(
                settings.GUACD_HOST, 
                settings.GUACD_PORT, 
                self.handle_guacamole_data
            )
            print(f"[DEBUG] Connecting to guacd at {settings.GUACD_HOST}:{settings.GUACD_PORT}")
            await self._client.open()
            print(f"[DEBUG] Connected to guacd, starting handshake...")
            
            if shadow in ['readonly', 'interactive', 'true']:
                # Tryb podglądu (Shadow) - pobieramy connection_id z Redisa
                connectionid = await cache.aget(f"guacd_session_{self.machine_id}")
                if not connectionid:
                    print(f"[ERROR] Brak aktywnej sesji dla maszyny {self.machine_id} w Redis!")
                    await self.close()
                    return
                print(f"[DEBUG] Dolaczam do istniejacej sesji: {connectionid} w trybie {shadow}")
                await self._client.handshake(
                    connectionid=connectionid,
                    width=width,
                    height=height,
                    **extras
                )
            else:
                # Standardowe nawiązanie nowej sesji
                await self._client.handshake(
                    protocol=protocol,
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    width=width,
                    height=height,
                    **extras,
                )
                self.is_primary = True
                # Zapisujemy wynegocjowane connection_id do Redis, aby inni mogli podglądać
                await cache.aset(f"guacd_session_{self.machine_id}", self._client.id, timeout=86400)
                print(f"[DEBUG] Zapisano connection_id do Redis: {self._client.id}")
                
            print(f"[DEBUG] Handshake completed successfully!")
        except Exception as e:
            import traceback
            print(f"[ERROR] Exception during connect: {e}")
            traceback.print_exc()
            await self.close()

    async def disconnect(self, close_code):
        if self.is_primary and self.machine_id:
            # Czyszczenie wpisu w Redis, by ikona "Podgląd" zniknęła
            await cache.adelete(f"guacd_session_{self.machine_id}")
            print(f"[DEBUG] Usunieto sesje maszyny {self.machine_id} z Redis")
            
        if self._client is not None:
            await self._client.close()

    async def handle_guacamole_data(self, instruction: GuacamoleProtocol):
        await self.send(text_data=instruction.encode())


    