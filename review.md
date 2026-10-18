# Przegląd Architektury — BackendRemoteLab
## Integracja EduGAIN (SAML2) + LDAP + System ról

> **Stack:** Django 5.x + Channels + Daphne + djangosaml2 + PySAML2 + xmlsec1 + django-auth-ldap + Vue 3

---

## 1. Obecna architektura (po zmianach)

```
Przeglądarka (Vue 3 + guacamole-common-js)
    ↕  WebSocket / REST  (HTTPS/WSS przez Nginx)
Django + Daphne (ASGI, port 8000)
    ├── /saml/*          → djangosaml2 (login, acs, logout, metadata)
    ├── /api/token/      → JWT (djangorestframework-simplejwt)
    ├── /api/machines/   → REST API (IsAuthenticated)
    ├── /api/pdu/        → REST API (IsAuthenticated)
    ├── /api/documents/  → REST API (IsAuthenticated)
    └── /ws/guacamole/   → GuacamoleConsumer (WebSocket)
         ↕  TCP 4822
        guacd (Docker)
         ↕  SSH / VNC / RDP
        Maszyny laboratoryjne
```

---

## 2. Przepływ uwierzytelniania

```
Użytkownik
  │
  ▼
GET /saml/login/
  │ (djangosaml2 buduje AuthnRequest + podpisuje kluczem SP)
  ▼
Redirect → IdP uczelni (Shibboleth / USOS / EduGAIN)
  │
  ▼  użytkownik loguje się uczelnianymi danymi
  │
POST /saml/acs/  ← IdP odsyła podpisaną asercję SAML2
  │
  ▼
EduGainLdapBackend.authenticate()
  ├── PySAML2 weryfikuje podpis IdP (xmlsec1)
  ├── Mapuje atrybuty SAML → pola User Django
  │       eduPersonPrincipalName → username
  │       mail → email, givenName → first_name, sn → last_name
  ├── Tworzy/aktualizuje rekord User w Django
  └── _sync_ldap_groups()
        ├── Odpytuje LDAP o grupy użytkownika
        └── AUTH_LDAP_MIRROR_GROUPS=True → synchronizuje Django groups
  │
  ▼
Użytkownik zalogowany (sesja Django)
  │
  ▼
Redirect → LOGIN_REDIRECT_URL = '/'
```

---

## 3. Pliki zmienione / dodane

| Plik | Zmiana |
|------|--------|
| [`Dockerfile`](file:///home/blazu/Desktop/BackendRemoteLab/Dockerfile) | Dodano: `xmlsec1`, `libxmlsec1-dev`, `libxmlsec1-openssl`, `libldap2-dev`, `libsasl2-dev`, `pkg-config` |
| [`requirements.txt`](file:///home/blazu/Desktop/BackendRemoteLab/requirements.txt) | Dodano: `djangosaml2`, `pysaml2`, `django-auth-ldap`, `ldap3`, `djangorestframework`, `djangorestframework-simplejwt` |
| [`core/settings.py`](file:///home/blazu/Desktop/BackendRemoteLab/core/settings.py) | Dodano: `djangosaml2`, `rest_framework` w INSTALLED_APPS; `SamlSessionMiddleware`; bloki LDAP, SAML_CONFIG, DRF, JWT |
| [`core/urls.py`](file:///home/blazu/Desktop/BackendRemoteLab/core/urls.py) | Dodano: `path('saml/', include('djangosaml2.urls'))`, endpointy JWT |
| [`remote/auth_backend.py`](file:///home/blazu/Desktop/BackendRemoteLab/remote/auth_backend.py) | **NOWY** — `EduGainLdapBackend` łączący SAML2 + LDAP |
| [`saml/generate_certs.sh`](file:///home/blazu/Desktop/BackendRemoteLab/saml/generate_certs.sh) | **NOWY** — skrypt generujący certyfikaty SP |
| [`saml/idp_metadata.xml.placeholder`](file:///home/blazu/Desktop/BackendRemoteLab/saml/idp_metadata.xml.placeholder) | **NOWY** — opis gdzie wrzucić metadane IdP |
| [`.gitignore`](file:///home/blazu/Desktop/BackendRemoteLab/.gitignore) | Dodano: `saml/certs/sp.key`, `saml/certs/sp.crt`, `saml/idp_metadata.xml` |

---

## 4. Co jeszcze musisz zrobić (TODO)

### Krok 1 — Zainstaluj zależności systemowe (lokalnie)

```bash
sudo apt-get install -y libldap2-dev libsasl2-dev libxmlsec1-dev pkg-config xmlsec1
```

### Krok 2 — Zainstaluj pakiety Python

```bash
source venv/bin/activate
pip install djangosaml2 pysaml2 django-auth-ldap ldap3 \
            djangorestframework djangorestframework-simplejwt
```

### Krok 3 — Wygeneruj certyfikaty SP (jeden raz!)

```bash
chmod +x saml/generate_certs.sh
./saml/generate_certs.sh
```

Skrypt tworzy `saml/certs/sp.key` (prywatny, tylko Twój serwer) i `saml/certs/sp.crt` (publiczny — wyślesz do IT uczelni).

### Krok 4 — Kontakt z działem IT uczelni

Wyślij im:
- plik `saml/certs/sp.crt` (Twój certyfikat publiczny)
- URL metadanych SP: `https://TWOJ_SERWER/saml/metadata/` lub sam XML ze strony

Oni wyślą Ci:
- plik XML z metadanymi ich IdP
- listę atrybutów które będą wysyłać (skonfrontuj z `SAML_ATTRIBUTE_MAPPING`)

### Krok 5 — Wklej metadane IdP

Zapisz plik XML od IT uczelni jako `saml/idp_metadata.xml` i odkomentuj w `settings.py`:

```python
# core/settings.py — sekcja SAML_CONFIG → 'metadata'
'metadata': {
    'local': [str(BASE_DIR / 'saml' / 'idp_metadata.xml')],
    # lub zdalnie:
    # 'remote': [{'url': 'https://federacja.uczelnia.pl/metadata.xml'}],
},
```

### Krok 6 — Ustaw zmienne środowiskowe

Uzupełnij `.env` (pamiętaj że jest w `.gitignore`):

```env
SECRET_KEY=wygeneruj-nowy-klucz-django-admin-secret-key
SP_BASE_URL=https://remotelab.twojauczelnia.pl

LDAP_URI=ldap://ldap.twojauczelnia.pl
LDAP_BIND_DN=cn=serviceaccount,dc=uczelnia,dc=pl
LDAP_BIND_PASSWORD=haslo-konta-serwisowego
LDAP_USER_BASE=ou=users,dc=uczelnia,dc=pl
LDAP_GROUP_BASE=ou=groups,dc=uczelnia,dc=pl
```

### Krok 7 — Uruchom migracje

```bash
python manage.py migrate
```

### Krok 8 — Sprawdź czy działa metadata endpoint

```bash
python manage.py runserver
curl http://localhost:8000/saml/metadata/
# Powinien zwrócić XML z danymi SP
```

---

## 5. Skonfiguruj grupy LDAP dla laboratorium

W `settings.py` masz zdefiniowane grupy (`_LDAP_BASE`). Utwórz je w OpenLDAP lub poproś IT uczelni o odpowiedniki w ich AD:

| Grupa LDAP | Flaga Django | Co może robić |
|------------|-------------|----------------|
| `cn=lab_students,...` | `is_active=True` | Przeglądać i łączyć się z przypisanymi maszynami |
| `cn=lab_staff,...` | `is_active=True` | + zarządzanie dokumentami PDF |
| `cn=lab_admins,...` | `is_staff=True`, `is_superuser=True` | Pełny dostęp + panel admin |

---

## 6. Architektura komponentów

```
EduGAIN IdP uczelni
  │  SAML2 asercja (HTTP POST)
  ▼
djangosaml2  (/saml/acs/)
  │  atrybuty: eppn, mail, givenName, sn
  ▼
EduGainLdapBackend  (remote/auth_backend.py)
  │  tworzy/aktualizuje User Django
  ▼
django-auth-ldap  (_sync_ldap_groups)
  │  zapytanie LDAP: uid=jan.kowalski
  ▼
LDAP Server  (OpenLDAP / AD uczelni)
  │  zwraca: [lab_students, lab_staff]
  ▼
Django Groups + Permissions
  │  zsynchronizowane automatycznie (AUTH_LDAP_MIRROR_GROUPS=True)
  ▼
REST API / WebSocket  →  sprawdza uprawnienia przed dostępem do zasobów
```

---

## 7. Znane ograniczenia obecnej wersji

| # | Ograniczenie | Priorytet |
|---|-------------|-----------|
| 1 | Widoki REST nadal używają `@csrf_exempt` — brak sprawdzania `IsAuthenticated` | Wysoki |
| 2 | `GuacamoleConsumer` nie sprawdza czy użytkownik jest zalogowany przed `accept()` | Wysoki |
| 3 | `SECRET_KEY` nadal wpisany na stałe w `settings.py` | Krytyczny |
| 4 | SQLite zamiast PostgreSQL (wieloużytkownikowe środowisko) | Średni |
| 5 | `CHANNEL_LAYERS` używa `InMemoryChannelLayer` zamiast Redis | Średni |

> **Uwaga:** Punkty 1 i 2 możesz dodać do następnego zadania — po tym jak SAML będzie działać.
> Punkt 3 napraw od razu — przenieś `SECRET_KEY` do `.env`.

---

## 8. Jak przetestować lokalnie (bez prawdziwego IdP)

Do testów bez uczelni możesz użyć testowego IdP:

**Opcja A — docker-test-idp (najprostsze):**
```bash
docker run -p 8080:8080 \
  -e SIMPLESAMLPHP_SP_ENTITY_ID=http://localhost:8000/saml/metadata/ \
  -e SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE=http://localhost:8000/saml/acs/ \
  kristophjunge/test-saml-idp
```
Metadane IdP będą pod: `http://localhost:8080/simplesaml/saml2/idp/metadata.php`

**Opcja B — xmlsec1 smoke test:**
```bash
# Sprawdź czy xmlsec1 jest dostępne
xmlsec1 --version

# Sprawdź czy settings.py wczytuje się bez błędów
python manage.py check
```
