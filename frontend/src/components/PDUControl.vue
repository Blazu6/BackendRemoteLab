<template>
  <div class="pdu-control">
    <h2>⚡ Zarządzanie Zasilaniem (PDU)</h2>
    
    <!-- Panel dodawania listwy -->
    <div class="add-pdu-panel">
      <h3>Dodaj nową listwę (Poligon)</h3>
      <div class="form-row">
        <input 
          v-model="newPduIp" 
          type="text" 
          placeholder="Adres IP (np. 192.168.1.45)" 
          class="input-field"
        />
        <!-- NOWE POLE NA HASŁO -->
        <input 
          v-model="newPduCredentials" 
          type="password" 
          placeholder="Hasło listwy" 
          class="input-field"
        />
        <select v-model="newPduProtocol" class="input-field">
          <option value="REST_JSON">REST API (JSON)</option>
          <option value="SNMP_V1">SNMP v1/v2</option>
        </select>
        <button class="btn btn-primary" @click="saveNewPdu">DODAJ</button>
      </div>
    </div>

    <hr class="divider" />

    <!-- Lista dodanych listew i porty -->
    <div class="pdu-list">
      <div v-if="pdus.length === 0" class="empty-state">
        Brak dodanych listew. Wpisz IP, hasło i kliknij DODAJ.
      </div>

      <div v-for="pdu in pdus" :key="pdu.ip" class="pdu-card">
        <div class="pdu-header">
          <div class="pdu-title-info">
            <h3>Listwa: {{ pdu.ip }}</h3>
            
            <!-- Wskaźnik stanu gniazdek (kropki) w nagłówku -->
            <div class="header-status-dots" v-if="pduStatuses[pdu.ip]">
              <div v-for="(state, port) in pduStatuses[pdu.ip]" :key="port" class="mini-dot-wrapper" :title="`${pduNames[pdu.ip]?.[Number(port)] || 'Gniazdko ' + port}: ${state}`">
                <span class="mini-num">{{ port }}</span>
                <span class="dot" :class="state === 'ON' ? 'dot-on' : 'dot-off'"></span>
              </div>
            </div>
          </div>

          <!-- Prawa strona nagłówka: Badget oraz guzik USUŃ -->
          <div class="header-actions">
            <span class="badge">{{ pdu.protocol }}</span>
            <button class="btn btn-danger" @click="deletePdu(pdu.ip)">USUŃ</button>
          </div>
        </div>
        
        <!-- Dynamiczna siatka portów na podstawie pobranych stanów -->
        <div class="ports-grid" v-if="pduStatuses[pdu.ip]">
          <div v-for="(state, port) in pduStatuses[pdu.ip]" :key="port" class="port-item">
            <!-- Edytowalna nazwa gniazdka -->
            <input 
              type="text" 
              v-model="pduNames[pdu.ip][Number(port)]" 
              @change="saveOutletName(pdu.ip, Number(port), pduNames[pdu.ip][Number(port)])"
              class="outlet-name-input"
              :placeholder="`Gniazdko ${port}`"
            />
            <div class="port-actions">
              <button class="btn btn-on" @click="togglePower(pdu, Number(port), 'ON')">ON</button>
              <button class="btn btn-off" @click="togglePower(pdu, Number(port), 'OFF')">OFF</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface PDU {
  ip: string;
  protocol: string;
}

const newPduIp = ref('');
const newPduProtocol = ref('REST_JSON');
const newPduCredentials = ref(''); // ZMIANA: Dodano ref dla hasła
const pdus = ref<PDU[]>([]);

const pduStatuses = ref<Record<string, Record<number, string>>>({});
const pduNames = ref<Record<string, Record<number, string>>>({});
let pollInterval: number | null = null;

const fetchPdus = async () => {
  try {
    const res = await fetch('/api/pdu/');
    const data = await res.json();
    if (data.status === 'success') {
      pdus.value = data.data;
      await fetchAllStatuses();
    }
  } catch (err) {
    console.error("Błąd pobierania listew:", err);
  }
};

const fetchAllStatuses = async () => {
  for (const pdu of pdus.value) {
    try {
      const res = await fetch(`/api/pdu/?ip=${pdu.ip}`);
      const data = await res.json();
      if (data.status === 'success') {
        
        if (!pduNames.value[pdu.ip]) {
          pduNames.value[pdu.ip] = {};
        }
        
        if (data.names) {
          for (const port in data.names) {
            if (pduNames.value[pdu.ip][port] === undefined) {
              pduNames.value[pdu.ip][port] = data.names[port];
            }
          }
        }

        pduStatuses.value[pdu.ip] = data.statuses;
      }
    } catch (err) {
      console.error(`Błąd statusu dla ${pdu.ip}:`, err);
    }
  }
};

onMounted(() => {
  fetchPdus();
  pollInterval = window.setInterval(fetchAllStatuses, 7000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});

const saveNewPdu = async () => {
  if (!newPduIp.value) return alert("Podaj adres IP listwy!");
  
  try {
    const res = await fetch('/api/pdu/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ip_address: newPduIp.value,
        protocol: newPduProtocol.value,
        credentials: newPduCredentials.value // ZMIANA: Wysłanie hasła w paczce JSON
      })
    });
    
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      newPduIp.value = '';
      newPduCredentials.value = ''; // ZMIANA: Czyszczenie pola z hasłem po dodaniu
      await fetchPdus();
    } else {
      alert(`Błąd zapisu: ${data.message}`);
    }
  } catch (error) {
    console.error("Błąd sieci:", error);
  }
};

const saveOutletName = async (ip: string, port: number, newName: string) => {
  try {
    const res = await fetch('/api/pdu/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'rename',
        ip_address: ip,
        outlet: port,
        name: newName || ''
      })
    });
    const data = await res.json();
    
    if (res.ok && data.status === 'success') {
      console.log(`Zapisano pomyślnie nazwę: ${newName}`);
    } else {
      console.error("Nie udało się zapisać nazwy gniazdka:", data.message);
      alert("Błąd zapisu nazwy gniazdka!");
    }
  } catch (error) {
    console.error("Błąd sieci przy zapisie nazwy:", error);
  }
};

const deletePdu = async (ip: string) => {
  if (!confirm(`Czy na pewno chcesz usunąć listwę ${ip}?`)) return;

  try {
    const res = await fetch('/api/pdu/', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_address: ip })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      delete pduStatuses.value[ip];
      delete pduNames.value[ip];
      await fetchPdus();
    } else {
      alert(`Błąd usuwania: ${data.message}`);
    }
  } catch (error) {
    console.error("Błąd sieci podczas usuwania:", error);
    alert("Brak połączenia z backendem.");
  }
};

const togglePower = async (pdu: PDU, port: number, action: string) => {
  try {
    const res = await fetch('/api/pdu/', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ip_address: pdu.ip,
        protocol: pdu.protocol,
        outlet: port,
        action: action
      })
    });
    
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      await fetchAllStatuses();
    } else {
      alert(`Odmowa: ${data.message || 'Sprawdź logi Django'}`);
    }
  } catch (error) {
    console.error("Błąd sieci:", error);
  }
};
</script>

<style scoped>
.pdu-control {
  padding: 2rem;
  background: #1e1e2e;
  border-radius: 12px;
  color: #cdd6f4;
  border: 1px dashed #585b70;
  max-width: 900px;
}
.pdu-control h2 {
  color: #f9e2af;
  margin-top: 0;
  margin-bottom: 2rem;
}
.add-pdu-panel {
  background: #181825;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}
.form-row {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}
.input-field {
  padding: 0.75rem;
  background: #313244;
  border: 1px solid #45475a;
  color: #cdd6f4;
  border-radius: 6px;
  flex: 1;
}
.pdu-card {
  background: #181825;
  border: 1px solid #313244;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.pdu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #313244;
  padding-bottom: 0.5rem;
}
.pdu-title-info {
  display: flex;
  align-items: center;
  gap: 2rem;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.header-status-dots {
  display: flex;
  gap: 0.75rem;
  background: #181825;
  padding: 0.3rem 0.8rem;
  border-radius: 6px;
  border: 1px solid #313244;
}
.mini-dot-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 0.7rem;
  color: #a6adc8;
}
.mini-num {
  margin-bottom: 2px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.dot-on {
  background-color: #a6e3a1;
  box-shadow: 0 0 6px #a6e3a1;
}
.dot-off {
  background-color: #f38ba8;
}
.badge {
  background: #89b4fa;
  color: #11111b;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: bold;
}
.btn-danger {
  background: #f38ba8;
  color: #11111b;
  padding: 0.25rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: bold;
  cursor: pointer;
}
.btn-danger:hover {
  opacity: 0.85;
}
.ports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 1rem;
}
.port-item {
  background: #313244;
  padding: 1rem;
  border-radius: 6px;
  text-align: center;
}
.outlet-name-input {
  width: 100%;
  padding: 0.4rem;
  margin-bottom: 0.75rem;
  background: #181825;
  border: 1px solid #45475a;
  color: #cdd6f4;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
  font-size: 0.9rem;
}
.outlet-name-input:focus {
  border-color: #89b4fa;
  outline: none;
}
.port-actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}
.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
}
.btn-primary { background: #89b4fa; color: #11111b; }
.btn-on { background: #a6e3a1; color: #11111b; }
.btn-off { background: #f38ba8; color: #11111b; }
.empty-state { text-align: center; color: #a6adc8; padding: 2rem; }
.divider { border: 0; height: 1px; background: #585b70; margin: 2rem 0; }
</style>