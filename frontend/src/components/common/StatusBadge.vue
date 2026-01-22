<template>
  <span class="status-badge" :class="statusClass">
    {{ statusText }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Status = 'pending' | 'loading' | 'done' | 'fail' | 'progress' | 'ready' | 'exported';

const props = withDefaults(defineProps<{
  status?: Status;
  customText?: string;
}>(), {
  status: 'pending',
});

const statusConfig: Record<Status, { text: string; class: string }> = {
  pending: { text: '未开始', class: 'status-badge--pending' },
  loading: { text: '生成中', class: 'status-badge--loading' },
  done: { text: '已完成', class: 'status-badge--done' },
  fail: { text: '失败', class: 'status-badge--fail' },
  progress: { text: '进行中', class: 'status-badge--progress' },
  ready: { text: '就绪', class: 'status-badge--ready' },
  exported: { text: '已导出', class: 'status-badge--exported' },
};

const statusText = computed(() => {
  return props.customText || statusConfig[props.status]?.text || props.status;
});

const statusClass = computed(() => {
  return statusConfig[props.status]?.class || 'status-badge--pending';
});
</script>

<style scoped>
.status-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  font-size: 11px;
  border: 1px solid;
}

.status-badge--pending {
  background: rgba(148, 163, 184, 0.08);
  color: #cbd5f5;
  border-color: rgba(148, 163, 184, 0.2);
}

.status-badge--loading {
  background: rgba(251, 191, 36, 0.15);
  color: #fcd34d;
  border-color: rgba(251, 191, 36, 0.3);
}

.status-badge--done,
.status-badge--ready {
  background: rgba(var(--md-accent-rgb), 0.12);
  color: #b8f4ff;
  border-color: rgba(var(--md-accent-rgb), 0.35);
}

.status-badge--fail {
  background: rgba(248, 113, 113, 0.15);
  color: #fecdd3;
  border-color: rgba(248, 113, 113, 0.3);
}

.status-badge--progress {
  background: rgba(251, 191, 36, 0.18);
  color: #fcd34d;
  border-color: rgba(251, 191, 36, 0.35);
}

.status-badge--exported {
  background: rgba(var(--md-accent-2-rgb), 0.18);
  color: #a7f3d0;
  border-color: rgba(var(--md-accent-2-rgb), 0.35);
}
</style>
