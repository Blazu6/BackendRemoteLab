<template>
  <div class="pdf-uploader">
    <h4>Wgraj nowy plik PDF</h4>
    
    <div class="form-group">
      <label>Kategoria instrukcji:</label>
      <select v-model="pdfType" class="dark-input">
        <option value="static">Zwykła (Do czytania)</option>
        <option value="interactive">Interaktywna (Do wypełnienia)</option>
      </select>
    </div>

    <div class="form-group">
      <input 
        type="file" 
        accept="application/pdf" 
        @change="handleFileSelect" 
        class="dark-input file-input" 
      />
    </div>

    <div class="actions">
      <button @click="$emit('cancel')" class="btn-cancel">Anuluj</button>
      <button @click="handleUpload" :disabled="!selectedFile" class="btn-submit">
        Wgraj instrukcję
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits(['uploaded', 'cancel']);
const selectedFile = ref<File | null>(null);
const pdfType = ref<'static' | 'interactive'>('static');

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
  }
};

const handleUpload = () => {
  if (!selectedFile.value) return;

  // Wysyłamy plik do głównego komponentu
  emit('uploaded', {
    file: selectedFile.value,
    type: pdfType.value,
    title: selectedFile.value.name.replace('.pdf', '') // Usuwamy .pdf z nazwy
  });
};
</script>

<style scoped>
.pdf-uploader {
  background: #181825;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px dashed #45475a;
}

h4 {
  margin: 0 0 1rem 0;
  color: #cdd6f4;
}

.form-group {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  color: #a6adc8;
  font-size: 0.9rem;
}

.dark-input {
  background: #1e1e2e;
  border: 1px solid #313244;
  color: #cdd6f4;
  padding: 0.8rem;
  border-radius: 6px;
  outline: none;
}

.dark-input:focus {
  border-color: #89b4fa;
}

.file-input {
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

button {
  flex: 1;
  padding: 0.8rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: 0.2s;
}

.btn-cancel {
  background: #313244;
  color: #cdd6f4;
}

.btn-cancel:hover { background: #45475a; }

.btn-submit {
  background: #89b4fa;
  color: #11111b;
}

.btn-submit:hover:not(:disabled) { background: #74c7ec; }
.btn-submit:disabled {
  background: #313244;
  color: #585b70;
  cursor: not-allowed;
}
</style>