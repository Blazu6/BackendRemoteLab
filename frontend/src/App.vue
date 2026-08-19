<template>
  <main class="app-layout">
    <header class="app-header">
      <h1>Remote Lab 🧪</h1>
    </header>

    <div class="main-stage">
      <!-- Formularz pokazujemy, jeśli nie ma żadnej aktywnej (pełnoekranowej) sesji -->
      <div v-show="!activeSessionId" class="dashboard-container">
        <div class="form-section">
          <ConnectionForm @saved="handleSaved" />
        </div>
        <div class="list-section">
          <MachineList ref="machineListRef" @connect="handleConnect" />
        </div>
      </div>

      <!-- Wyświetlanie wszystkich sesji. Teleportują się do #dock gdy są zminimalizowane -->
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
    </div>

    <!-- Pasek zadań na zminimalizowane sesje (Dock) -->
    <div id="dock" class="dock-container" :class="{ 'has-items': hasMinimizedSessions }">
      <!-- Teleporty będą wrzucać tutaj DOM zminimalizowanych RemoteSession -->
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import ConnectionForm from './components/ConnectionForm.vue';
import MachineList from './components/MachineList.vue';
import RemoteSession from './components/RemoteSession.vue';
import type { ConnectionConfig } from './composables/useGuacamole';

interface SessionData {
  id: string;
  config: ConnectionConfig;
  isMinimized: boolean;
}

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
  flex-direction: column;
  height: 100vh;
}

.app-header {
  padding: 1rem 2rem;
  background: #1e1e2e;
  border-bottom: 1px solid #313244;
  flex-shrink: 0;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #89b4fa;
}

.main-stage {
  position: relative;
  flex: 1;
  display: flex;
  padding: 1rem;
  overflow: hidden; /* zapobiega scrollowaniu gdy okna są absolute */
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