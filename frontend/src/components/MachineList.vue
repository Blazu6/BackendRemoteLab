<template>
  <div class="machine-list">
    <h2>Zapisane Serwery</h2>
    
    <div v-if="loading" class="loading">Ładowanie maszyn...</div>
    <div v-else-if="machines.length === 0" class="empty">
      Brak zapisanych serwerów. Dodaj nowy z lewej strony.
    </div>
    
    <div v-else class="grid">
      <div 
        v-for="machine in machines" 
        :key="machine.id"
        class="machine-card"
        @click="$emit('connect', machine)"
      >
        <div class="machine-header">
          <span class="protocol-badge" :class="machine.protocol">{{ machine.protocol.toUpperCase() }}</span>
          <h3>{{ machine.name }}</h3>
          <button class="delete-btn" @click.stop="deleteMachine(machine.id!)" title="Usuń serwer">🗑️</button>
        </div>
        <div class="machine-details">
          <span>{{ machine.hostname }}:{{ machine.port }}</span>
          <span v-if="machine.username" class="user">👤 {{ machine.username }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { ConnectionConfig } from '../composables/useGuacamole';

const emit = defineEmits<{
  (e: 'connect', config: ConnectionConfig): void
}>();

const machines = ref<ConnectionConfig[]>([]);
const loading = ref(true);

const fetchMachines = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/machines/');
    if (res.ok) {
      machines.value = await res.json();
    } else {
      console.error('Błąd pobierania maszyn', res.status);
    }
  } catch (err) {
    console.error('Błąd sieci:', err);
  } finally {
    loading.value = false;
  }
};

const deleteMachine = async (id: number) => {
  if (!confirm('Czy na pewno chcesz usunąć ten serwer?')) return;
  
  try {
    const res = await fetch(`/api/machines/${id}/`, {
      method: 'DELETE'
    });
    if (res.ok) {
      // Odśwież listę po usunięciu
      fetchMachines();
    } else {
      alert('Nie udało się usunąć serwera.');
    }
  } catch (err) {
    alert('Błąd sieci podczas usuwania.');
  }
};

onMounted(() => {
  fetchMachines();
});

defineExpose({
  fetchMachines
});
</script>

<style scoped>
.machine-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.machine-list h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #89b4fa;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.machine-card {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 10px;
  padding: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
}

.machine-card:hover {
  border-color: #89b4fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.machine-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.machine-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #cdd6f4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1; /* Pozwala tytułowi zająć resztę miejsca i zepchnąć przycisk kosza na prawo */
}

.delete-btn {
  background: transparent;
  border: none;
  color: #f38ba8;
  cursor: pointer;
  padding: 0.2rem;
  border-radius: 4px;
  opacity: 0.6;
  transition: all 0.2s;
}

.delete-btn:hover {
  opacity: 1;
  background: rgba(243, 139, 168, 0.15);
}

.protocol-badge {
  font-size: 0.65rem;
  font-weight: bold;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  color: #11111b;
}
.protocol-badge.ssh { background: #a6e3a1; }
.protocol-badge.rdp { background: #89b4fa; }
.protocol-badge.vnc { background: #f9e2af; }

.machine-details {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #a6adc8;
}

.user {
  font-size: 0.8rem;
  color: #9399b2;
}

.loading, .empty {
  color: #9399b2;
  font-size: 0.9rem;
  padding: 1rem;
  text-align: center;
  background: #1e1e2e;
  border-radius: 8px;
  border: 1px dashed #45475a;
}
</style>
