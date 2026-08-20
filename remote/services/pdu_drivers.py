import requests

# 1. Klasa bazowa (Szablon)
class BasePDUDriver:
    def __init__(self, ip, credentials):
        self.ip = ip
        self.credentials = credentials

    def turn_on(self, outlet_id):
        raise NotImplementedError("Metoda turn_on musi być zaimplementowana w podklasie.")

    def turn_off(self, outlet_id):
        raise NotImplementedError("Metoda turn_off musi być zaimplementowana w podklasie.")


# 2. Konkretny sterownik dla obecnego API (To, co już napisałeś)
class RestPDUDriver(BasePDUDriver):
    def turn_on(self, outlet_id):
        url = f"http://{self.ip}:8080/api/outlet/{outlet_id}" 
        headers = {"Authorization": self.credentials}
        response = requests.post(url, json={"action": "ON"}, headers=headers, timeout=5)
        
        # 🔴 NOWA LINIJKA: Wypisze do konsoli Django dokładny powód błędu
        print(f"[DEBUG PDU] Strzał do {url} | Status: {response.status_code} | Treść: {response.text}")
        
        return response.ok
    def turn_off(self, outlet_id):
        # Używamy portu 8080 z Twojego screena
        url = f"http://{self.ip}:8080/api/outlet/{outlet_id}"
        headers = {"Authorization": self.credentials}
        response = requests.post(url, json={"action": "OFF"}, headers=headers, timeout=5)
        print(f"[DEBUG PDU] Strzał do {url} | Status: {response.status_code} | Treść: {response.text}")
        return response.ok
  
    def get_status(self, outlet_id):
        url = f"http://{self.ip}:8080/api/outlet/{outlet_id}"
        headers = {"Authorization": self.credentials} # <-- TO JEST KLUCZOWE!
        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.ok:
                data = response.json()
                state = data.get('state', 'OFF')
                return str(state).upper()
            else:
                return None # Jeśli Flask zwróci 404 lub 401, zwracamy None
        except Exception as e:
            print(f"[DEBUG STATUS ERROR] {e}")
            return None
 
# 3. Zaślepka dla przyszłego SNMP (gotowa na rozbudowę)
class SNMPPDUDriver(BasePDUDriver):
    def turn_off(self, outlet_id):
        # Tutaj w przyszłości wyląduje biblioteka pysnmp
        oid = f"1.3.6.1.4.1.318.1.1.4.4.2.1.3.{outlet_id}"
        print(f"[SNMP] Symulacja wysłania komendy OFF do {self.ip} na port {outlet_id}")
        return True