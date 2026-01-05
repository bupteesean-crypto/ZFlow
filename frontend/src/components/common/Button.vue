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
  background: linear-gradient(135deg, rgba(108, 249, 224, 0.9), rgba(124, 93, 255, 0.9));
  color: #0b111d;
  border-color: transparent;
}

.z-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(108, 249, 224, 0.25);
}

.z-btn--secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #e5e9ff;
  border-color: rgba(255, 255, 255, 0.12);
}

.z-btn--secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(108, 249, 224, 0.35);
}

.z-btn--ghost {
  background: transparent;
  color: #e5e7eb;
  border-color: rgba(255, 255, 255, 0.12);
}

.z-btn--ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
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
