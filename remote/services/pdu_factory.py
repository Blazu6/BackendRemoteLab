from .pdu_drivers import RestPDUDriver, SNMPPDUDriver

def get_pdu_driver(pdu_instance):
    """Zwraca odpowiedni sterownik na podstawie konfiguracji listwy z bazy."""
    
    if pdu_instance.protocol == 'REST_JSON':
        return RestPDUDriver(pdu_instance.ip_address, pdu_instance.credentials)
        
    elif pdu_instance.protocol == 'SNMP_V1':
        return SNMPPDUDriver(pdu_instance.ip_address, pdu_instance.credentials)
        
    # Jeśli kiedyś dodasz nowy typ listwy, dopisujesz tutaj kolejne 'elif'
    
    else:
        raise ValueError(f"Nieobsługiwany protokół komunikacji: {pdu_instance.protocol}")