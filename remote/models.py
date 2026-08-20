from django.db import models

class Machine(models.Model):
    name = models.CharField(max_length=100, help_text="Nazwa przyjazna dla użytkownika (np. Główny Serwer)")
    protocol = models.CharField(max_length=10)
    hostname = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.protocol}://{self.hostname})"

class PDU(models.Model):
    ip_address = models.CharField(max_length=50, unique=True)
    protocol = models.CharField(max_length=50, default='REST_JSON')
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