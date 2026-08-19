# BackendRemoteLab

Zdalny dostęp do maszyn laboratoryjnych przez przeglądarkę — Django + Apache Guacamole + Vite.

## Wymagania

- Python 3.10+
- Node.js 18+
- Docker (do uruchomienia guacd, i maszyn testowych)

## Uruchomienie

### 1. guacd (Apache Guacamole daemon)

* **a)Uruchomienie samego kontenera
```bash
docker run -d --name guacd -p 4822:4822 guacamole/guacd:latest
```

* **b)Uruchomienie całego test bencha
```bash
docker compose up -d
```

### 2. Backend (Django)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Backend nasłuchuje na `http://0.0.0.0:8000`.

### 3. Frontend (Vite)

```bash
cd frontend
npm install
npm run dev -- --host
```

Frontend nasłuchuje na `http://0.0.0.0:5173` i proxyuje WebSocket do Django.

## Architektura

```
Przeglądarka (guacamole-common-js)
    ↕ WebSocket (ws://localhost:5173/ws/guacamole/)
Vite dev proxy
    ↕ WebSocket (ws://localhost:8000/ws/guacamole/)
Django Channels (GuacamoleConsumer)
    ↕ TCP (127.0.0.1:4822)
guacd (Docker)
    ↕ SSH/VNC/RDP
Maszyna docelowa
```
