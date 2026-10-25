#This is build to have column that can be encrypted do not store passwords in plain text in db

import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

def get_fernet():
    #this funciton is to prepare key to the format that fernet requires
    key_32_bytes = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    fernet_key = base64.urlsafe_b64encode(key_32_bytes)
    return Fernet(fernet_key)

class EncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        if value is None:
            return None
        else:
            fernet = get_fernet()
            encrypted_bytes = fernet.encrypt(str(value).encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def from_db_value(self, value, expresssion, connection):
        if value is None:
            return None
        else:
            fernet = get_fernet()
            decrypted_bytes = fernet.decrypt(value.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
