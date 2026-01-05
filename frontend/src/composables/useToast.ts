import { ref } from 'vue';

type ToastVariant = 'success' | 'error' | 'info' | 'warning';

const toasts = ref<Array<{ id: string; message: string; variant: ToastVariant }>>([]);

export function useToast() {
  const showToast = (message: string, variant: ToastVariant = 'info', duration = 3000) => {
    const id = String(Date.now());
    toasts.value.push({ id, message, variant });

    if (duration > 0) {
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id);
      }, duration);
    }
  };

  const removeToast = (id: string) => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  };

  return {
    toasts,
    showToast,
    removeToast,
  };
}
