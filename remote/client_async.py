import asyncio
import enum
import logging
from typing import Callable, Any, Optional

from .protocol import GuacamoleProtocol, INST_TERM

PROTOCOLS = ('vnc', 'rdp', 'ssh')

class GuacamoleClientPhase(enum.Enum):
    DISCONNECTED = 0
    HANDSHAKE = 1
    CONNECTED = 2

class AsyncGuacamoleClient:
    def __init__(self, guacd_host: str, guacd_port: int, on_instruction: Callable[[GuacamoleProtocol], Any]):
        self._logger = logging.getLogger(f"guacamole.client")

        self._guacd_host = guacd_host
        self._guacd_port = guacd_port

        self._id = None
        self._state = GuacamoleClientPhase.DISCONNECTED

        self.on_instruction = on_instruction

        self._handshake_queue = asyncio.Queue(maxsize=512)

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

        self._read_task: Optional[asyncio.Task] = None

    @property
    def state(self) -> GuacamoleClientPhase:
        return self._state

    @property
    def id(self) -> str:
        return self._id

    async def _receive(self):
        buffer = ""

        while True:
            data = await self.reader.read(4096)
            if not data:
                self._logger.info("Connection closed by guacd")
                break

            buffer += data.decode('utf-8')

            while INST_TERM in buffer:
                line, buffer = buffer.split(INST_TERM, 1)

                instruction = GuacamoleProtocol.decode(line + INST_TERM, check_terminator=False)

                if self.state == GuacamoleClientPhase.CONNECTED:
                    try:
                        await self.on_instruction(instruction)
                    except Exception as e:
                        self._logger.warning(f"Failed to forward instruction to WebSocket client: {e}")
                        return
                else:
                    await self._handshake_queue.put(instruction)

    async def open(self):
        if self.reader or self.writer:
            self._logger.warning("Tried to call open() on a connection that is already open")
            return

        self.reader, self.writer = await asyncio.open_connection(self._guacd_host, self._guacd_port)
        self._read_task = asyncio.create_task(self._receive())

    async def close(self):
        self._logger.info("Closing connection")

        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        self._read_task = None
        self.writer = None
        self.reader = None

    async def send_raw(self, data: str):
        if not self.writer:
            raise IOError("Transport is not open")
        self.writer.write(data.encode("utf-8"))
        

    async def send_instruction(self, instruction: GuacamoleProtocol):
        self._logger.debug(f'Sending instruction: {instruction}')
        await self.send_raw(instruction.encode())


    async def _handshake_wait_instruction(self, opcode) -> GuacamoleProtocol:
        self._logger.debug(f'Waiting for instruction \"{opcode}\"')

        instruction = await self._handshake_queue.get()

        if not instruction:
            raise ValueError(f"Cannot establish Handshake, \"{opcode}\" instruction not received")

        if instruction.opcode != opcode:
            raise ValueError(f"Cannot establish Handshake. Expecting \"{opcode}\" instruction, received \"{instruction.opcode}\" instead.")

        return instruction

    async def handshake(self, protocol='vnc', width=1024, height=768, dpi=96, audio=None, video=None, image=None, **kwargs):
        if protocol not in PROTOCOLS and 'connectionid' not in kwargs:
            raise ValueError('Cannot start Handshake, missing/invalid protocol without connectionid')

        self._state = GuacamoleClientPhase.HANDSHAKE

        # If connectionid is provided - connect to existing connectionid
        if 'connectionid' in kwargs:
            await self.send_instruction(GuacamoleProtocol('select', kwargs.get('connectionid')))
        else:
            await self.send_instruction(GuacamoleProtocol('select', protocol))

        try:
            args_instruction = await self._handshake_wait_instruction("args")
        except ValueError as e:
            self._logger.error("Handshake failed", exc_info=e)
            await self.close()
            raise e

        await self.send_instruction(GuacamoleProtocol('size', width, height, dpi))
        await self.send_instruction(GuacamoleProtocol('audio', *([] if audio is None else audio)))
        await self.send_instruction(GuacamoleProtocol('video', *([] if video is None else video)))
        await self.send_instruction(GuacamoleProtocol('image', *([] if image is None else image)))

        connection_args = [
            kwargs.get(argument.replace('-', '_'), '') for argument in args_instruction.args
        ]
        await self.send_instruction(GuacamoleProtocol('connect', *connection_args))

        try:
            ready_instruction = await self._handshake_wait_instruction("ready")
        except ValueError as e:
            self._logger.error("Handshake failed", exc_info=e)
            await self.close()
            raise e

        if ready_instruction.args:
            self._id = ready_instruction.args[0]
            self._logger.info(f"Established connection with client id: {self.id}")

        self._logger.info('Handshake completed')
        self._state = GuacamoleClientPhase.CONNECTED
