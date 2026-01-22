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
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@400;500;700&display=swap");
@import "./styles/utilities.css";
@import "./styles/layout.css";

:root {
  --md-surface: #0b0f16;
  --md-surface-container: #111827;
  --md-surface-container-low: #0f172a;
  --md-surface-elevated: #151f33;
  --md-surface-card: rgba(15, 23, 42, 0.86);
  --md-on-surface: #e2e8f0;
  --md-on-surface-variant: #94a3b8;
  --md-primary: #4de7ff;
  --md-on-primary: #041019;
  --md-secondary-container: #12243a;
  --md-on-secondary-container: #d7f7ff;
  --md-tertiary: #00d4a1;
  --md-outline: #334155;
  --md-shadow: rgba(2, 6, 23, 0.45);
  --md-stroke: rgba(148, 163, 184, 0.2);
  --md-stroke-strong: rgba(77, 231, 255, 0.45);
  --md-accent-rgb: 77, 231, 255;
  --md-accent-2-rgb: 0, 212, 161;
  --md-accent-glow: rgba(77, 231, 255, 0.22);
  --md-accent-soft: rgba(77, 231, 255, 0.12);
  --md-surface-glow: rgba(15, 23, 42, 0.75);
  --md-card-shadow: 0 18px 38px rgba(2, 6, 23, 0.45);
  --md-card-shadow-soft: 0 12px 26px rgba(2, 6, 23, 0.35);
  --md-field-bg: rgba(10, 16, 28, 0.85);
  --layer-nav: 100;
  --layer-side: 90;
  --layer-popover: 200;
  --layer-overlay: 800;
  --layer-modal: 900;
  --layer-toast: 1000;
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
  font-family: "Space Grotesk", "Manrope", "Noto Sans SC", sans-serif;
  line-height: 1.5;
  color: var(--md-on-surface);
  background: radial-gradient(circle at top, rgba(56, 189, 248, 0.08), transparent 45%),
    radial-gradient(circle at 20% 20%, rgba(0, 212, 161, 0.08), transparent 42%),
    radial-gradient(circle at 80% 0%, rgba(77, 231, 255, 0.12), transparent 38%),
    var(--md-surface);
  position: relative;
}

#app {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.35;
  z-index: 0;
}

body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at 20% 10%, rgba(var(--md-accent-rgb), 0.12), transparent 45%),
    radial-gradient(circle at 80% 90%, rgba(var(--md-accent-2-rgb), 0.1), transparent 40%);
  z-index: 0;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.08);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(77, 231, 255, 0.18);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(77, 231, 255, 0.3);
}

/* Link styles */
a {
  color: inherit;
  text-decoration: none;
}

/* Focus visible */
:focus-visible {
  outline: 2px solid rgba(var(--md-accent-rgb), 0.7);
  outline-offset: 2px;
}

/* Selection */
::selection {
  background: rgba(var(--md-accent-rgb), 0.25);
  color: var(--md-on-surface);
}

input,
textarea,
select {
  font-family: inherit;
}

input::placeholder,
textarea::placeholder {
  color: rgba(148, 163, 184, 0.7);
}

input:focus,
textarea:focus,
select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--md-accent-rgb), 0.25);
  border-color: rgba(var(--md-accent-rgb), 0.35);
}

/* Toast Notifications */
.toast-fixed {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--layer-toast);
  animation: slideUp 0.3s ease;
}

.toast-notification {
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  box-shadow: 0 16px 32px rgba(2, 6, 23, 0.45);
  margin-top: 8px;
}

.toast--info {
  background: rgba(15, 23, 42, 0.9);
  color: var(--md-on-surface);
  border: 1px solid rgba(77, 231, 255, 0.18);
}

.toast--success {
  background: rgba(15, 118, 110, 0.22);
  color: #a7f3d0;
  border: 1px solid rgba(20, 184, 166, 0.35);
}

.toast--error {
  background: rgba(220, 38, 38, 0.2);
  color: #fecaca;
  border: 1px solid rgba(248, 113, 113, 0.35);
}

.toast--warning {
  background: rgba(245, 158, 11, 0.22);
  color: #fde68a;
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

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
