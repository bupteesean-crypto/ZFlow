<template>
  <div class="api-settings-page">
    <ApiSettingsModal v-model:show="showModal" @saved="handleSaved" />
    <div class="page-hint">
      <div>API 设置弹窗已打开，如未显示可点击下方按钮。</div>
      <button class="primary-btn" @click="showModal = true">打开 API 设置</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import ApiSettingsModal from '@/components/ApiSettingsModal.vue';

const router = useRouter();
const route = useRoute();
const showModal = ref(true);

const handleSaved = () => {
  const redirect = route.query.redirect;
  if (typeof redirect === 'string' && redirect.length > 0) {
    router.push(redirect);
  } else {
    router.push('/');
  }
};
</script>

<style scoped>
.api-settings-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--md-on-surface-variant);
  text-align: center;
  gap: 12px;
  flex-direction: column;
}

.primary-btn {
  padding: 10px 18px;
  border-radius: 10px;
  border: none;
  color: #0c0f1a;
  background: #e8eef7;
  font-weight: 600;
  cursor: pointer;
}
</style>
