<template>
  <div class="terminal-container">
    <form v-if="!isConnected" @submit.prevent="handleConnect" class="connect-form">
      <h2>Połącz z serwerem</h2>
      
      <div class="form-group">
        <label>Protokół:</label>
        <select v-model="form.protocol">
          <option value="ssh">SSH</option>
          <option value="vnc">VNC</option>
          <option value="rdp">RDP</option>
        </select>
      </div>

      <div class="form-group">
        <label>Host:</label>
        <input v-model="form.hostname" type="text" required />
      </div>

      <div class="form-group">
        <label>Port:</label>
        <input v-model="form.port" type="text" required />
      </div>

      <div class="form-group">
        <label>Użytkownik:</label>
        <input v-model="form.username" type="text" />
      </div>

      <div class="form-group">
        <label>Hasło:</label>
        <input v-model="form.password" type="password" />
      </div>

      <button type="submit">Połącz</button>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </form>

    <div v-else class="status-bar">
      <span>🟢 Połączono z {{ form.hostname }} ({{ form.protocol.toUpperCase() }})</span>
      <button @click="disconnect" class="disconnect-btn">Rozłącz</button>
    </div>

    <div ref="displayRef" class="display-viewport"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue';
import { useGuacamole, type ConnectionConfig } from '../composables/useGuacamole';

const displayRef = ref<HTMLElement | null>(null);

const form = reactive<ConnectionConfig>({
  protocol: 'ssh',
  hostname: '',
  port: '22',
  username: '',
  password: '',
});

const { isConnected, errorMessage, connect, disconnect } = useGuacamole();

const handleConnect = () => {
  if (displayRef.value) {
    connect(displayRef.value, form);
  }
};

// Automatyczne czyszczenie zasobów przy zniszczeniu komponentu
onUnmounted(() => {
  disconnect();
});
</script>

<style scoped>
.terminal-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.connect-form {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  max-width: 400px;
  background: #2a2a2a;
  padding: 1.5rem;
  border-radius: 8px;
  color: white;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

input, select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #444;
  background: #1a1a1a;
  color: white;
}

button {
  padding: 0.6rem;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.disconnect-btn {
  background: #e74c3c;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1e1e1e;
  padding: 0.5rem 1rem;
  color: white;
  border-radius: 4px;
}

.display-viewport {
  background: #000;
  min-height: 400px;
  border-radius: 4px;
  overflow: hidden;
}

.error {
  color: #ff6b6b;
}
</style>