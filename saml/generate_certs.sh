#!/bin/bash

# Dynamicznie pobierz katalog, w którym leży ten skrypt:
CERTS_DIR="$(dirname "$0")/certs"

# Upewnij się, że katalog istnieje:
mkdir -p "$CERTS_DIR"

openssl req -x509 \
    -newkey rsa:2048 \
    -keyout "$CERTS_DIR/sp.key" \
    -out "$CERTS_DIR/sp.crt" \
    -days 3650 \
    -nodes \
    -subj "/C=PL/O=Uczelnia/CN=remotelab.local"

# Uprawnienia spójne ze ścieżką:
chmod 600 "$CERTS_DIR/sp.key"
chmod 644 "$CERTS_DIR/sp.crt"

echo "Certyfikaty SAML SP zostały pomyślnie wygenerowane w $CERTS_DIR"
