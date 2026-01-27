<template>
  <Teleport to="body">
    <div v-if="show" class="api-modal">
      <div class="api-modal__backdrop" @click="handleClose"></div>
      <div class="api-modal__panel">
        <div class="api-modal__header">
          <div>
            <div class="api-modal__title">API 设置</div>
            <div class="api-modal__subtitle">绑定调用平台与 API Key（仅后端保存）</div>
          </div>
          <button class="api-modal__close" @click="handleClose">×</button>
        </div>

        <div class="api-modal__body">
          <label class="field-label">调用平台</label>
          <select v-model="apiBase" class="field">
            <option value="https://bigmodel.cn">https://bigmodel.cn</option>
            <option value="https://chat.z.ai">https://chat.z.ai</option>
          </select>

          <label class="field-label">API Key</label>
          <input
            v-model="apiKey"
            class="field"
            type="password"
            placeholder="输入后端保存，不会在前端持久化"
          />
          <div class="field-hint">
            状态：{{ hasApiKey ? '已绑定' : '未绑定' }}
          </div>
        </div>

        <div class="api-modal__footer">
          <div class="footer-hint">
            未配置 API Key 将无法进行素材生成。
          </div>
          <div class="footer-actions">
            <button class="ghost-btn" @click="handleClose">取消</button>
            <button class="primary-btn" :disabled="saving" @click="handleSave">
              {{ saving ? '保存中...' : '保存设置' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import { fetchLlmSettings, updateLlmSettings } from '@/api/llmSettings';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'saved'): void;
}>();

const apiBase = ref('https://bigmodel.cn');
const apiKey = ref('');
const hasApiKey = ref(false);
const saving = ref(false);

const loadSettings = async () => {
  try {
    const data = await fetchLlmSettings();
    apiBase.value = data.api_base || 'https://bigmodel.cn';
    hasApiKey.value = Boolean(data.has_api_key);
    sessionStorage.setItem('llmConfigured', hasApiKey.value ? 'true' : 'false');
    sessionStorage.setItem('llmApiBase', data.api_base || '');
  } catch (err) {
    alert(err instanceof Error ? err.message : '加载 API 设置失败');
  }
};

const handleSave = async () => {
  if (!apiBase.value) {
    alert('请选择调用平台');
    return;
  }
  if (!apiKey.value && !hasApiKey.value) {
    alert('请输入 API Key');
    return;
  }
  saving.value = true;
  try {
    const data = await updateLlmSettings({
      api_base: apiBase.value,
      api_key: apiKey.value || undefined,
    });
    hasApiKey.value = Boolean(data.has_api_key);
    apiKey.value = '';
    sessionStorage.setItem('llmConfigured', hasApiKey.value ? 'true' : 'false');
    sessionStorage.setItem('llmApiBase', data.api_base || '');
    emit('saved');
    emit('update:show', false);
  } catch (err) {
    alert(err instanceof Error ? err.message : '保存失败');
  } finally {
    saving.value = false;
  }
};

const handleClose = () => {
  emit('update:show', false);
};

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      apiKey.value = '';
      loadSettings();
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.api-modal {
  position: fixed;
  inset: 0;
  z-index: var(--layer-modal);
  display: flex;
  align-items: center;
  justify-content: center;
}

.api-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(6, 10, 18, 0.7);
  backdrop-filter: blur(6px);
}

.api-modal__panel {
  position: relative;
  z-index: 1;
  width: min(520px, 92vw);
  background: rgba(12, 18, 28, 0.95);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--md-card-shadow);
}

.api-modal__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.api-modal__title {
  font-size: 18px;
  font-weight: 600;
}

.api-modal__subtitle {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-top: 6px;
}

.api-modal__close {
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  font-size: 20px;
  cursor: pointer;
}

.api-modal__body {
  display: grid;
  gap: 10px;
}

.field-label {
  font-size: 13px;
  color: var(--md-on-surface-variant);
}

.field {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: rgba(5, 10, 18, 0.9);
  color: var(--md-on-surface);
}

.field-hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.api-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
}

.footer-hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.primary-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  color: #0c0f1a;
  background: #e8eef7;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost-btn {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: transparent;
  color: var(--md-on-surface);
  cursor: pointer;
}
</style>
