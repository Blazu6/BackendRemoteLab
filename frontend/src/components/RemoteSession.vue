<template>
  <Teleport to="#dock" :disabled="!isMinimized">
    <div
      v-show="isConnected || isConnecting"
      class="terminal-window"
      :class="{ 'is-minimized': isMinimized, 'is-active': isActive }"
      @click="isMinimized ? restore() : $emit('activate')"
    >
      <!-- Pasek tytułowy -->
      <div class="title-bar">
        <span class="title-info">
          <span class="status-dot" :class="{ 'connected': isConnected, 'error': !!errorMessage }"></span>
          {{ config.hostname }} · {{ config.protocol.toUpperCase() }}
        </span>
        <div class="title-actions">
          <button
            class="title-btn minimize-btn"
            @click.stop="toggleMinimize"
            :title="isMinimized ? 'Przywróć' : 'Minimalizuj'"
          >
            {{ isMinimized ? '🗖' : '🗕' }}
          </button>
          <button class="title-btn close-btn" @click.stop="handleDisconnect" title="Rozłącz">✕</button>
        </div>
      </div>

      <!-- Viewport terminala -->
      <div ref="displayRef" class="display-viewport"></div>

      <div v-if="errorMessage" class="error-overlay">
        {{ errorMessage }}
      </div>

      <!-- Etykieta na miniaturce -->
      <div v-if="isMinimized" class="mini-label">
        <span>{{ config.protocol.toUpperCase() }} · {{ config.hostname }}</span>
        <button class="mini-close-btn" @click.stop="handleDisconnect" title="Rozłącz">✕</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useGuacamole, type ConnectionConfig } from '../composables/useGuacamole';

const props = defineProps<{
  config: ConnectionConfig;
  isActive: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'activate'): void;
  (e: 'minimize', state: boolean): void;
}>();

const displayRef = ref<HTMLElement | null>(null);
const isMinimized = ref(false);
const isConnecting = ref(true);

const { isConnected, errorMessage, connect, disconnect, triggerRescale } = useGuacamole();

onMounted(() => {
  if (displayRef.value) {
    connect(displayRef.value, props.config);
  }
});

watch(isConnected, (val) => {
  if (val) {
    isConnecting.value = false;
  }
});

const handleDisconnect = () => {
  disconnect();
  emit('close');
};

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value;
  emit('minimize', isMinimized.value);
  if (!isMinimized.value) {
    emit('activate');
    setTimeout(() => triggerRescale(), 350);
  }
};

const restore = () => {
  if (!isMinimized.value) return;
  isMinimized.value = false;
  emit('minimize', false);
  emit('activate');
  setTimeout(() => triggerRescale(), 350);
};

// Zarządzanie stanem klawiatury zależnie od aktywności i zminimalizowania
// Focusujemy terminal gdy staje się aktywny
watch(
  () => props.isActive && !isMinimized.value,
  (shouldBeEnabled) => {
    if (shouldBeEnabled) {
      setTimeout(() => {
        triggerRescale();
        displayRef.value?.focus();
      }, 100);
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  disconnect();
});

// Pozwalamy rodzicowi wymusić minimalizację/przywrócenie
defineExpose({
  restore,
  minimize: () => {
    if (!isMinimized.value) toggleMinimize();
  },
  isMinimized
});
</script>

<style scoped>
/* ── Okno terminala ── */
.terminal-window {
  display: flex;
  flex-direction: column;
  position: absolute; /* absolutne pozycjonowanie na tle formularza */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #11111b;
  border: 1px solid #333;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
}

.terminal-window.is-active {
  z-index: 20;
}

/* ── Zminimalizowane okno (zarządzane przez rodzica na Docku) ── */
/* Jeśli is-minimized, to flex container (np. dock) może nim sterować jeśli użyjemy odpowiedniego CSS. 
Ale my po prostu ukrywamy główny widok w App.vue, a samo okno zmniejszamy, gdy ląduje na pasku. */
.terminal-window.is-minimized {
  position: relative !important;
  top: auto;
  left: auto;
  width: 240px;
  height: 160px;
  max-width: 240px;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
  border: 1px solid #45475a;
  z-index: 5;
}

.terminal-window.is-minimized:hover {
  border-color: #89b4fa;
  box-shadow: 0 4px 24px rgba(137, 180, 250, 0.2);
  transform: translateY(-5px);
}

.terminal-window.is-minimized .display-viewport {
  pointer-events: none;
}

.terminal-window.is-minimized .title-bar {
  padding: 0.25rem 0.5rem;
  font-size: 0.7rem;
}

.terminal-window.is-minimized .title-actions {
  display: none;
}

/* ── Pasek tytułowy ── */
.title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.8rem;
  background: #1e1e2e;
  border-bottom: 1px solid #313244;
  flex-shrink: 0;
  user-select: none;
}

.title-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: #a6adc8;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f9e2af; /* żółty - łączenie */
}
.status-dot.connected {
  background: #a6e3a1;
  box-shadow: 0 0 6px rgba(166, 227, 161, 0.5);
}
.status-dot.error {
  background: #f38ba8;
  box-shadow: 0 0 6px rgba(243, 139, 168, 0.5);
}

.title-actions {
  display: flex;
  gap: 0.3rem;
}

.title-btn {
  padding: 0.15rem 0.5rem;
  background: transparent;
  color: #6c7086;
  border: none;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}

.title-btn:hover {
  background: #313244;
  color: #cdd6f4;
}

.close-btn:hover {
  background: #f38ba8;
  color: #1e1e2e;
}

/* ── Viewport ── */
.display-viewport {
  flex: 1;
  background: #000;
  overflow: hidden;
  /* Usunięto flex centering, bo gryzie się z transform: scale() i ucina ekran */
}

.error-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(30,30,46,0.9);
  padding: 1rem 2rem;
  border-radius: 8px;
  border: 1px solid #f38ba8;
  color: #f38ba8;
  font-weight: bold;
}

/* ── Miniaturka label ── */
.mini-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 30, 46, 0.95);
  color: #a6adc8;
  font-size: 0.7rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.mini-close-btn {
  background: transparent;
  color: #f38ba8;
  border: none;
  cursor: pointer;
  padding: 0 0.2rem;
  font-size: 0.9rem;
  line-height: 1;
  transition: color 0.15s;
}

.mini-close-btn:hover {
  color: #ffb4c6;
}
</style>
