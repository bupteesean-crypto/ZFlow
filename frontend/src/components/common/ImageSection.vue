<template>
  <section class="section">
    <h3>生成图片</h3>
    <div v-if="images.length === 0" class="empty-text">
      暂无图片（图像生成为尽力而为）。
    </div>
    <div v-else class="image-grid">
      <div
        v-for="(item, idx) in images"
        :key="`${item.url}-${idx}`"
        :class="['image-card', { selected: isSelected(item), loading: isLoading(item) }]"
        :title="buildPromptTooltip(item)"
        @click="emit('select', item)"
      >
        <img :src="item.url" :alt="item.prompt || '生成图片'" class="image" />
        <div v-if="item.isActive" class="active-badge">✅</div>
        <div class="meta">
          <div class="prompt">{{ item.prompt || '暂无提示词' }}</div>
          <div class="provider">
            {{ item.provider || 'unknown' }} / {{ item.model || 'unknown' }} / {{ item.size || '-' }}
          </div>
        </div>
      </div>
      <div v-if="showLoadingPlaceholder" class="image-card loading-card">
        <div class="loading-text">生成中...</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
type ImageItem = {
  id?: string;
  url: string;
  prompt?: string;
  promptSource?: string;
  provider?: string;
  model?: string;
  size?: string;
  isActive?: boolean;
  type?: string;
  sceneId?: string;
  subjectId?: string;
  view?: string;
  promptParts?: {
    content?: string;
    style?: string;
    constraints?: string;
  };
};

const props = defineProps<{
  images: ImageItem[];
  selectedImageId?: string;
  loadingGroupKey?: string;
  isLoading?: boolean;
  showLoadingPlaceholder?: boolean;
}>();

const emit = defineEmits<{
  (event: "select", image: ImageItem): void;
}>();


const formatPromptSource = (source?: string) => {
  const normalized = (source || '').trim();
  if (normalized === 'user_edit') return '直接编辑';
  if (normalized === 'user_feedback') return '修改意见生成';
  if (normalized === 'art_style_propagation') return '风格传播';
  if (normalized) return normalized;
  return '系统生成';
};

const buildPromptTooltip = (item: ImageItem) => {
  const prompt = item.prompt || '暂无提示词';
  return `提示词：${prompt}\n来源：${formatPromptSource(item.promptSource)}`;
};

const getGroupKey = (item: ImageItem) => {
  const type = item.type || 'scene';
  if (item.subjectId && type === 'character_sheet') {
    return `subject:${item.subjectId}:${type}`;
  }
  if (item.subjectId && item.view) {
    return `subject:${item.subjectId}:${item.view}:${type}`;
  }
  if (item.sceneId) {
    return `scene:${item.sceneId}:${type}`;
  }
  return `single:${item.id || item.url}`;
};

const isSelected = (item: ImageItem) => {
  if (!props.selectedImageId) return false;
  return Boolean(item.id && item.id === props.selectedImageId);
};

const isLoading = (item: ImageItem) => {
  if (!props.isLoading || !props.loadingGroupKey) return false;
  return props.loadingGroupKey === getGroupKey(item);
};
</script>

<style scoped>
.section {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  padding: 14px;
}

.section h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.empty-text {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.image-card {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  overflow: hidden;
  background: var(--md-surface);
  position: relative;
}

.image-card.selected {
  border-color: rgba(103, 80, 164, 0.8);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.25);
}

.image-card.loading {
  opacity: 0.7;
}

.image {
  display: block;
  width: 100%;
  height: 120px;
  object-fit: cover;
  background: rgba(0, 0, 0, 0.04);
}

.active-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 2px 6px;
  border-radius: 999px;
}

.loading-card {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 180px;
  color: var(--md-on-surface-variant);
  font-size: 12px;
  border-style: dashed;
}

.loading-text {
  padding: 8px;
}

.meta {
  padding: 8px;
}

.prompt {
  font-size: 12px;
  color: var(--md-on-surface);
  margin-bottom: 4px;
  max-height: 48px;
  overflow: hidden;
}

.provider {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

</style>
