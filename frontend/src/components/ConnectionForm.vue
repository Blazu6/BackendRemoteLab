<template>
  <form @submit.prevent="handleSubmit" class="connect-form">
    <h2>Dodaj nowy serwer</h2>
    
    <div class="form-group">
      <label>Nazwa (Alias):</label>
      <input v-model="form.name" type="text" placeholder="np. Mój Główny Linux" required />
    </div>

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
      <input v-model="form.hostname" type="text" placeholder="np. 192.168.1.100" required />
    </div>

    <div class="form-group">
      <label>Port:</label>
      <input v-model="form.port" type="text" required />
    </div>

    <div class="form-group">
      <label>Użytkownik (opcjonalnie):</label>
      <input v-model="form.username" type="text" />
    </div>

    <div class="form-group">
      <label>Hasło (opcjonalnie):</label>
      <input v-model="form.password" type="password" />
    </div>

    <button type="submit" :disabled="isSaving">
      {{ isSaving ? 'Zapisywanie...' : 'Zapisz i zamknij' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import type { ConnectionConfig } from '../composables/useGuacamole';

const emit = defineEmits<{
  (e: 'saved'): void
}>();

const form = reactive<ConnectionConfig>({
  name: '',
  protocol: 'ssh',
  hostname: '',
  port: '2222',
  username: '',
  password: '',
});

const isSaving = ref(false);

const handleSubmit = async () => {
  isSaving.value = true;
  try {
    const res = await fetch('/api/machines/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });
    
    if (res.ok) {
      // Wyczyść formularz (opcjonalnie, lub tylko hasło)
      form.name = '';
      form.hostname = '';
      form.password = '';
      emit('saved');
    } else {
      const data = await res.json();
      alert('Błąd zapisu: ' + data.message);
    }
  } catch (err) {
    alert('Błąd sieci: ' + err);
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.connect-form {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
  max-width: 420px;
  background: #1e1e2e;
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #333;
  color: #cdd6f4;
  margin: 0 auto;
}

.connect-form h2 {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
  color: #a6e3a1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.form-group label {
  font-size: 0.85rem;
  color: #9399b2;
}

input, select {
  padding: 0.55rem 0.7rem;
  border-radius: 6px;
  border: 1px solid #45475a;
  background: #11111b;
  color: #cdd6f4;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

input:focus, select:focus {
  outline: none;
  border-color: #89b4fa;
}

button {
  padding: 0.65rem;
  background: #a6e3a1;
  color: #1e1e2e;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
  transition: background 0.2s;
}

button:hover {
  background: #94e2d5;
}
</style>
