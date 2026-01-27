<template>
  <!-- Download Modal | 下载弹窗 -->
  <n-modal v-model:show="visible" preset="card" :title="$t('canvas.asset_download')" style="width: 600px; max-width: 90vw;">
    <div class="space-y-4">
      <!-- Stats | 统计 -->
      <div class="flex items-center gap-4 text-sm text-[var(--text-secondary)]">
        <span>{{ $t('node.image') }}: {{ imageAssets.length }} {{ $t('common.unit_sheet') }}</span>
        <span>{{ $t('node.video') }}: {{ videoAssets.length }} {{ $t('common.unit_count') }}</span>
      </div>

      <!-- Image assets | 图片素材 -->
      <div v-if="imageAssets.length > 0">
        <h4 class="text-sm font-medium mb-2">{{ $t('canvas.image_assets') }}</h4>
        <div class="grid grid-cols-4 gap-2 max-h-[200px] overflow-y-auto">
          <div 
            v-for="(asset, idx) in imageAssets" 
            :key="idx"
            class="relative aspect-square rounded-lg overflow-hidden bg-[var(--bg-tertiary)] cursor-pointer group"
            @click="downloadAsset(asset)"
          >
            <img :src="asset.url" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <n-icon :size="24" color="white"><DownloadOutline /></n-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- Video assets | 视频素材 -->
      <div v-if="videoAssets.length > 0">
        <h4 class="text-sm font-medium mb-2">{{ $t('canvas.video_assets') }}</h4>
        <div class="space-y-2 max-h-[200px] overflow-y-auto">
          <div 
            v-for="(asset, idx) in videoAssets" 
            :key="idx"
            class="flex items-center gap-3 p-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
            @click="downloadAsset(asset)"
          >
            <div class="w-16 h-10 rounded bg-[var(--bg-primary)] flex items-center justify-center">
              <n-icon :size="20"><VideocamOutline /></n-icon>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm truncate">{{ asset.label || $t('node.video') }}</div>
              <div class="text-xs text-[var(--text-secondary)]">{{ asset.duration ? asset.duration + 's' : '' }}</div>
            </div>
            <n-icon :size="20" class="text-[var(--text-secondary)]"><DownloadOutline /></n-icon>
          </div>
        </div>
      </div>

      <!-- Empty state | 空状态 -->
      <div v-if="imageAssets.length === 0 && videoAssets.length === 0" class="text-center py-8 text-[var(--text-secondary)]">
        {{ $t('canvas.no_downloadable_assets') }}
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end">
        <n-button @click="visible = false">{{ $t('common.close') }}</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup>
/**
 * Download Modal Component | 下载弹窗组件
 * Display and download image/video assets from canvas nodes
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NModal, NButton, NIcon } from 'naive-ui'
import { DownloadOutline, VideocamOutline } from '@vicons/ionicons5'
import { nodes } from '../stores/canvas'

const { t } = useI18n()

// Props | 属性
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

// Emits | 事件
const emit = defineEmits(['update:show'])

// Visible state with v-model support | 支持 v-model 的显示状态
const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

// Get downloadable image assets | 获取可下载的图片素材
const imageAssets = computed(() => {
  return nodes.value
    .filter(n => n.type === 'image' && n.data?.url)
    .map(n => ({
      url: n.data.url,
      label: n.data.label || t('node.image'),
      nodeId: n.id
    }))
})

// Get downloadable video assets | 获取可下载的视频素材
const videoAssets = computed(() => {
  return nodes.value
    .filter(n => n.type === 'video' && n.data?.url)
    .map(n => ({
      url: n.data.url,
      label: n.data.label || t('node.video'),
      duration: n.data.duration,
      nodeId: n.id
    }))
})

// Download single asset | 下载单个素材
const downloadAsset = (asset) => {
  window.open(asset.url, '_blank')
  window.$message?.success(t('common.opened_in_new_tab'))
}
</script>
