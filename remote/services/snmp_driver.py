from pysnmp.hlapi import *

class SnmpPDUDriver:
    def __init__(self, ip, credentials):
        self.ip = ip
        # W świecie SNMP hasło to tzw. Community String
        self.community = credentials 
        
        # BARDZO WAŻNE: To jest standardowy OID (adres w pamięci) dla listew firmy APC.
        # Odpowiada za odczyt/zapis stanu gniazdek (sPDUOutletControlState).
        # Jeśli na miejscu okaże się, że listwa to np. CyberPower lub Eaton, 
        # ten ciąg cyfr trzeba będzie podmienić pod ich specyfikację.
        self.base_oid = '1.3.6.1.4.1.318.1.1.4.4.2.1.3.'

    def get_status(self, port):
        """Pobiera aktualny stan gniazdka za pomocą komendy SNMP GET"""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=0), # mpModel=0 oznacza SNMPv1
                UdpTransportTarget((self.ip, 161), timeout=2.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(f"{self.base_oid}{port}"))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            # Jeśli sprzęt nie odpowiada (np. złe IP, złe hasło)
            if errorIndication or errorStatus:
                print(f"[SNMP GET ERROR] {errorIndication or errorStatus}")
                return None
                
            # Parsowanie odpowiedzi z listwy
            for name, val in varBinds:
                value = int(val)
                # W listwach APC wartość 1 oznacza ON, a 2 oznacza OFF
                return 'ON' if value == 1 else 'OFF'
                
            return None
        except Exception as e:
            print(f"[SNMP CRITICAL] {str(e)}")
            return None

    def turn_on(self, port):
        # Wysłanie komendy SET z wartością 1 (ON)
        return self._set_port(port, 1)

    def turn_off(self, port):
        # Wysłanie komendy SET z wartością 2 (OFF)
        return self._set_port(port, 2)

    def _set_port(self, port, state_value):
        """Wysyła polecenie zmiany stanu gniazdka za pomocą komendy SNMP SET"""
        try:
            iterator = setCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=0),
                UdpTransportTarget((self.ip, 161), timeout=2.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(f"{self.base_oid}{port}"), Integer(state_value))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication or errorStatus:
                print(f"[SNMP SET ERROR] {errorIndication or errorStatus}")
                return False
                
            return True
        except Exception as e:
            print(f"[SNMP SET CRITICAL] {str(e)}")
            return False