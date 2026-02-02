<template>
  <!-- Workflow panel | 工作流面板 -->
  <n-drawer v-model:show="visible" :width="360" placement="left">
    <n-drawer-content :title="$t('canvas.workflow_templates')" closable>
      <!-- Tabs | 标签页 -->
      <n-tabs type="line" animated>
        <n-tab-pane name="public" :tab="$t('canvas.public_workflows')">
          <div class="workflow-list">
            <div 
              v-for="workflow in publicWorkflows" 
              :key="workflow.id"
              class="workflow-card"
              @click="handleAddWorkflow(workflow)"
            >
              <div class="workflow-icon">
                <n-icon :size="32">
                  <component :is="getIcon(workflow.icon)" />
                </n-icon>
              </div>
              <div class="workflow-info">
                <div class="workflow-name">{{ $t(workflow.nameKey) || workflow.name }}</div>
                <div class="workflow-desc">{{ $t(workflow.descKey) || workflow.description }}</div>
              </div>
              <div class="workflow-add">
                <n-button size="small" type="primary" quaternary>
                  <template #icon>
                    <n-icon><AddOutline /></n-icon>
                  </template>
                </n-button>
              </div>
            </div>
          </div>
        </n-tab-pane>
        <n-tab-pane name="my" :tab="$t('canvas.my_workflows')">
          <div class="empty-state">
            <n-icon :size="48" class="text-gray-400">
              <FolderOpenOutline />
            </n-icon>
            <p class="text-gray-500 mt-2">{{ $t('canvas.no_custom_workflows') }}</p>
          </div>
        </n-tab-pane>
      </n-tabs>

      </n-drawer-content>
  </n-drawer>
</template>

<script setup>
/**
 * Workflow Panel Component | 工作流面板组件
 * 显示工作流模板列表，支持一键添加到画布
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NDrawer, NDrawerContent, NTabs, NTabPane, NIcon, NButton } from 'naive-ui'
import { 
  AddOutline, 
  GridOutline, 
  ImageOutline, 
  VideocamOutline,
  FolderOpenOutline 
} from '@vicons/ionicons5'
import { WORKFLOW_TEMPLATES } from '../config/workflows'

const { t } = useI18n()

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['update:show', 'add-workflow'])

// Visible state | 显示状态
const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

// Public workflows | 公共工作流
const publicWorkflows = computed(() => WORKFLOW_TEMPLATES)

// Icon mapping | 图标映射
const iconMap = {
  GridOutline,
  ImageOutline,
  VideocamOutline
}

const getIcon = (iconName) => {
  return iconMap[iconName] || GridOutline
}

// Handle add workflow | 处理添加工作流
const handleAddWorkflow = (workflow) => {
  // 直接添加工作流，节点内容由用户自己填写
  emit('add-workflow', { workflow, options: {} })
  visible.value = false
}
</script>

<style scoped>
.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.workflow-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.workflow-card:hover {
  border-color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.workflow-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--bg-tertiary);
  color: var(--accent-color);
}

.workflow-info {
  flex: 1;
  min-width: 0;
}

.workflow-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.workflow-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-add {
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}
</style>
