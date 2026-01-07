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
import { useToast } from './composables/useToast';
const { state: toastState, push: pushToast } = useToast();

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
@import url("https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&display=swap");

:root {
  --md-surface: #fffbfe;
  --md-surface-container: #f3edf7;
  --md-surface-container-low: #e7e0ec;
  --md-on-surface: #1c1b1f;
  --md-on-surface-variant: #49454f;
  --md-primary: #6750a4;
  --md-on-primary: #ffffff;
  --md-secondary-container: #e8def8;
  --md-on-secondary-container: #1d192b;
  --md-tertiary: #7d5260;
  --md-outline: #79747e;
  --md-shadow: rgba(18, 18, 18, 0.12);
}
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
  font-family: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
  line-height: 1.5;
  color: var(--md-on-surface);
  background: var(--md-surface);
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
  background: rgba(73, 69, 79, 0.08);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(73, 69, 79, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(73, 69, 79, 0.3);
}

/* Link styles */
a {
  color: inherit;
  text-decoration: none;
}

/* Focus visible */
:focus-visible {
  outline: 2px solid rgba(103, 80, 164, 0.5);
  outline-offset: 2px;
}

/* Selection */
::selection {
  background: rgba(103, 80, 164, 0.2);
  color: var(--md-on-surface);
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
  box-shadow: 0 12px 28px rgba(26, 18, 44, 0.18);
  margin-top: 8px;
}

.toast--info {
  background: var(--md-surface-container);
  color: var(--md-on-surface);
  border: 1px solid rgba(121, 116, 126, 0.2);
}

.toast--success {
  background: rgba(232, 247, 242, 0.9);
  color: #146c43;
  border: 1px solid rgba(20, 108, 67, 0.25);
}

.toast--error {
  background: rgba(255, 234, 236, 0.9);
  color: #b42318;
  border: 1px solid rgba(180, 35, 24, 0.25);
}

.toast--warning {
  background: rgba(255, 244, 224, 0.92);
  color: #b54708;
  border: 1px solid rgba(181, 71, 8, 0.25);
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
