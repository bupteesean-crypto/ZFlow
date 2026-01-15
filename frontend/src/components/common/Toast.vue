<template>
  <Transition name="toast">
    <div v-if="visible" class="toast" :class="`toast--${variant}`">
      {{ message }}
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

type ToastVariant = 'success' | 'error' | 'info' | 'warning';

const props = withDefaults(defineProps<{
  show?: boolean;
  message?: string;
  duration?: number;
  variant?: ToastVariant;
}>(), {
  show: false,
  message: '',
  duration: 3000,
  variant: 'info',
});

const emit = defineEmits<{
  'update:show': [value: boolean];
  close: [];
}>();

const visible = ref(props.show);

let timeoutId: number | undefined;

watch(() => props.show, (show) => {
  visible.value = show;
  if (show) {
    if (timeoutId) clearTimeout(timeoutId);
    if (props.duration > 0) {
      timeoutId = window.setTimeout(() => {
        close();
      }, props.duration);
    }
  }
});

const close = () => {
  visible.value = false;
  emit('update:show', false);
  emit('close');
};
</script>

<style scoped>
.toast {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 24px;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  z-index: var(--layer-toast);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
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

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}
</style>
