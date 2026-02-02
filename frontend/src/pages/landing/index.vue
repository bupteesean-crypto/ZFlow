<template>
  <div class="landing-page cyber-grid">
    <!-- Hero Section -->
    <section class="hero-section">
      <div :class="['hero-content', { 'hero-sticky-shrunk': isShrunk }]">
        <div class="hero-badge">AI 驱动的视频创作平台</div>
        <h1 class="hero-title">
          将你的想法<br />
          转化为<span class="glow-text">精彩视频</span>
        </h1>
        <p class="hero-sub">
          通过自然语言对话，生成角色、场景、分镜与完整视频。
          <br />适合创作者、营销团队与视频爱好者。
        </p>
      </div>

      <!-- Expandable Prompt Input -->
      <div :class="['entry-shell', { expanded: isExpanded, minimal: isMinimal }]">
        <div class="mode-toggle" :class="mode">
          <span class="mode-pill"></span>
          <button type="button" @click="mode = 'general'">通用</button>
          <button type="button" @click="mode = 'pro'">专业</button>
        </div>

        <div class="entry-line">
          <textarea
            ref="textareaRef"
            v-model="prompt"
            placeholder="输入你想要生成的视频描述，例如：一个女孩在海边散步，阳光明媚"
            @focus="handleFocus"
            @blur="handleBlur"
            @input="handleInput"
          />
          <button class="entry-submit" :disabled="!canSubmit" @click="handleSubmit">
            {{ submitLabel }}
          </button>
        </div>

        <div v-if="isExpanded" class="entry-extra">
          <div class="helper-row">
            <span :class="['count', countClass]">{{ prompt.length }} / {{ maxPromptLength }}</span>
            <span class="mode-hint">{{ countHint }}</span>
          </div>

          <div v-if="mode === 'general'" class="input-actions">
            <span class="action-label">一句话描述即可生成完整素材包</span>
          </div>

          <div v-else class="pro-config">
            <div class="config-block">
              <div class="config-title">附件导入</div>
              <div class="config-hint">先上传素材，再选择用途，系统会据此优化生成。</div>
              <div class="upload-box" @click="triggerFileSelect" @dragover.prevent @drop.prevent="handleDrop">
                <input ref="fileInputRef" type="file" multiple class="file-input" @change="handleFileChange" />
                <div class="upload-text">拖拽或点击上传素材</div>
                <div class="upload-hint">支持图片/音频/视频/PDF/Word/TXT，单文件建议 &lt; 50MB</div>
              </div>
              <div v-if="attachments.length" class="upload-actions">
                <button class="btn-ghost small" @click="applyRecommendedBindings">一键套用推荐</button>
                <button class="btn-ghost small" @click="bindAllImagesAsCharacter">图片全部绑定为角色参考</button>
                <div class="upload-batch">
                  <input
                    v-model="batchLabel"
                    class="config-input compact"
                    placeholder="批量备注（如：角色参考）"
                  />
                  <button class="btn-ghost small" @click="applyBatchLabel">应用备注</button>
                </div>
              </div>
              <div v-if="hasUnboundAttachments" class="upload-reminder">请为每个附件选择用途，未绑定的文件不会参与生成。</div>
              <div v-if="attachments.length" class="upload-list">
                <div v-for="item in attachments" :key="item.localId" class="upload-item">
                  <div class="upload-info">
                    <div class="upload-name">{{ item.name }}</div>
                    <div class="upload-meta">{{ formatFileMeta(item) }}</div>
                    <div v-if="item.error" class="upload-error">{{ item.error }}</div>
                  </div>
                  <div class="upload-controls">
                    <select v-model="item.bindType" class="config-select" @change="syncAttachment(item)">
                      <option value="">未绑定</option>
                      <option value="character">角色参考</option>
                      <option value="scene">场景参考</option>
                      <option value="storyboard">分镜大纲</option>
                      <option value="script">剧本</option>
                      <option value="audio">旁白/音效</option>
                      <option value="other">其他</option>
                    </select>
                    <input
                      v-model="item.label"
                      class="config-input"
                      placeholder="用途/备注（如：角色形象参考）"
                      @blur="syncAttachment(item)"
                    />
                  </div>
                  <div class="upload-recommend">
                    <span class="recommend-text">
                      推荐用途：{{ bindTypeLabel(getRecommendedBindType(item)) }}
                      <span v-if="!item.bindType" class="recommend-warn">未绑定</span>
                    </span>
                    <button class="btn-ghost small" @click="applyRecommendedBinding(item)">套用推荐</button>
                  </div>
                  <div class="upload-progress" v-if="item.status === 'uploading'">
                    <div class="upload-progress-bar" :style="{ width: item.progress + '%' }"></div>
                  </div>
                  <div v-else class="upload-status">
                    <span :class="['status-pill', item.status === 'failed' ? 'danger' : 'ok']">
                      {{ item.status === 'failed' ? '上传失败' : '上传完成' }}
                    </span>
                    <span class="status-divider">｜</span>
                    <span class="status-parse">解析：{{ item.parseStatusLabel }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="config-advanced-toggle">
              <button class="btn-ghost" @click="showAdvanced = !showAdvanced">
                {{ showAdvanced ? '收起高级配置' : '下一步：完善配置' }}
              </button>
              <span class="advanced-hint">包含模型、主体、风格、画幅、时长</span>
            </div>

            <div v-if="showAdvanced" class="config-advanced">
              <div class="config-block">
                <div class="config-title">模型选择</div>
                <div class="model-columns">
                  <div class="model-column">
                    <div class="model-column-title">文生图模型</div>
                    <div class="model-chip-group">
                      <button
                        v-for="model in imageModels"
                        :key="`txt-${model.id}`"
                        :class="['model-chip', { active: selectedModels.image === model.id, disabled: !model.enabled }]"
                        :disabled="!model.enabled"
                        @click="selectImageModel(model.id)"
                      >
                        {{ model.label }}
                      </button>
                      <span v-if="imageModels.length === 0" class="model-empty">暂无模型</span>
                    </div>
                  </div>
                  <div class="model-column">
                    <div class="model-column-title">图文生图模型</div>
                    <div class="model-chip-group">
                      <button
                        v-for="model in imageModels"
                        :key="`ref-${model.id}`"
                        :class="['model-chip', { active: selectedModels.imageRef === model.id, disabled: !model.enabled }]"
                        :disabled="!model.enabled"
                        @click="selectImageRefModel(model.id)"
                      >
                        {{ model.label }}
                      </button>
                      <span v-if="imageModels.length === 0" class="model-empty">暂无模型</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="config-block">
                <div class="config-title">主体设定</div>
                <div class="subject-input-grid">
                  <input v-model="subjectNameInput" class="config-input" placeholder="主体名称（如：女孩 / 小猪）" />
                  <input v-model="subjectDescInput" class="config-input" placeholder="一句话描述（可选）" />
                  <button class="btn-ghost" @click="addSubjectItem">添加</button>
                </div>
                <div v-if="suggestedSubjects.length" class="subject-suggest">
                  <div class="suggest-header">
                    <span>来自角色参考：</span>
                    <button class="btn-ghost small" @click="addAllSuggestedSubjects">生成主体列表</button>
                  </div>
                  <div class="subject-suggest-list">
                    <button
                      v-for="name in suggestedSubjects"
                      :key="name"
                      class="subject-suggest-chip"
                      @click="addSuggestedSubject(name)"
                    >
                      + {{ name }}
                    </button>
                  </div>
                </div>
                <div v-if="subjectItems.length" class="subject-list">
                  <div v-for="(item, index) in subjectItems" :key="`${item.name}-${index}`" class="subject-item">
                    <div class="subject-text">
                      <div class="subject-main">{{ item.name }}</div>
                      <div class="subject-desc">{{ item.description || '未填写描述' }}</div>
                    </div>
                    <button class="chip-remove" @click="removeSubjectItem(index)">移除</button>
                  </div>
                </div>
              </div>

              <div class="config-block">
                <div class="config-title">选择风格</div>
                <div class="style-row">
                  <button class="btn-ghost" @click="showStyleSelector = true">
                    {{ selectedStyle?.name || '选择风格' }}
                  </button>
                  <input v-model="customStyle" class="config-input" placeholder="自定义风格名称（可选）" />
                </div>
              </div>

              <div class="config-block config-grid">
                <div>
                  <div class="config-title">画幅</div>
                  <select v-model="aspectRatio" class="config-select">
                    <option v-for="option in aspectOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
                <div>
                  <div class="config-title">时长</div>
                  <select v-model="durationPreset" class="config-select">
                    <option v-for="option in durationOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <div v-if="durationPreset === 'custom'" class="duration-custom">
                    <input v-model="durationCustom.h" class="config-input small" placeholder="小时" />
                    <input v-model="durationCustom.m" class="config-input small" placeholder="分钟" />
                    <input v-model="durationCustom.s" class="config-input small" placeholder="秒" />
                  </div>
                </div>
              </div>

              <div class="config-preview">
                当前画幅：{{ aspectRatio }} ｜ 时长：{{ durationLabel }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showStyleSelector" class="style-selector-popover">
        <div class="style-selector-header">
          <div class="style-selector-title">选择风格</div>
          <button class="btn-ghost" @click="showStyleSelector = false">关闭</button>
        </div>
        <div class="style-grid">
          <button
            v-for="style in styleOptions"
            :key="style.id"
            :class="['style-card', { active: selectedStyle?.id === style.id }]"
            @click="pickStyle(style)"
          >
            <span class="style-swatch" :style="{ background: style.preview }"></span>
            <span>{{ style.name }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Inspiration Grid -->
    <section class="inspiration-section" :class="{ 'is-shrunk': isShrunk }">
      <h2 class="section-title">灵感示例</h2>
      <div class="inspiration-grid">
        <div
          v-for="card in inspirationCards"
          :key="card.id"
          class="demo-card glass-panel"
          @click="applyInspiration(card)"
        >
          <div class="card-image">{{ card.emoji }}</div>
          <div class="card-content">
            <h3>{{ card.title }}</h3>
            <p>{{ card.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Todo Progress (shown when generating) -->
    <div v-if="generating" class="generating-overlay">
      <div class="generating-box glass-panel neon-border">
        <h3>正在生成素材...</h3>
        <div class="todo-list">
          <div
            v-for="(item, index) in todoItems"
            :key="index"
            :class="['todo-item', `todo-item--${item.status}`]"
          >
            <span class="todo-icon">{{ getTodoIcon(item.status) }}</span>
            <span>{{ item.title }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { createProject, updateProject } from '@/api/projects';
import { fetchModels, type ModelOption } from '@/api/models';
import { createMaterialPackage } from '@/api/material-packages';
import { uploadAttachment, updateAttachment, type AttachmentItem } from '@/api/attachments';

interface TodoItem {
  title: string;
  status: 'pending' | 'loading' | 'done';
}

interface InspirationCard {
  id: string;
  emoji: string;
  title: string;
  description: string;
  prompt: string;
}

const router = useRouter();
const { showToast } = useToast();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const prompt = ref('');
const isExpanded = ref(false);
const isMinimal = ref(true);
const isShrunk = ref(false);
const mode = ref<'general' | 'pro'>('general');
const generating = ref(false);
const imageModels = ref<ModelOption[]>([]);
const selectedModels = ref<{ image: string; imageRef: string; video: string }>({
  image: '',
  imageRef: '',
  video: '',
});
const maxPromptLength = 10000;
const minPromptLength = 3;
const draftProjectId = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const attachments = ref<
  Array<
    AttachmentItem & {
      localId: string;
      name: string;
      progress: number;
      status: 'ready' | 'uploading' | 'failed';
      error?: string;
      bindType?: string;
      label?: string;
      parseStatusLabel: string;
    }
  >
>([]);
const showAdvanced = ref(false);
const batchLabel = ref('');
const subjectNameInput = ref('');
const subjectDescInput = ref('');
const subjectItems = ref<Array<{ name: string; description: string }>>([]);
const showStyleSelector = ref(false);
const customStyle = ref('');
const aspectRatio = ref('3:4');
const durationPreset = ref('auto');
const durationCustom = ref({ h: '', m: '', s: '' });

const inspirationCards: InspirationCard[] = [
  {
    id: '1',
    emoji: '🌾',
    title: '田园生活',
    description: 'Q版角色在微缩田园中劳作，治愈风格',
    prompt: '北京的田园生活。Q版妞妞与文文在田边劳作，红砖木屋、青瓦屋顶有青苔，微缩模型+童话绘本风格，远处隐约北京城市轮廓，安静治愈氛围。',
  },
  {
    id: '2',
    emoji: '🌃',
    title: '都市夜景',
    description: '浪漫西餐厅约会，北京夜景背景',
    prompt: '北京都市生活。微缩西餐厅内，文文与妞妞进行都市约会，窗外是北京夜景，雍和宫剪影，微缩模型+童话绘本风格。',
  },
  {
    id: '3',
    emoji: '🚀',
    title: '科幻冒险',
    description: '悬浮列车穿梭的霓虹城市',
    prompt: '未来城市冒险。悬浮列车穿梭在霓虹城市轨道站，多啦A梦与大雄的科幻冒险，赛博朋克风格。',
  },
  {
    id: '4',
    emoji: '🏫',
    title: '校园日常',
    description: '轻松愉快的校园生活片段',
    prompt: '校园日常任务。Q版角色在校园里的日常互动，明亮色彩，轻松愉快的氛围。',
  },
];

const todoItems = ref<TodoItem[]>([
  { title: '分析需求', status: 'pending' },
  { title: '生成脚本', status: 'pending' },
  { title: '生成素材', status: 'pending' },
  { title: '整理候选', status: 'pending' },
  { title: '回填结果', status: 'pending' },
]);

const countClass = computed(() => {
  const len = prompt.value.length;
  if (len > maxPromptLength) return 'count-error';
  if (len > maxPromptLength * 0.9) return 'count-warn';
  return len >= minPromptLength ? 'count-ok' : 'count-warn';
});

const countHint = computed(() => {
  const len = prompt.value.length;
  if (len < minPromptLength) {
    return `至少输入 ${minPromptLength} 字`;
  }
  if (len > maxPromptLength) {
    return '字数超出上限，请精简';
  }
  return '按 Enter 换行';
});

const canSubmit = computed(() => {
  const len = prompt.value.trim().length;
  return len >= minPromptLength && len <= maxPromptLength && !generating.value;
});

const submitLabel = computed(() => {
  if (generating.value) return '提交中...';
  return mode.value === 'pro' ? '开始创作' : '自动生成';
});

const styleOptions = [
  { id: 'popmart', name: '泡泡玛特', preview: 'linear-gradient(135deg, #ffd6e8, #ffe5f2)' },
  { id: 'animal', name: '动森风格', preview: 'linear-gradient(135deg, #bfe6c9, #e8f5d0)' },
  { id: 'toon3d', name: '卡通 3D', preview: 'linear-gradient(135deg, #c7d2ff, #f0d4ff)' },
  { id: 'disney', name: '迪士尼', preview: 'linear-gradient(135deg, #ffe0b2, #ffd180)' },
  { id: 'lego', name: '乐高风格', preview: 'linear-gradient(135deg, #ffec99, #ffd43b)' },
  { id: 'lowpoly', name: '低模风格', preview: 'linear-gradient(135deg, #d3f9d8, #b2f2bb)' },
  { id: 'ghibli', name: '吉卜力', preview: 'linear-gradient(135deg, #d0ebff, #a5d8ff)' },
  { id: 'live', name: '真人摄影', preview: 'linear-gradient(135deg, #e9ecef, #ced4da)' },
  { id: 'clay', name: '黏土风格', preview: 'linear-gradient(135deg, #ffe8cc, #ffd8a8)' },
  { id: 'snoopy', name: '史努比', preview: 'linear-gradient(135deg, #f1f3f5, #dee2e6)' },
  { id: 'line', name: '线性插画', preview: 'linear-gradient(135deg, #f8f9fa, #e9ecef)' },
];
const selectedStyle = ref<{ id: string; name: string; preview: string } | null>(null);

const aspectOptions = [
  { value: '16:9', label: '16:9（自然日常）' },
  { value: '4:3', label: '4:3（复古学院）' },
  { value: '2.35:1', label: '2.35:1（影院宽屏）' },
  { value: '19:16', label: '19:16（竖屏亲近）' },
  { value: '3:4', label: '3:4（默认）' },
];

const durationOptions = [
  { value: 'auto', label: '智能' },
  { value: '5', label: '5 秒' },
  { value: '10', label: '10 秒' },
  { value: '15', label: '15 秒' },
  { value: '20', label: '20 秒' },
  { value: '30', label: '30 秒' },
  { value: '45', label: '45 秒' },
  { value: '60', label: '60 秒' },
  { value: 'custom', label: '自定义' },
];

const durationLabel = computed(() => {
  if (durationPreset.value === 'auto') return '智能';
  if (durationPreset.value === 'custom') {
    const seconds = resolveDurationSeconds();
    if (!seconds) return '自定义';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
  }
  return `${durationPreset.value}秒`;
});

const handleFocus = () => {
  isExpanded.value = true;
  isMinimal.value = false;
};

const handleBlur = (e: FocusEvent) => {
  // Keep expanded if clicking inside the entry shell
  const target = e.relatedTarget as HTMLElement;
  if (target?.closest('.entry-shell') || target?.closest('.style-selector-popover')) return;
  if (prompt.value.length === 0) {
    isMinimal.value = true;
  }
  isExpanded.value = false;
};

const handleInput = () => {
  // Auto-resize textarea
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px';
  }
};

const resolveDurationSeconds = () => {
  if (durationPreset.value !== 'custom') {
    const seconds = Number(durationPreset.value);
    return Number.isFinite(seconds) ? seconds : 0;
  }
  const h = Number(durationCustom.value.h || 0);
  const m = Number(durationCustom.value.m || 0);
  const s = Number(durationCustom.value.s || 0);
  if (!Number.isFinite(h) || !Number.isFinite(m) || !Number.isFinite(s)) {
    return 0;
  }
  if (m >= 60 || s >= 60) {
    return 0;
  }
  return Math.max(0, Math.floor(h * 3600 + m * 60 + s));
};

const buildInputConfig = () => {
  const durationSec = durationPreset.value === 'auto' ? null : resolveDurationSeconds();
  const subjects = subjectItems.value
    .map(item => ({
      name: item.name.trim(),
      description: item.description.trim(),
    }))
    .filter(item => item.name);
  return {
    aspect_ratio: aspectRatio.value,
    duration_sec: durationSec || undefined,
    style_name: customStyle.value.trim() || selectedStyle.value?.name || '',
    subject_seeds: subjects.map(item => item.name),
    subjects,
    image_model_id: selectedModels.value.image || '',
    image_ref_model_id: selectedModels.value.imageRef || '',
  };
};

const buildDocumentsPayload = () => {
  return attachments.value
    .filter(item => item.status === 'ready' && item.id)
    .map(item => ({
      id: item.id,
      name: item.filename || item.name,
      category: item.category,
      content_type: item.content_type,
      url: item.url,
      label: item.label || '',
      bind_type: item.bindType || '',
      tags: item.tags || [],
      parsed_text: item.parsed_text || '',
    }));
};

const formatFileMeta = (item: AttachmentItem & { name: string; parseStatusLabel: string }) => {
  const sizeMb = item.size ? `${(item.size / (1024 * 1024)).toFixed(1)} MB` : '未知大小';
  const categoryMap: Record<string, string> = {
    image: '图片',
    audio: '音频',
    video: '视频',
    document: '文档',
  };
  const categoryLabel = categoryMap[item.category || ''] || '文件';
  return `${categoryLabel} · ${sizeMb}`;
};

const bindTypeLabel = (value: string) => {
  const map: Record<string, string> = {
    character: '角色参考',
    scene: '场景参考',
    storyboard: '分镜大纲',
    script: '剧本',
    audio: '旁白/音效',
    other: '其他',
  };
  return map[value] || '未绑定';
};

const getRecommendedBindType = (item: { name?: string; filename?: string; category?: string }) => {
  const rawName = (item.filename || item.name || '').toLowerCase();
  const name = rawName.replace(/\s+/g, '');
  if (item.category === 'audio') return 'audio';
  if (item.category === 'video') return 'storyboard';
  if (item.category === 'document') {
    if (name.includes('分镜') || name.includes('storyboard')) return 'storyboard';
    if (name.includes('剧本') || name.includes('script')) return 'script';
    if (name.includes('场景') || name.includes('scene')) return 'scene';
    return 'script';
  }
  if (item.category === 'image') {
    if (name.includes('场景') || name.includes('背景') || name.includes('scene') || name.includes('bg')) return 'scene';
    if (name.includes('角色') || name.includes('人物') || name.includes('人设') || name.includes('character')) {
      return 'character';
    }
    return 'character';
  }
  return 'other';
};

const applyRecommendedBinding = async (item: any) => {
  const recommended = getRecommendedBindType(item);
  item.bindType = recommended;
  await syncAttachment(item);
};

const applyRecommendedBindings = async () => {
  const pending = attachments.value.filter(item => item.status === 'ready' && item.id);
  for (const item of pending) {
    if (!item.bindType) {
      item.bindType = getRecommendedBindType(item);
    }
  }
  await Promise.all(pending.map(item => syncAttachment(item)));
};

const bindAllImagesAsCharacter = async () => {
  const pending = attachments.value.filter(item => item.status === 'ready' && item.category === 'image' && item.id);
  for (const item of pending) {
    item.bindType = 'character';
  }
  await Promise.all(pending.map(item => syncAttachment(item)));
};

const applyBatchLabel = async () => {
  const label = batchLabel.value.trim();
  if (!label) return;
  const pending = attachments.value.filter(item => item.status === 'ready' && item.id);
  for (const item of pending) {
    item.label = label;
  }
  await Promise.all(pending.map(item => syncAttachment(item)));
  batchLabel.value = '';
};

const extractSubjectName = (filename: string) => {
  const base = filename.replace(/\.[^/.]+$/, '');
  return base.replace(/[_\-]/g, ' ').replace(/\d+/g, '').trim();
};

const suggestedSubjects = computed(() => {
  const names = new Set<string>();
  attachments.value.forEach(item => {
    const bindType = item.bindType || getRecommendedBindType(item);
    if (bindType !== 'character') return;
    const filename = item.filename || item.name || '';
    const name = extractSubjectName(filename);
    if (name) names.add(name);
  });
  const existing = new Set(subjectItems.value.map(item => item.name.trim()).filter(Boolean));
  return Array.from(names).filter(name => !existing.has(name));
});

const hasUnboundAttachments = computed(() => {
  return attachments.value.some(item => item.status === 'ready' && item.id && !item.bindType);
});

const addSuggestedSubject = (name: string) => {
  const trimmed = name.trim();
  if (!trimmed) return;
  subjectItems.value.push({ name: trimmed, description: '' });
};

const addAllSuggestedSubjects = () => {
  suggestedSubjects.value.forEach(name => addSuggestedSubject(name));
};

const addSubjectItem = () => {
  const name = subjectNameInput.value.trim();
  if (!name) return;
  subjectItems.value.push({ name, description: subjectDescInput.value.trim() });
  subjectNameInput.value = '';
  subjectDescInput.value = '';
};

const removeSubjectItem = (index: number) => {
  subjectItems.value.splice(index, 1);
};

const ensureProject = async () => {
  if (draftProjectId.value) return draftProjectId.value;
  const projectName = prompt.value.trim().slice(0, 20) || '未命名创作';
  const project = await createProject({ name: projectName });
  draftProjectId.value = project.id;
  return project.id;
};

const triggerFileSelect = () => {
  fileInputRef.value?.click();
};

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files ? Array.from(target.files) : [];
  if (!files.length) return;
  await uploadFiles(files);
  target.value = '';
};

const handleDrop = async (event: DragEvent) => {
  const files = event.dataTransfer ? Array.from(event.dataTransfer.files) : [];
  if (!files.length) return;
  await uploadFiles(files);
};

const uploadFiles = async (files: File[]) => {
  let projectId = draftProjectId.value;
  try {
    if (!projectId) {
      projectId = await ensureProject();
    }
  } catch (err) {
    showToast(err instanceof Error ? err.message : '创建项目失败', 'error');
    return;
  }
  await Promise.all(
    files.map(async file => {
      const localId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const item = {
        localId,
        id: '',
        filename: file.name,
        name: file.name,
        size: file.size,
        content_type: file.type,
        category: file.type.split('/')[0] || 'document',
        url: '',
        label: '',
        bindType: '',
        tags: [],
        parsed_text: '',
        parse_status: '',
        parseStatusLabel: '上传中…',
        progress: 0,
        status: 'uploading' as const,
      };
      attachments.value.push(item);
      try {
        const uploaded = await uploadAttachment(
          projectId as string,
          file,
          item.label,
          item.bindType,
          item.tags,
          percent => {
            item.progress = percent;
          }
        );
        item.id = uploaded.id;
        item.filename = uploaded.filename;
        item.size = uploaded.size;
        item.content_type = uploaded.content_type;
        item.category = uploaded.category;
        item.url = uploaded.url;
        item.label = uploaded.label || item.label || '';
        item.bindType = uploaded.bind_type || item.bindType || '';
        item.tags = uploaded.tags || [];
        item.parsed_text = uploaded.parsed_text || '';
        item.parse_status = uploaded.parse_status || '';
        item.status = 'ready';
        item.parseStatusLabel =
          uploaded.parse_status === 'ok'
            ? '已解析'
            : uploaded.parse_status === 'unsupported'
            ? '解析失败'
            : '未解析';
      } catch (err) {
        item.status = 'failed';
        item.error = err instanceof Error ? err.message : '上传失败';
        item.parseStatusLabel = '上传失败';
      }
    })
  );
};

const syncAttachment = async (item: any) => {
  if (!draftProjectId.value || !item.id) return;
  try {
    const updated = await updateAttachment(draftProjectId.value, item.id, {
      label: item.label || '',
      bind_type: item.bindType || '',
      tags: item.tags || [],
    });
    item.label = updated.label || item.label || '';
    item.bindType = updated.bind_type || item.bindType || '';
    item.tags = updated.tags || [];
  } catch (err) {
    item.error = err instanceof Error ? err.message : '标注保存失败';
  }
};

const pickStyle = (style: { id: string; name: string; preview: string }) => {
  selectedStyle.value = style;
  showStyleSelector.value = false;
};

const pickDefaultModel = (items: ModelOption[]) => {
  const storedImage = sessionStorage.getItem('selectedImageModelId') || '';
  if (items.length === 0) return;
  const defaults = items.find(item => item.is_default && item.enabled) || items.find(item => item.enabled);
  if (!defaults) return;
  const next = items.find(item => item.id === storedImage && item.enabled)?.id || defaults.id;
  selectedModels.value.image = next;
  selectedModels.value.imageRef = selectedModels.value.imageRef || next;
  sessionStorage.setItem('selectedImageModelId', next);
};

const selectImageModel = (modelId: string) => {
  if (!modelId) return;
  selectedModels.value.image = modelId;
  if (!selectedModels.value.imageRef) {
    selectedModels.value.imageRef = modelId;
  }
  sessionStorage.setItem('selectedImageModelId', modelId);
};

const selectImageRefModel = (modelId: string) => {
  if (!modelId) return;
  selectedModels.value.imageRef = modelId;
};

const handleSubmit = async () => {
  const trimmed = prompt.value.trim();
  if (!trimmed) {
    showToast('请输入创作描述', 'warning');
    return;
  }
  if (trimmed.length < minPromptLength) {
    showToast(`至少输入 ${minPromptLength} 字`, 'warning');
    return;
  }
  if (trimmed.length > maxPromptLength) {
    showToast('输入内容已超过最大字数限制', 'warning');
    return;
  }

  generating.value = true;

  try {
    const projectId = draftProjectId.value || (await ensureProject());
    const projectName = trimmed.slice(0, 20) || '未命名创作';
    const missingBindings =
      mode.value === 'pro' &&
      attachments.value.some(item => item.status === 'ready' && item.id && !item.bindType);
    if (missingBindings) {
      showToast('有附件未绑定用途，未绑定的文件不会参与生成', 'warning');
    }
    const inputConfig = mode.value === 'pro' ? buildInputConfig() : undefined;
    await updateProject(projectId, {
      name: projectName,
      description: trimmed,
      ...(inputConfig ? { input_config: inputConfig } : {}),
    });

    sessionStorage.setItem('currentProjectId', projectId);
    sessionStorage.setItem('currentProjectName', projectName);
    sessionStorage.setItem('currentPrompt', trimmed);
    sessionStorage.setItem('currentMode', mode.value);
    sessionStorage.removeItem('streamProjectId');
    sessionStorage.removeItem('streamType');
    sessionStorage.removeItem('streamPrompt');
    sessionStorage.removeItem('streamStartedAt');

    const documents = mode.value === 'pro' ? buildDocumentsPayload() : undefined;
    const createResult = await createMaterialPackage({
      project_id: projectId,
      prompt: trimmed,
      mode: mode.value,
      documents,
      input_config: inputConfig,
      image_model_id: selectedModels.value.image || undefined,
    });
    sessionStorage.setItem('streamPackageId', createResult.package_id);
    sessionStorage.setItem('streamPackagePrompt', trimmed);
    sessionStorage.setItem('streamPackageStartedAt', String(Date.now()));
    generating.value = false;
    router.push('/materials');
  } catch (err) {
    generating.value = false;
    showToast(err instanceof Error ? err.message : '生成失败', 'error');
  }
};

const applyInspiration = (card: InspirationCard) => {
  prompt.value = card.prompt;
  isExpanded.value = true;
  isMinimal.value = false;
  if (textareaRef.value) {
    textareaRef.value.focus();
  }
};

const getTodoIcon = (status: TodoItem['status']) => {
  switch (status) {
    case 'done': return '✓';
    case 'loading': return '⏳';
    default: return '○';
  }
};

// Scroll handler for sticky effect (rAF throttled)
let isTicking = false;
const updateShrinkState = () => {
  const next = window.scrollY > 200;
  if (next !== isShrunk.value) {
    isShrunk.value = next;
  }
  isTicking = false;
};

const handleScroll = () => {
  if (isTicking) return;
  isTicking = true;
  window.requestAnimationFrame(updateShrinkState);
};

onMounted(() => {
  updateShrinkState();
  window.addEventListener('scroll', handleScroll, { passive: true });
  fetchModels('image')
    .then(items => {
      imageModels.value = items;
      pickDefaultModel(items);
    })
    .catch(() => {
      imageModels.value = [];
    });
});

let inputConfigTimer: number | null = null;
const scheduleInputConfigSave = () => {
  if (mode.value !== 'pro' || !draftProjectId.value) return;
  if (inputConfigTimer) {
    window.clearTimeout(inputConfigTimer);
  }
  inputConfigTimer = window.setTimeout(async () => {
    inputConfigTimer = null;
    try {
      await updateProject(draftProjectId.value as string, {
        input_config: buildInputConfig(),
      });
    } catch (err) {
      // Ignore autosave errors to avoid blocking input.
    }
  }, 500);
};

watch(
  () => [
    mode.value,
    aspectRatio.value,
    durationPreset.value,
    durationCustom.value.h,
    durationCustom.value.m,
    durationCustom.value.s,
    customStyle.value,
    selectedStyle.value?.name,
    selectedModels.value.image,
    selectedModels.value.imageRef,
    ...subjectItems.value.map(item => `${item.name}:${item.description}`),
  ],
  () => {
    scheduleInputConfigSave();
  }
);

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  if (inputConfigTimer) {
    window.clearTimeout(inputConfigTimer);
  }
});
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  padding: 0;
  overflow-x: hidden;
  position: relative;
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.cyber-grid::before,
.cyber-grid::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.cyber-grid::before {
  background-image: linear-gradient(rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px);
  background-size: 100px 100px;
  opacity: 0.35;
}

.cyber-grid::after {
  background: radial-gradient(circle at 20% 20%, rgba(var(--md-accent-rgb), 0.12), transparent 40%),
    radial-gradient(circle at 80% 10%, rgba(var(--md-accent-2-rgb), 0.1), transparent 36%),
    radial-gradient(circle at 60% 70%, rgba(var(--md-accent-rgb), 0.08), transparent 38%);
}

.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 24px 80px;
}

.hero-content {
  text-align: center;
  max-width: 640px;
  margin-bottom: 48px;
  transition: all 0.7s cubic-bezier(0.33, 1, 0.68, 1);
}

.hero-sticky-shrunk {
  transform: translateY(-40px);
  opacity: 0.2;
  scale: 0.98;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 9999px;
  border: 1px solid rgba(var(--md-accent-rgb), 0.45);
  background: rgba(var(--md-accent-rgb), 0.18);
  color: var(--md-primary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 11px;
  margin-bottom: 24px;
}

.hero-title {
  font-size: clamp(32px, 5vw, 48px);
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--md-on-surface);
  margin-bottom: 20px;
}

.glow-text {
  color: var(--md-primary);
  text-shadow: 0 0 26px rgba(var(--md-accent-rgb), 0.3);
}

.hero-sub {
  color: var(--md-on-surface-variant);
  max-width: 520px;
  margin: 0 auto;
  font-size: 16px;
  line-height: 1.6;
}

/* Entry Shell */
.entry-shell {
  width: 100%;
  max-width: 640px;
  border: 1px solid var(--md-stroke);
  border-radius: 18px;
  padding: 16px;
  background: var(--md-surface-card);
  box-shadow: var(--md-card-shadow);
  transition: all 0.4s cubic-bezier(0.33, 1, 0.68, 1);
}

.entry-shell.minimal {
  background: rgba(11, 15, 22, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.25);
  padding: 10px 14px;
}

.entry-shell.expanded {
  border-color: rgba(var(--md-accent-rgb), 0.45);
  box-shadow: 0 30px 68px rgba(2, 6, 23, 0.55);
  background: var(--md-surface-card);
}

.entry-shell.minimal .mode-toggle,
.entry-shell.minimal .entry-extra {
  display: none;
}

.entry-shell.minimal .entry-line {
  border-bottom: none;
  padding-bottom: 0;
}

.entry-shell.minimal textarea {
  border: none;
  padding: 6px 0;
  background: transparent;
  min-height: 42px;
  line-height: 1.5;
  resize: none;
}

.entry-shell.minimal .input-actions {
  display: none;
}

.entry-shell.expanded textarea {
  min-height: 140px;
  background: var(--md-field-bg);
  border-radius: 12px;
  border: 1px solid var(--md-stroke);
  padding: 12px;
  color: var(--md-on-surface);
}

.entry-shell.expanded textarea::placeholder {
  color: var(--md-on-surface-variant);
}

.entry-line {
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  padding-bottom: 10px;
  display: flex;
  align-items: stretch;
  gap: 10px;
}

.entry-line textarea {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--md-on-surface);
  font-size: 16px;
  font-family: inherit;
  resize: none;
}

.entry-line textarea::placeholder {
  color: var(--md-on-surface-variant);
}

.entry-submit {
  min-width: 96px;
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(var(--md-accent-rgb), 0.5);
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.85));
  color: #031019;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.entry-submit:hover {
  transform: translateY(-1px);
}

.entry-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.entry-extra {
  display: none;
  margin-top: 12px;
}

.entry-shell.expanded .entry-extra {
  display: block;
}

.helper-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 10px;
}

.count-ok { color: var(--md-primary); }
.count-warn { color: #b54708; }
.count-error { color: #b42318; }

.input-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.input-actions button {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--md-stroke);
  background: rgba(15, 23, 42, 0.75);
  color: var(--md-on-surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.input-actions button:hover {
  border-color: rgba(var(--md-accent-rgb), 0.35);
  transform: translateY(-1px);
}

.action-label {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-left: auto;
}

.pro-config {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.config-block {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(10, 16, 28, 0.75);
}

.config-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.config-hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}

.upload-box {
  border: 1px dashed rgba(148, 163, 184, 0.45);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.6);
}

.upload-text {
  font-size: 13px;
  margin-bottom: 6px;
}

.upload-hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.upload-actions {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.upload-batch {
  display: flex;
  align-items: center;
  gap: 6px;
}

.upload-reminder {
  margin-top: 8px;
  font-size: 12px;
  color: #b42318;
}

.file-input {
  display: none;
}

.upload-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-item {
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  padding: 10px;
  background: rgba(10, 16, 28, 0.85);
}

.upload-info {
  margin-bottom: 8px;
}

.upload-name {
  font-size: 13px;
  font-weight: 600;
}

.upload-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.upload-error {
  font-size: 12px;
  color: #b42318;
}

.upload-controls {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.upload-recommend {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}

.recommend-warn {
  margin-left: 6px;
  color: #b42318;
}

.config-input {
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  padding: 0 10px;
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  font-size: 12px;
}

.config-input.small {
  width: 72px;
  padding: 0 6px;
}

.config-input.compact {
  width: 180px;
  height: 30px;
  font-size: 11px;
}

.config-select {
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  padding: 0 8px;
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  font-size: 12px;
}

.upload-progress {
  height: 6px;
  background: rgba(148, 163, 184, 0.15);
  border-radius: 999px;
  overflow: hidden;
}

.upload-progress-bar {
  height: 100%;
  background: var(--md-primary);
  transition: width 0.2s ease;
}

.upload-status {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.status-pill {
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.status-pill.ok {
  color: #6ee7b7;
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.35);
}

.status-pill.danger {
  color: #fecaca;
  background: rgba(248, 113, 113, 0.16);
  border-color: rgba(248, 113, 113, 0.35);
}

.status-divider {
  color: rgba(148, 163, 184, 0.6);
}

.config-advanced-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}

.advanced-hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.config-advanced {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.model-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.model-column-title {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}

.model-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-chip {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
  font-size: 12px;
  cursor: pointer;
}

.model-chip.active {
  border-color: var(--md-primary);
  color: var(--md-primary);
}

.model-chip.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-empty {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.subject-input-grid {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(160px, 1.4fr) auto;
  gap: 8px;
  align-items: center;
}

.subject-suggest {
  margin-top: 10px;
}

.suggest-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 6px;
}

.subject-suggest-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.subject-suggest-chip {
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.subject-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.subject-item {
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  padding: 8px;
  background: rgba(10, 16, 28, 0.85);
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
}

.subject-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.subject-main {
  font-size: 13px;
  font-weight: 600;
}

.subject-desc {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.chip-remove {
  border: none;
  background: transparent;
  color: var(--md-primary);
  cursor: pointer;
  font-size: 12px;
}

.style-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.duration-custom {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.config-preview {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  text-align: right;
}

.style-selector-popover {
  position: absolute;
  top: 120px;
  right: 24px;
  width: min(520px, 90vw);
  background: var(--md-surface);
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  z-index: 20;
}

.style-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.style-selector-title {
  font-size: 14px;
  font-weight: 600;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.style-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  background: var(--md-surface-container-low);
  cursor: pointer;
}

.style-card.active {
  border-color: var(--md-primary);
  color: var(--md-primary);
}

.style-swatch {
  width: 26px;
  height: 26px;
  border-radius: 8px;
}

/* Mode Toggle */
.mode-toggle {
  width: 96px;
  height: 34px;
  border-radius: 9999px;
  border: 1px solid var(--md-stroke);
  background: rgba(10, 16, 28, 0.85);
  position: relative;
  display: flex;
  align-items: center;
  padding: 4px;
  gap: 6px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 12px;
  flex-shrink: 0;
}

.mode-pill {
  position: absolute;
  top: 4px;
  bottom: 4px;
  width: calc(50% - 6px);
  border-radius: 9999px;
  background: rgba(var(--md-accent-rgb), 0.28);
  transition: transform 0.25s ease;
}

.mode-toggle.general .mode-pill {
  transform: translateX(0);
}

.mode-toggle.pro .mode-pill {
  transform: translateX(100%);
}

.mode-toggle button {
  flex: 1;
  background: none;
  border: none;
  color: inherit;
  position: relative;
  z-index: 2;
  cursor: pointer;
  padding: 0;
  white-space: nowrap;
}

.btn-ghost {
  background: rgba(10, 16, 28, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: var(--md-on-surface);
}

.btn-ghost.small {
  font-size: 11px;
  padding: 4px 8px;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.85));
  border: none;
  color: #031019;
  font-weight: 600;
}

/* Glass Panel */
.glass-panel {
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  box-shadow: var(--md-card-shadow);
}

/* Neon Border */
.neon-border {
  position: relative;
  overflow: hidden;
}

.neon-border::after {
  content: "";
  position: absolute;
  inset: -120%;
  background: conic-gradient(from 120deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.8), rgba(var(--md-accent-rgb), 0.6), rgba(var(--md-accent-rgb), 0.9));
  animation: rotate 12s linear infinite;
  opacity: 0.25;
  transform-origin: center;
}

.neon-border::before {
  content: "";
  position: absolute;
  inset: 1px;
  background: var(--md-surface-container);
  border-radius: 18px;
  z-index: 1;
}

.neon-border > * {
  position: relative;
  z-index: 2;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}

/* Inspiration Section */
.inspiration-section {
  padding: 60px 24px;
  max-width: 1200px;
  margin: 0 auto;
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.inspiration-section.is-shrunk {
  opacity: 0.2;
  transform: translateY(12px);
  pointer-events: none;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 32px;
  text-align: center;
}

.inspiration-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.demo-card {
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: transform 0.25s ease, border-color 0.25s ease;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: var(--md-surface-container);
}

.demo-card:hover {
  transform: translateY(-4px);
  border-color: rgba(var(--md-accent-rgb), 0.35);
  background: rgba(var(--md-accent-rgb), 0.1);
}

.card-image {
  font-size: 48px;
  margin-bottom: 16px;
}

.card-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 8px;
}

.card-content p {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  line-height: 1.5;
}

/* Generating Overlay */
.generating-overlay {
  position: fixed;
  inset: 0;
  background: rgba(28, 27, 31, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--layer-overlay);
  backdrop-filter: blur(8px);
}

.generating-box {
  padding: 32px;
  border-radius: 20px;
  max-width: 400px;
  width: 90%;
}

.generating-box h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 24px;
  text-align: center;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: var(--md-on-surface);
}

.todo-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--md-surface-container-low);
}

.todo-item--loading .todo-icon {
  background: rgba(181, 71, 8, 0.15);
  color: #b54708;
}

.todo-item--done .todo-icon {
  background: rgba(var(--md-accent-rgb), 0.15);
  color: var(--md-primary);
}
</style>
