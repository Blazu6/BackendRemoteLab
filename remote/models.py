import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

# --- Nasz własny silnik szyfrujący (odporny na błędy nowszych wersji Django) ---
def get_cipher():
    key = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(key))

class EncryptedCharField(models.CharField):
    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return get_cipher().decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def get_prep_value(self, value):
        if not value:
            return value
        return get_cipher().encrypt(str(value).encode('utf-8')).decode('utf-8')


# --- TWOJE MODELE ---

class Machine(models.Model):
    name = models.CharField(max_length=100, help_text="Nazwa przyjazna dla użytkownika (np. Główny Serwer)")
    protocol = models.CharField(max_length=10)
    hostname = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=100, blank=True, null=True)
    # Zgodnie z życzeniem - Machine nie tknięte!
    password = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.protocol}://{self.hostname})"

class PDU(models.Model):
    ip_address = models.CharField(max_length=50, unique=True)
    protocol = models.CharField(max_length=50, default='REST_JSON')
    
    # ZMIANA: Używamy naszego pola szyfrującego TYLKO tutaj
    credentials = EncryptedCharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ip_address

class PDUOutletMapping(models.Model):
    pdu_ip = models.CharField(max_length=50)  # Adres IP listwy
    outlet_id = models.IntegerField()         # Numer portu (np. 1, 2, 3...)
    custom_name = models.CharField(max_length=100, blank=True, default="") # Nazwa własna, np. "Toster"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pdu_ip', 'outlet_id') # Unikalna para: IP + Port

    def __str__(self):
        return f"{self.pdu_ip} [Port {self.outlet_id}] -> {self.custom_name}"