import asyncio
import logging
# Importujemy nasze własne klasy
from remote.client_async import AsyncGuacamoleClient

# Logi pokażą nam dokladnie instrukcje wysyłane w send_instruction
logging.basicConfig(level=logging.DEBUG)

async def print_incoming_instruction(instruction):
    # Wykorzystujemy nasz obiekt GuacamoleProtocol
    print(f"📥 [CALLBACK] Opcode: {instruction.opcode} | Args: {instruction.args}")

async def main():
    client = AsyncGuacamoleClient(
        guacd_host="127.0.0.1",
        guacd_port=4822,
        on_instruction=print_incoming_instruction
    )

    print("🔌 Otwieranie gniazda...")
    await client.open()

    print("🤝 Wywoływanie naszej metody handshake()...")
    await client.handshake(
        protocol="ssh",
        hostname="172.17.0.1",
        port="22",
        username="blazu",
        password="4268",
    )

    # Utrzymujemy pętlę przez 3 sekundy, aby odebrać pierwsze ramki
    await asyncio.sleep(3)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())