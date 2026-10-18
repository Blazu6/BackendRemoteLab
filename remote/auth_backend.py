"""
Backend autentykacji łączący EduGAIN (SAML2) z LDAP.

Przepływ:
  1. djangosaml2 weryfikuje asercję SAML i wywołuje ten backend
  2. Ten backend tworzy/aktualizuje użytkownika Django na podstawie
     atrybutów z asercji (email, imię, nazwisko)
  3. Następnie odpytuje LDAP o grupy tego użytkownika
  4. Synchronizuje grupy LDAP z grupami Django (→ uprawnienia)

Jeśli użytkownik nie ma żadnej grupy w LDAP, dostęp jest blokowany.
"""
import logging
from djangosaml2.backends import Saml2Backend
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class EduGainLdapBackend(Saml2Backend):
    """
    Rozszerza Saml2Backend o synchronizację grup z LDAP.

    Konfiguracja w settings.py:
      SAML_USE_NAME_ID_AS_USERNAME = False
      SAML_ATTRIBUTE_MAPPING = { 'eduPersonPrincipalName': ('username',), ... }
      AUTH_LDAP_* — standardowe ustawienia django-auth-ldap
      SAML_LDAP_SYNC_GROUPS = True  (domyślnie True)
    """

    def authenticate(self, request, session_info=None, attribute_mapping=None, **kwargs):
        """
        Wywoływane przez djangosaml2 po pomyślnej weryfikacji asercji SAML.
        """
        user = super().authenticate(
            request,
            session_info=session_info,
            attribute_mapping=attribute_mapping,
            **kwargs,
        )

        if user is None:
            logger.warning("SAML authentication failed — super().authenticate() returned None")
            return None

        logger.info(f"SAML login: {user.username} ({user.email})")

        # Synchronizacja grup z LDAP (jeśli włączone w settings)
        from django.conf import settings
        if getattr(settings, 'SAML_LDAP_SYNC_GROUPS', True):
            self._sync_ldap_groups(user)

        return user

    def _sync_ldap_groups(self, user):
        """
        Odpytuje LDAP o grupy użytkownika i synchronizuje je z Django groups.

        Używa django-auth-ldap pod spodem — wywołuje metodę populate_user()
        która uaktualnia flagi is_staff, is_superuser oraz grupy.
        """
        try:
            from django_auth_ldap.backend import LDAPBackend
            ldap_backend = LDAPBackend()

            # Tworzymy obiekt LDAPUser dla tego użytkownika
            ldap_user = ldap_backend.get_user(user.pk)
            if ldap_user is not None:
                # Wymusza ponowne pobranie grup z LDAP i zapis do Django
                ldap_user.ldap_user._mirror_groups()
                logger.info(
                    f"LDAP groups synced for {user.username}: "
                    f"{list(user.groups.values_list('name', flat=True))}"
                )
            else:
                logger.warning(
                    f"User {user.username} not found in LDAP — no groups assigned. "
                    f"Check LDAP_URI and user DN configuration."
                )
        except Exception as e:
            # Nie blokujemy logowania jeśli LDAP nie odpowiada —
            # użytkownik dostanie się, ale bez grup (brak uprawnień do zasobów)
            logger.error(f"LDAP group sync failed for {user.username}: {e}")

    def is_authorized(self, attributes, attribute_mapping, idp_entityid, **kwargs):
        """
        Opcjonalna weryfikacja atrybutów SAML przed utworzeniem użytkownika.
        Odrzuca użytkowników których uczelnia nie przekazała wymaganego atrybutu.
        """
        eppn = attributes.get('eduPersonPrincipalName', [])
        if not eppn:
            logger.warning(f"Rejected SAML login — missing eduPersonPrincipalName from {idp_entityid}")
            return False
        return True
