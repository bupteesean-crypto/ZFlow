<template>
  <div :class="['candidate-row', `candidate-row--${type}`]">
    <div
      v-for="(item, index) in items"
      :key="index"
      :class="['candidate-card', { active: item.selected }]"
      @click="handleSelect(item)"
    >
      <div class="candidate-top">
        <span class="candidate-tag">{{ item.tag }}</span>
        <span v-if="item.selected" class="candidate-check">当前使用</span>
      </div>
      <div class="candidate-body">
        <!-- Image type -->
        <template v-if="type === 'image'">
          <div class="asset-thumb img-card">
            <img v-if="item.img" :src="item.img" alt="" @error="handleImageError" />
            <div v-else class="placeholder">预览</div>
          </div>
          <div class="text-xs text-slate-400">{{ item.text }}</div>
        </template>
        <!-- Audio type -->
        <template v-else-if="type === 'audio'">
          <div class="asset-media full-audio">
            <audio controls :src="item.audio" class="w-full"></audio>
          </div>
          <div class="text-xs text-slate-400">{{ item.text }}</div>
        </template>
        <!-- Text type -->
        <template v-else>
          <div class="text-content text-sm text-slate-200">{{ truncateText(item.text) }}</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface CandidateItem {
  tag: string;
  text: string;
  img?: string;
  audio?: string;
  prompt?: string;
  selected: boolean;
}

const props = defineProps<{
  items: CandidateItem[];
  type?: 'image' | 'audio' | 'text';
}>();

const emit = defineEmits<{
  select: [item: CandidateItem];
}>();

const handleSelect = (item: CandidateItem) => {
  emit('select', item);
};

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.style.display = 'none';
};

const truncateText = (text: string) => {
  if (!text) return '';
  if (text.length <= 100) return text;
  return text.substring(0, 100) + '...';
};
</script>

<style scoped>
.candidate-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 6px;
}

.candidate-row.text-mode {
  flex-direction: column;
  overflow: visible;
}

.candidate-row.text-mode .candidate-card {
  width: 100%;
  min-width: 0;
}

.candidate-row.audio-mode {
  flex-direction: column;
  overflow: visible;
}

.candidate-row.audio-mode .candidate-card {
  width: 100%;
  min-width: 0;
}

.candidate-card {
  min-width: 240px;
  width: 240px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.candidate-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
}

.candidate-card.active {
  border-color: rgba(108, 249, 224, 0.5);
  background: rgba(108, 249, 224, 0.1);
}

.candidate-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.candidate-tag {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.35);
  color: #c7d2fe;
  white-space: nowrap;
}

.candidate-check {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(108, 249, 224, 0.18);
  color: #9cfbe6;
  border: 1px solid rgba(108, 249, 224, 0.3);
  white-space: nowrap;
}

.candidate-body {
  flex: 1;
}

.asset-thumb {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.03);
}

.img-card {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.img-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.img-card .placeholder {
  color: #9bb0e0;
  font-size: 13px;
}

.asset-media {
  margin-top: 4px;
}

.full-audio audio {
  width: 100%;
  height: 32px;
}

.text-content {
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 12px;
}

</style>
