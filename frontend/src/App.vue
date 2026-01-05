<template>
  <component :is="layoutComponent">
    <RouterView />
  </component>

  <!-- Toast Container -->
  <Teleport to="body">
    <div v-for="toast in toasts" :key="toast.id" class="toast-fixed">
      <div :class="['toast-notification', `toast--${toast.variant}`]">
        {{ toast.message }}
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, provide } from 'vue';
import { RouterView, useRoute } from 'vue-router';
import { toasts as toastState } from './composables/useToast';

// Import layout components
import AppShell from './components/layout/AppShell.vue';

const route = useRoute();

// Layout mapping
const layoutComponents: Record<string, any> = {
  'app-shell': AppShell,
  'bare': 'div',  // No layout wrapper
  'legacy': 'div',  // Legacy pages use simple div
};

const layoutComponent = computed(() => {
  const layout = (route.meta?.layout as string) || 'bare';
  return layoutComponents[layout] || 'div';
});

// Provide toast state to all components
provide('toasts', toastState);
</script>

<style>
/* Global Styles */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: "JetBrains Mono", "SFMono-Regular", "Menlo", "Inter", system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  color: #dfe8ff;
  background: #05070f;
}

#app {
  min-height: 100vh;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* Link styles */
a {
  color: inherit;
  text-decoration: none;
}

/* Focus visible */
:focus-visible {
  outline: 2px solid rgba(108, 249, 224, 0.6);
  outline-offset: 2px;
}

/* Selection */
::selection {
  background: rgba(108, 249, 224, 0.25);
  color: #f8fbff;
}

/* Toast Notifications */
.toast-fixed {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  animation: slideUp 0.3s ease;
}

.toast-notification {
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  margin-top: 8px;
}

.toast--info {
  background: rgba(12, 16, 26, 0.95);
  color: #dfe8ff;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toast--success {
  background: rgba(12, 16, 26, 0.95);
  color: #9cfbe6;
  border: 1px solid rgba(108, 249, 224, 0.35);
}

.toast--error {
  background: rgba(12, 16, 26, 0.95);
  color: #fecdd3;
  border: 1px solid rgba(248, 113, 113, 0.35);
}

.toast--warning {
  background: rgba(12, 16, 26, 0.95);
  color: #fcd34d;
  border: 1px solid rgba(251, 191, 36, 0.35);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
