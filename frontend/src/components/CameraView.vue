<template>
  <div class="camera-view">
    <h2>Monitoring Laboratorium (MediaMTX)</h2>
    <div class="placeholder-info">
      <p>Miejsce na moduł podglądu z kamer (MediaMTX).</p>
      <p class="dev-note">
        <strong>Dev Note:</strong> Backend odpowiada pod endpointem <code>GET /api/cameras/</code>.<br>
        Zaimplementuj tutaj odtwarzacz wideo (np. WebRTC lub HLS) do odbierania strumieni z serwera MediaMTX.
      </p>
    </div>
    
    <div v-if="loading" class="loading">Ładowanie kamer...</div>
    <div v-else class="mock-data">
      <h3>Odpowiedź z mock-API:</h3>
      <pre>{{ mockData }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const loading = ref(true);
const mockData = ref<any>(null);

onMounted(async () => {
  try {
    const res = await fetch('/api/cameras/');
    mockData.value = await res.json();
  } catch (err) {
    mockData.value = { error: 'Failed to fetch' };
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.camera-view {
  padding: 2rem;
  background: #1e1e2e;
  border-radius: 12px;
  color: #cdd6f4;
  border: 1px dashed #585b70;
  max-width: 800px;
}
.camera-view h2 {
  color: #89b4fa;
  margin-top: 0;
}
.placeholder-info {
  margin-bottom: 2rem;
}
.dev-note {
  background: #181825;
  padding: 1rem;
  border-left: 4px solid #f9e2af;
  border-radius: 4px;
  font-size: 0.9rem;
}
.mock-data pre {
  background: #11111b;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}
</style>
