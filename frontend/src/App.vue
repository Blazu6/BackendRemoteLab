<template>
  <main class="app">
    <h1>Remote Lab 🧪</h1>
    <TerminalDisplay /> </main>
</template>

<script setup lang="ts">
import TerminalDisplay from './components/TerminalDisplay.vue';
</script>

<style>
body {
  margin: 0;
  background-color: #121212;
  color: white;
  font-family: system-ui, sans-serif;
}

.app {
  padding: 2rem;
}
</style>