<template>
  <main class="app-layout">
    <aside class="app-sidebar" v-show="!activeSessionId">
      <div class="logo">Remote Lab 🧪</div>
      <nav class="nav-menu">
        <button 
          :class="{ active: currentView === 'machines' }" 
          @click="currentView = 'machines'"
        >
          🖥️ Zdalny Dostęp
        </button>
        <button 
          :class="{ active: currentView === 'pdu' }" 
          @click="currentView = 'pdu'"
        >
          ⚡ Zasilanie PDU
        </button>
        <button 
          :class="{ active: currentView === 'cameras' }" 
          @click="currentView = 'cameras'"
        >
          📷 Kamery
        </button>
      </nav>
    </aside>

    <div class="main-content">
      <div class="main-stage">
        
        <!-- Widok Maszyn (Istniejący) -->
        <template v-if="currentView === 'machines'">
          <div v-show="!activeSessionId" class="dashboard-container">
            <div class="form-section">
              <ConnectionForm @saved="handleSaved" />
            </div>
            <div class="list-section">
              <MachineList ref="machineListRef" @connect="handleConnect" />
            </div>
          </div>

          <!-- Aktywne sesje maszyn -->
          <RemoteSession
            v-for="session in sessions"
            :key="session.id"
            :config="session.config"
            :is-active="activeSessionId === session.id"
            ref="sessionRefs"
            @activate="activateSession(session.id)"
            @minimize="handleMinimize(session.id, $event)"
            @close="removeSession(session.id)"
          />
        </template>

        <!-- Widok PDU -->
        <div v-if="currentView === 'pdu'" class="module-container">
          <PDUControl />
        </div>

        <!-- Widok Kamer -->
        <div v-if="currentView === 'cameras'" class="module-container">
          <CameraView />
        </div>
      </div>

      <!-- Pasek zadań na zminimalizowane sesje (Dock) -->
      <div id="dock" class="dock-container" :class="{ 'has-items': hasMinimizedSessions }">
        <!-- Teleporty będą wrzucać tutaj DOM zminimalizowanych RemoteSession -->
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import ConnectionForm from './components/ConnectionForm.vue';
import MachineList from './components/MachineList.vue';
import RemoteSession from './components/RemoteSession.vue';
import PDUControl from './components/PDUControl.vue';
import CameraView from './components/CameraView.vue';
import type { ConnectionConfig } from './composables/useGuacamole';

interface SessionData {
  id: string;
  config: ConnectionConfig;
  isMinimized: boolean;
}

const currentView = ref('machines');
const sessions = ref<SessionData[]>([]);
const activeSessionId = ref<string | null>(null);
const machineListRef = ref<InstanceType<typeof MachineList> | null>(null);

const handleSaved = () => {
  machineListRef.value?.fetchMachines();
};

const hasMinimizedSessions = computed(() => {
  return sessions.value.some(s => s.isMinimized);
});

const handleConnect = (config: ConnectionConfig) => {
  const id = `session-${Date.now()}`;
  sessions.value.push({
    id,
    config,
    isMinimized: false
  });
  
  // Minimalizujemy poprzednią aktywną sesję, jeśli jakaś była
  if (activeSessionId.value) {
    const prev = sessions.value.find(s => s.id === activeSessionId.value);
    if (prev) {
      prev.isMinimized = true;
    }
  }

  activeSessionId.value = id;
};

const activateSession = (id: string) => {
  // Minimalizujemy wszystkie inne
  sessions.value.forEach(s => {
    if (s.id !== id) s.isMinimized = true;
  });
  
  const session = sessions.value.find(s => s.id === id);
  if (session) {
    session.isMinimized = false;
    activeSessionId.value = id;
  }
};

const handleMinimize = (id: string, minimized: boolean) => {
  const session = sessions.value.find(s => s.id === id);
  if (session) {
    session.isMinimized = minimized;
  }
  
  if (minimized && activeSessionId.value === id) {
    activeSessionId.value = null; // Pokazujemy znowu formularz
  } else if (!minimized) {
    activateSession(id);
  }
};

const removeSession = (id: string) => {
  sessions.value = sessions.value.filter(s => s.id !== id);
  if (activeSessionId.value === id) {
    activeSessionId.value = null;
  }
};
</script>

<style>
body {
  margin: 0;
  background-color: #11111b; /* Catppuccin Mocha crust */
  color: #cdd6f4; /* Catppuccin Mocha text */
  font-family: system-ui, sans-serif;
  overflow: hidden;
}

.app-layout {
  display: flex;
  flex-direction: row; /* Zmienione na wiersz ze względu na pasek boczny */
  height: 100vh;
  width: 100vw;
}

.app-sidebar {
  width: 250px;
  background: #181825;
  border-right: 1px solid #313244;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  padding: 1.5rem;
  font-size: 1.5rem;
  font-weight: bold;
  color: #89b4fa;
  border-bottom: 1px solid #313244;
  text-align: center;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
}

.nav-menu button {
  background: transparent;
  border: none;
  color: #a6adc8;
  padding: 1rem 1.5rem;
  text-align: left;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.nav-menu button:hover {
  background: #1e1e2e;
  color: #cdd6f4;
}

.nav-menu button.active {
  background: #1e1e2e;
  color: #89b4fa;
  border-left-color: #89b4fa;
  font-weight: 600;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-stage {
  position: relative;
  flex: 1;
  display: flex;
  padding: 1rem;
  overflow: hidden;
}

.module-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.dashboard-container {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 2rem;
  width: 100%;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  align-items: flex-start;
  padding-top: 2rem;
  overflow-y: auto; /* Zapewnia poprawne przewijanie całości po zawinięciu */
}

.form-section {
  flex: 1 1 350px;
  max-width: 450px;
}

.list-section {
  flex: 1;
  overflow-y: auto;
  padding-right: 1rem;
}

/* ── DOCK ── */
.dock-container {
  display: flex;
  gap: 1rem;
  padding: 0;
  background: #181825;
  border-top: 1px solid #313244;
  height: 0; /* chowany gdy pusty */
  transition: all 0.3s;
  overflow-x: auto;
  align-items: center;
  flex-shrink: 0;
}

.dock-container.has-items {
  height: 190px; /* 160px miniaturka + paddingi */
  padding: 1rem;
}

/* Nadpisanie z RemoteSession.vue po teleportacji */
#dock .terminal-window.is-minimized {
  position: relative !important;
  flex-shrink: 0;
}
</style>