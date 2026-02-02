<template>
  <!-- API Settings Modal | API 设置弹窗 -->
  <n-modal v-model:show="showModal" preset="card" :title="$t('common.api_settings')" style="width: 480px;">
    <n-form ref="formRef" :model="formData" label-placement="left" label-width="80">
      
      <n-form-item label="Base URL" path="baseUrl">
        <n-input 
        v-model:value="formData.baseUrl" 
        placeholder="https://api.z.ai/api/paas/v4"
        />
      </n-form-item>
      <n-form-item label="API Key" path="apiKey">
        <n-input 
          v-model:value="formData.apiKey" 
          type="password"
          show-password-on="click"
          :placeholder="$t('common.enter_api_key')"
        />
      </n-form-item>

      <!-- 三方渠道端点配置 -->
      <!-- <n-divider title-placement="left" class="!my-3">
        <span class="text-xs text-[var(--text-secondary)]">端点路径</span>
      </n-divider>
      
      <div class="endpoint-list">
        <div class="endpoint-item">
          <span class="endpoint-label">问答</span>
          <n-tag size="small" type="info" class="endpoint-tag">/chat/completions</n-tag>
        </div>
        <div class="endpoint-item">
          <span class="endpoint-label">生图</span>
          <n-tag size="small" type="success" class="endpoint-tag">/images/generations</n-tag>
        </div>
        <div class="endpoint-item">
          <span class="endpoint-label">视频生成</span>
          <n-tag size="small" type="warning" class="endpoint-tag">/videos</n-tag>
        </div>
        <div class="endpoint-item">
          <span class="endpoint-label">视频查询</span>
          <n-tag size="small" type="warning" class="endpoint-tag">/videos/{taskId}</n-tag>
        </div>
      </div> -->

      <n-alert v-if="!isConfigured" type="warning" :title="$t('common.not_configured')" class="mb-4">
        <div class="flex flex-col gap-2">
          <p>{{ $t('common.configure_api_key_desc') }}</p>
          <a 
            href="https://chat.z.ai/auth?response_type=code&client_id=client_lS94_Ka2ycE9IwCNYisudg&redirect_uri=https%3A%2F%2Fz.ai%2Flogin%2Fcallback%3Fredirect%3D%2525252Fmodel-api&state=1768882184504" 
            target="_blank"
            class="text-[var(--accent-color)] hover:underline text-sm flex items-center gap-1"
          >
            🔗 {{ $t('common.get_api_key') }}
            <span class="text-xs">{{ $t('common.new_user_register') }}</span>
          </a>
        </div>
      </n-alert>

      <n-alert v-else type="success" :title="$t('common.configured')" class="mb-4">
        {{ $t('common.api_ready_desc') }}
      </n-alert>
    </n-form>

    <template #footer>
      <div class="flex justify-between items-center">
        <a 
          href="https://chat.z.ai/auth?response_type=code&client_id=client_lS94_Ka2ycE9IwCNYisudg&redirect_uri=https%3A%2F%2Fz.ai%2Flogin%2Fcallback%3Fredirect%3D%2525252Fmodel-api&state=1768882184504" 
          target="_blank"
          class="text-xs text-[var(--text-secondary)] hover:text-[var(--accent-color)] transition-colors"
        >
          没有 API Key？点击注册
        </a>
        <div class="flex gap-2">
          <n-button @click="handleClear" tertiary>清除配置</n-button>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave">保存</n-button>
        </div>
      </div>
    </template>
  </n-modal>
</template>

<script setup>
/**
 * API Settings Component | API 设置组件
 * Modal for configuring API key and base URL
 */
import { ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NModal, NForm, NFormItem, NInput, NButton, NAlert, NDivider, NTag } from 'naive-ui'
import { useApiConfig } from '../hooks'

const { t } = useI18n()

// Props | 属性
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

// Emits | 事件
const emit = defineEmits(['update:show', 'saved'])

// API Config hook | API 配置 hook
const { apiKey, baseUrl, isConfigured, setApiKey, setBaseUrl, clear: clearConfig } = useApiConfig()

// Modal visibility | 弹窗可见性
const showModal = ref(props.show)

// Form data | 表单数据
const formData = reactive({
  apiKey: apiKey.value,
  baseUrl: baseUrl.value
})

// Watch prop changes | 监听属性变化
watch(() => props.show, (val) => {
  showModal.value = val
  if (val) {
    formData.apiKey = apiKey.value
    formData.baseUrl = baseUrl.value
  }
})

// Watch modal changes | 监听弹窗变化
watch(showModal, (val) => {
  emit('update:show', val)
})

// Handle save | 处理保存
const handleSave = () => {
  if (formData.apiKey) {
    setApiKey(formData.apiKey)
  }
  if (formData.baseUrl) {
    setBaseUrl(formData.baseUrl)
  }
  showModal.value = false
  emit('saved')
}

// Handle clear | 处理清除
const handleClear = () => {
  clearConfig()
  formData.apiKey = ''
  formData.baseUrl = 'https://api.z.ai/api/paas/v4/'
}
</script>

<style scoped>
.endpoint-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 6px;
}

.endpoint-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.endpoint-label {
  font-size: 13px;
  color: var(--text-secondary, #666);
  min-width: 70px;
}

.endpoint-tag {
  font-family: monospace;
  font-size: 12px;
}
</style>
