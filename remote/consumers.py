import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .protocol import encode, decode

class GuacamoleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept(subprotocol='guacamole')
        self.guacd_reader, self.guacd_writer = await asyncio.open_connection('127.0.0.1', 4822)
        self.guacd_writer.write(encode("select", ["ssh"]).encode('utf-8'))
        await self.guacd_writer.drain()
        self.pump_task = asyncio.create_task(self.pump_tcp_to_ws())



    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass

    async def pump_tcp_to_ws(self):
        buffer = ""

        while True:
            data = await self.guacd_reader.read(4096)
            if not data:
                print("Connection closed by server")
                break
        
            buffer += data.decode('utf-8')

            while ";" in buffer:
                idx = buffer.find(";")
                message = buffer[:idx+1]
                buffer = buffer[idx+1:]
                await self.send(text_data=message)
                
                
                

        
        