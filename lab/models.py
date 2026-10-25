from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from .fields import EncryptedCharField
from django.core.validators import FileExtensionValidator

# Create your models here.

class Machine(models.Model):

    class Protocol(models.TextChoices):
            SSH = 'ssh', 'SSH'
            VNC = 'vnc', 'VNC'
            RDP = 'rdp', 'RDP'
            TELNET = 'telnet', 'TELNET'



    name = models.CharField(max_length=30)
    hostname = models.CharField(max_length=255, unique=True)
    port = models.PositiveIntegerField()
    protocol = models.CharField(
            max_length=10,
            choices=Protocol.choices,
            default=Protocol.SSH,
        )
    username = models.CharField(max_length=100, null=True, blank=True)
    password = EncryptedCharField(blank = True)
    allowed_groups = models.ManyToManyField(Group, blank=True, related_name='machines')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.protocol})"

class PDU(models.Model):

    class Protocol(models.TextChoices):
            REST_JSON = 'rest', 'REST'
            SNMP = 'snmp', 'SNMP'
  

    ip_address = models.GenericIPAddressField(unique=True)
    protocol = models.CharField(
            max_length=10,
            choices=Protocol.choices,
            default=Protocol.REST_JSON
    )
    credentials = EncryptedCharField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} ({self.protocol})"

class PDUOutletMapping(models.Model):

    outlet_id = models.PositiveSmallIntegerField()
    custom_name = models.CharField(max_length=100)
    pdu = models.ForeignKey(PDU, on_delete=models.CASCADE, related_name='outlets')
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='pdu_outlets')
    

    class Meta:
        unique_together = ('pdu', 'outlet_id')

    def __str__(self):
        return f"{self.pdu.ip_address} [Port {self.outlet_id}]: {self.custom_name}"


class Document(models.Model):
    class DocType(models.TextChoices):
        STATIC = 'static', 'Static'
        INTERACTIVE = 'interactive', 'Interactive'

    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DocType.choices,
        default=DocType.STATIC,
    )
    allowed_groups = models.ManyToManyField(Group, blank=True, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.doc_type})"


class LaboratorySession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_sessions',
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    connection_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'machine']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['machine'],
                condition=models.Q(ended_at__isnull=True),
                name='unique_active_session_per_machine',
            ),
        ]


    def __str__(self):
        user_name = self.user.get_username() if self.user else "Anonymous"
        machine_name = self.machine.name if self.machine else "Deleted Machine"
        return f"Sesja: {user_name} -> {machine_name} ({self.started_at})"



