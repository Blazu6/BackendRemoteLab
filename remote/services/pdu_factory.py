from .pdu_drivers import RestPDUDriver
from .snmp_driver import SnmpPDUDriver  # Używamy naszego prawdziwego sterownika SNMP

# Słownik mapujący nazwy protokołów z bazy danych na konkretne klasy sterowników
DRIVER_MAPPING = {
    'REST_JSON': RestPDUDriver,
    'SNMP_V1': SnmpPDUDriver,  # Mapujemy na prawdziwą klasę z pliku snmp_driver.py
}

def get_pdu_driver(pdu_instance):
    """
    Zwraca odpowiednią instancję sterownika na podstawie konfiguracji listwy.
    Wykorzystuje słownik do dynamicznego dobierania klas.
    """
    driver_class = DRIVER_MAPPING.get(pdu_instance.protocol)
    
    if not driver_class:
        raise ValueError(f"Nieobsługiwany protokół komunikacji: {pdu_instance.protocol}")
        
    # Tworzymy i zwracamy obiekt wybranego sterownika, przekazując IP i hasło
    return driver_class(pdu_instance.ip_address, pdu_instance.credentials)