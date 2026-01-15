<template>
  <div class="async-state">
    <div v-if="loading" class="state-card">
      <div class="state-spinner"></div>
      <div class="state-text">{{ loadingText }}</div>
    </div>
    <div v-else-if="error" class="state-card state-card--error">
      <div class="state-title">加载失败</div>
      <div class="state-text">{{ error }}</div>
      <button v-if="showRetry" class="state-btn" type="button" @click="$emit('retry')">
        {{ retryLabel }}
      </button>
    </div>
    <div v-else-if="empty" class="state-card state-card--empty">
      <div class="state-title">{{ emptyTitle }}</div>
      <div class="state-text">{{ emptyText }}</div>
    </div>
    <div v-else class="state-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  loading: boolean;
  error?: string | null;
  empty?: boolean;
  loadingText?: string;
  emptyTitle?: string;
  emptyText?: string;
  retryLabel?: string;
  showRetry?: boolean;
}>(), {
  loadingText: '加载中...',
  emptyTitle: '暂无内容',
  emptyText: '暂时没有可以展示的数据。',
  retryLabel: '重试',
  showRetry: true,
});

defineEmits<{
  retry: [];
}>();
</script>

<style scoped>
.async-state {
  width: 100%;
}

.state-card {
  min-height: 140px;
  border-radius: 14px;
  border: 1px solid rgba(121, 116, 126, 0.18);
  background: var(--md-surface-container);
  color: var(--md-on-surface);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 24px;
}

.state-card--error {
  border-color: rgba(180, 35, 24, 0.35);
  background: rgba(255, 234, 236, 0.6);
  color: #7a1b12;
}

.state-card--empty {
  color: var(--md-on-surface-variant);
  background: var(--md-surface-container-low);
}

.state-title {
  font-weight: 600;
  font-size: 15px;
}

.state-text {
  font-size: 13px;
  line-height: 1.6;
}

.state-btn {
  border: none;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  background: var(--md-primary);
  color: var(--md-on-primary);
  cursor: pointer;
}

.state-spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid rgba(103, 80, 164, 0.2);
  border-top-color: var(--md-primary);
  animation: spin 0.8s linear infinite;
}

.state-body {
  width: 100%;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
