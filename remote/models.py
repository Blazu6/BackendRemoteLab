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
