<template>
  <component
    :is="tag"
    :type="tag === 'button' ? nativeType : undefined"
    :to="tag === 'a' ? to : undefined"
    :href="tag === 'a' ? to : undefined"
    :disabled="disabled"
    class="z-btn"
    :class="classes"
    @click="handleClick"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { RouteLocationRaw } from 'vue-router';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

const props = withDefaults(defineProps<{
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  nativeType?: 'button' | 'submit' | 'reset';
  to?: RouteLocationRaw;
  pill?: boolean;
}>(), {
  variant: 'primary',
  size: 'md',
  nativeType: 'button',
  pill: false,
});

const emit = defineEmits<{
  click: [e: Event];
}>();

const tag = computed(() => props.to ? 'a' : 'button');

const classes = computed(() => [
  `z-btn--${props.variant}`,
  `z-btn--${props.size}`,
  { 'z-btn--pill': props.pill },
]);

const handleClick = (e: Event) => {
  if (!props.disabled) {
    emit('click', e);
  }
};
</script>

<style scoped>
.z-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  font-weight: 500;
}

.z-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Sizes */
.z-btn--sm {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 8px;
}

.z-btn--md {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 10px;
}

.z-btn--lg {
  padding: 12px 20px;
  font-size: 15px;
  border-radius: 12px;
}

.z-btn--pill {
  border-radius: 9999px;
}

/* Variants */
.z-btn--primary {
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.95), rgba(var(--md-accent-2-rgb), 0.9));
  color: #031019;
  border-color: transparent;
}

.z-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(77, 231, 255, 0.25);
}

.z-btn--secondary {
  background: rgba(148, 163, 184, 0.08);
  color: #e2e8f0;
  border-color: rgba(148, 163, 184, 0.2);
}

.z-btn--secondary:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(var(--md-accent-rgb), 0.35);
}

.z-btn--ghost {
  background: transparent;
  color: #e2e8f0;
  border-color: rgba(148, 163, 184, 0.2);
}

.z-btn--ghost:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.08);
  border-color: rgba(148, 163, 184, 0.35);
}

.z-btn--danger {
  background: rgba(248, 113, 113, 0.12);
  color: #fecdd3;
  border-color: rgba(248, 113, 113, 0.3);
}

.z-btn--danger:hover:not(:disabled) {
  background: rgba(248, 113, 113, 0.2);
  border-color: rgba(248, 113, 113, 0.5);
}
</style>
