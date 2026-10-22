# RemoteLab v2 — Backend

System zdalnego dostępu do maszyn laboratoryjnych i sterowania infrastrukturą badawczą przez przeglądarkę (Praca magisterska).

## 🛠️ Stack technologiczny
- **Backend:** Django 5.x + ASGI (Daphne / Django Channels)
- **Zdalny dostęp:** Apache Guacamole (`guacd`) — SSH / VNC / RDP
- **Uwierzytelnianie:** SAML2 (EduGAIN) + LDAP (grupy uczelniane)
- **Testy i QA:** `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`
- **Infrastruktura:** Docker / Docker Compose (docelowo k3s)

---

## 🚀 Szybki start (Środowisko lokalne)

### 1. Wymagania wstępne
- Python 3.10+
- Git

### 2. Przygotowanie środowiska
```bash
# 1. Klonowanie repozytorium i przejście do katalogu
cd BackendRemoteLab

# 2. Utworzenie i aktywacja wirtualnego środowiska
python3 -m venv venv
source venv/bin/activate

# 3. Instalacja zależności
pip install -r requirements.txt
```

### 3. Konfiguracja zmiennych środowiskowych
Skopiuj szablon konfiguracji i uzupełnij klucze:
```bash
cp .env.example .env
```
Upewnij się, że w pliku `.env` ustawiłeś unikalny `SECRET_KEY`.

### 4. Uruchomienie testów
```bash
pytest
```
Uruchomienie testów z raportem pokrycia kodu:
```bash
pytest --cov=lab --cov-report=term-missing
```

### 5. Start serwera deweloperskiego
```bash
python manage.py runserver
```
Serwer domyślnie nasłuchuje na `http://127.0.0.1:8000/`.
