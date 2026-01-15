<template>
  <aside class="side-nav">
    <div class="glass-side">
      <RouterLink
        v-for="item in items"
        :key="item.name"
        :to="item.to"
        class="nav-link icon-only"
        :class="{ active: isActive(item.to) }"
        :data-label="item.label"
      >
        {{ item.icon }}
      </RouterLink>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

interface NavItem {
  name: string;
  to: string;
  icon: string;
  label: string;
}

defineProps<{
  items: NavItem[];
}>();

const route = useRoute();

const isActive = (path: string): boolean => {
  if (path === '/') {
    return route.path === '/' || route.path === '/landing';
  }
  return route.path.startsWith(path);
};
</script>

<style scoped>
.side-nav {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 64px;
  z-index: var(--layer-side);
}

.glass-side {
  background: rgba(243, 237, 247, 0.9);
  border-right: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 16px 0;
  margin: 0 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.14);
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  font-size: 15px;
  border-radius: 12px;
  color: var(--md-on-surface-variant);
  border: 1px solid transparent;
  transition: 0.2s ease;
  text-decoration: none;
  width: 48px;
  height: 48px;
  position: relative;
  box-shadow: 0 8px 16px rgba(26, 18, 44, 0.1);
}

.nav-link:hover {
  border-color: rgba(103, 80, 164, 0.2);
  background: rgba(103, 80, 164, 0.1);
  color: var(--md-on-surface);
  transform: translateY(-2px);
}

.nav-link.active {
  border-color: rgba(103, 80, 164, 0.4);
  background: rgba(103, 80, 164, 0.18);
  color: var(--md-on-surface);
}

.nav-link.icon-only::after {
  content: attr(data-label);
  position: absolute;
  left: 60px;
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  color: var(--md-on-surface);
  font-size: 12px;
  opacity: 0;
  transform: translateY(4px);
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.nav-link.icon-only:hover::after {
  opacity: 1;
  transform: translateY(0);
}
</style>
