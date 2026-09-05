<template>
  <div class="instructions-layout">
    <!-- Lewy panel: Lista instrukcji -->
    <div class="instructions-sidebar">
      <div class="sidebar-header">
        <h3>Dostępne Instrukcje</h3>
        <!-- Przycisk do pokazania uploadera -->
        <button class="upload-btn" @click="showUploader = !showUploader">
          {{ showUploader ? 'Anuluj' : '➕ Dodaj' }}
        </button>
      </div>

      <!-- Lista plików -->
      <div class="pdf-list" v-if="!showUploader">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="pdf-item"
          :class="{ active: selectedDoc?.id === doc.id }"
          @click="selectedDoc = doc"
        >
          <div class="pdf-icon">📄</div>
          
          <div class="pdf-info">
            <h4>{{ doc.title }}</h4>
            <span class="pdf-type" :class="doc.type">
              {{ doc.type === 'interactive' ? 'Do wypełnienia' : 'Do czytania' }}
            </span>
          </div>

          <!-- PRZYCISK: Usuwanie (pojawia się po najechaniu) -->
          <button 
            class="delete-btn" 
            @click.stop="deleteDocument(doc.id)"
            title="Usuń instrukcję"
          >
            🗑️
          </button>
        </div>
        
        <!-- Komunikat, gdy lista jest pusta -->
        <div v-if="documents.length === 0" class="empty-list-text">
          Brak instrukcji. Dodaj pierwszą!
        </div>
      </div>
      
      <!-- Miejsce na uploader -->
      <div class="uploader-container" v-else>
        <PdfUploader 
          @uploaded="onDocumentUploaded"
          @cancel="showUploader = false"
        />
      </div>
    </div>

    <!-- Prawy panel: Podgląd PDF -->
    <div class="instructions-viewer">
      <template v-if="selectedDoc">
        <div class="viewer-header">
          <h2>{{ selectedDoc.title }}</h2>
          <a :href="selectedDoc.url" download class="download-btn">
            ⬇️ Pobierz na dysk
          </a>
        </div>

        <!-- NOWY ELEMENT: Ostrzeżenie widoczne tylko dla PDF-ów do wypełniania -->
        <div v-if="selectedDoc.type === 'interactive'" class="warning-banner">
          ⚠️ <strong>Uwaga:</strong> Twoje odpowiedzi nie zapisują się na serwerze! Pamiętaj, aby pobrać plik (ze swoimi zmianami) przed odświeżeniem strony, w przeciwnym razie stracisz postępy.
        </div>

        <div class="iframe-container">
          <!-- Natywna przeglądarka PDF -->
          <iframe
            :src="selectedDoc.url"
            class="pdf-iframe"
            title="Podgląd instrukcji"
          ></iframe>
        </div>
      </template>
      
      <!-- Stan pusty, gdy nic nie wybrano -->
      <div v-else class="empty-state">
        <div class="empty-icon">📂</div>
        <p>Wybierz instrukcję z listy po lewej stronie lub wgraj nową, aby ją wyświetlić.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import PdfUploader from './PdfUploader.vue';
import axios from 'axios';

// Definiujemy interfejs dla TypeScriptu
interface Document {
  id: number;
  title: string;
  url: string;
  type: 'static' | 'interactive';
}

const showUploader = ref(false);
const selectedDoc = ref<Document | null>(null);
const documents = ref<Document[]>([]);

// Adres serwera Django
const DJANGO_BASE_URL = 'http://192.168.1.88:8000';
const API_URL = `${DJANGO_BASE_URL}/api/documents/`;

// 1. POBIERANIE LISTY Z BAZY
const fetchDocuments = async () => {
  try {
    const response = await axios.get(API_URL);
    // Dodajemy adres Django do linku PDF
    documents.value = response.data.map((doc: Document) => ({
      ...doc,
      url: `${DJANGO_BASE_URL}${doc.url}`
    }));
  } catch (error) {
    console.error("Błąd pobierania listy:", error);
  }
};

// 2. WYSYŁANIE DO DJANGO
const onDocumentUploaded = async (data: { file: File, type: 'static' | 'interactive', title: string }) => {
  const formData = new FormData();
  formData.append('file', data.file);
  formData.append('title', data.title);
  formData.append('type', data.type);

  try {
    await axios.post(API_URL, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    await fetchDocuments();
    showUploader.value = false;
  } catch (error) {
    console.error("Błąd podczas wysyłania na serwer!", error);
    alert("Wystąpił błąd podczas wgrywania pliku.");
  }
};

// 3. USUWANIE Z DJANGO
const deleteDocument = async (id: number) => {
  if (!confirm('Czy na pewno chcesz usunąć tę instrukcję?')) return;

  try {
    await axios.delete(`${API_URL}${id}/`);
    documents.value = documents.value.filter(doc => doc.id !== id);
    if (selectedDoc.value?.id === id) selectedDoc.value = null;
  } catch (error) {
    console.error("Błąd podczas usuwania z serwera!", error);
    alert("Błąd podczas usuwania instrukcji.");
  }
};

// Pobierz instrukcje przy wejściu na widok
onMounted(() => {
  fetchDocuments();
});
</script>

<style scoped>
.instructions-layout {
  display: flex;
  height: 100%;
  width: 100%;
  gap: 1rem;
}

/* LEWY PANEL */
.instructions-sidebar {
  width: 350px;
  background: #1e1e2e;
  border-radius: 12px;
  border: 1px solid #313244;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #313244;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  color: #cdd6f4;
  font-size: 1.1rem;
}

.upload-btn {
  background: #313244;
  color: #cdd6f4;
  border: none;
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}

.upload-btn:hover {
  background: #45475a;
}

.pdf-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.empty-list-text {
  text-align: center;
  color: #a6adc8;
  padding: 2rem 0;
  font-size: 0.9rem;
}

.pdf-item {
  background: #181825;
  border: 1px solid transparent;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  gap: 1rem;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.pdf-item:hover {
  background: #313244;
}

.pdf-item.active {
  border-color: #89b4fa;
  background: #313244;
}

.pdf-icon {
  font-size: 1.8rem;
}

.pdf-info {
  flex: 1;
}

.pdf-info h4 {
  margin: 0 0 0.3rem 0;
  color: #cdd6f4;
  font-size: 0.95rem;
}

.pdf-type {
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.pdf-type.static {
  background: #45475a;
  color: #a6adc8;
}

.pdf-type.interactive {
  background: #89b4fa20;
  color: #89b4fa;
}

/* STYL KOSZA NA ŚMIECI */
.delete-btn {
  background: transparent;
  border: none;
  color: #f38ba8;
  font-size: 1.2rem;
  cursor: pointer;
  opacity: 0;
  transition: 0.2s;
  padding: 0.5rem;
  border-radius: 4px;
}

.pdf-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #f38ba820;
  transform: scale(1.1);
}

.uploader-container {
  padding: 2rem;
  text-align: center;
}

/* PRAWY PANEL */
.instructions-viewer {
  flex: 1;
  background: #1e1e2e;
  border-radius: 12px;
  border: 1px solid #313244;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.viewer-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #313244;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.viewer-header h2 {
  margin: 0;
  color: #89b4fa;
  font-size: 1.2rem;
}

.download-btn {
  background: #a6e3a1;
  color: #11111b;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: bold;
  font-size: 0.9rem;
  transition: 0.2s;
}

.download-btn:hover {
  background: #94cc90;
}

/* STYL DLA BANERA OSTRZEGAWCZEGO */
.warning-banner {
  background-color: rgba(243, 139, 168, 0.15); 
  color: #f38ba8; 
  padding: 0.8rem 1.5rem;
  font-size: 0.9rem;
  border-bottom: 1px solid #313244;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.warning-banner strong {
  font-weight: 800;
}

.iframe-container {
  flex: 1;
  width: 100%;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #a6adc8;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}
</style>