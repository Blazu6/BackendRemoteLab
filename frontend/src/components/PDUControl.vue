<template>
  <div class="pdu-control">
    <h2>Zarządzanie Zasilaniem (PDU)</h2>
    <div class="placeholder-info">
      <p>Miejsce na moduł integracji PDU.</p>
      <p class="dev-note">
        <strong>Dev Note:</strong> Backend odpowiada pod endpointem <code>GET /api/pdu/</code>.<br>
        Możesz tutaj wrzucić listę przekaźników i przyciski ON/OFF z odpowiednimi zapytaniami POST.
      </p>
    </div>
    
    <div v-if="loading" class="loading">Ładowanie stanu PDU...</div>
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
    const res = await fetch('/api/pdu/');
    mockData.value = await res.json();
  } catch (err) {
    mockData.value = { error: 'Failed to fetch' };
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.pdu-control {
  padding: 2rem;
  background: #1e1e2e;
  border-radius: 12px;
  color: #cdd6f4;
  border: 1px dashed #585b70;
  max-width: 800px;
}
.pdu-control h2 {
  color: #f9e2af;
  margin-top: 0;
}
.placeholder-info {
  margin-bottom: 2rem;
}
.dev-note {
  background: #181825;
  padding: 1rem;
  border-left: 4px solid #89b4fa;
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
