from lab.fields import EncryptedCharField

def test_encrypted_char_field_encrypts_and_decrypts():
    field = EncryptedCharField()
    raw_secret = "tajne_haslo_laboratorium_123"
    encrypted = field.get_prep_value(raw_secret)
    assert encrypted != raw_secret
    assert encrypted.startswith("gAAAAA")
    decrypted = field.from_db_value(encrypted, None, None)
    assert decrypted == raw_secret

def test_encrypted_char_field_handles_none():
    field = EncryptedCharField()
    assert field.get_prep_value(None) is None
    assert field.from_db_value(None, None, None) is None
