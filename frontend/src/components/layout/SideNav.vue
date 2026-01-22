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
  background: linear-gradient(180deg, rgba(11, 15, 22, 0.92), rgba(11, 15, 22, 0.65));
  border-right: 1px solid rgba(77, 231, 255, 0.22);
  border-radius: 16px;
  padding: 16px 0;
  margin: 0 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 16px 28px rgba(2, 6, 23, 0.45);
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
  box-shadow: 0 10px 18px rgba(2, 6, 23, 0.45);
}

.nav-link:hover {
  border-color: rgba(var(--md-accent-rgb), 0.2);
  background: rgba(var(--md-accent-rgb), 0.1);
  color: var(--md-on-surface);
  transform: translateY(-2px);
}

.nav-link.active {
  border-color: rgba(var(--md-accent-rgb), 0.4);
  background: rgba(var(--md-accent-rgb), 0.2);
  color: var(--md-on-surface);
  box-shadow: 0 12px 22px rgba(var(--md-accent-rgb), 0.15);
}

.nav-link.icon-only::after {
  content: attr(data-label);
  position: absolute;
  left: 60px;
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
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
