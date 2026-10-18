#!/bin/bash
# ===========================================================================
# Generowanie certyfikatów dla SAML Service Provider (SP)
#
# Uruchom ONE RAZ przed pierwszym startem aplikacji:
#   chmod +x saml/generate_certs.sh
#   ./saml/generate_certs.sh
#
# Pliki sp.crt i sp.key NIGDY nie wchodzą do repozytorium!
# Plik sp.crt (klucz publiczny) wysyłasz do działu IT uczelni przy rejestracji SP.
# ===========================================================================

CERTS_DIR="$(dirname "$0")/certs"
mkdir -p "$CERTS_DIR"

echo "Generuję certyfikat SP RSA-2048, ważny 10 lat..."

openssl req -x509 \
    -newkey rsa:2048 \
    -keyout "$CERTS_DIR/sp.key" \
    -out    "$CERTS_DIR/sp.crt" \
    -days   3650 \
    -nodes \
    -subj "/C=PL/ST=Wielkopolska/L=Poznan/O=Uczelnia/OU=RemoteLab/CN=remotelab.uczelnia.pl"

chmod 600 "$CERTS_DIR/sp.key"
chmod 644 "$CERTS_DIR/sp.crt"

echo ""
echo "Gotowe! Pliki:"
echo "  $CERTS_DIR/sp.key  (klucz prywatny — NIGDY nie udostępniaj)"
echo "  $CERTS_DIR/sp.crt  (certyfikat publiczny — wyślij do IT uczelni)"
echo ""
echo "Zawartość certyfikatu (do wklejenia w formularzu rejestracji SP):"
echo "---"
cat "$CERTS_DIR/sp.crt"
