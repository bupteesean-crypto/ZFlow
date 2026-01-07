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
          <button type="button" @click="mode = 'general'">通用模式</button>
          <button type="button" @click="mode = 'pro'">专业模式</button>
        </div>

        <div class="entry-line">
          <textarea
            ref="textareaRef"
            v-model="prompt"
            placeholder="描述你想创作的视频，例如：北京的田园生活，Q版角色在微缩景观中..."
            @focus="handleFocus"
            @blur="handleBlur"
            @input="handleInput"
          />
          <button class="entry-submit" @click="handleSubmit">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>

        <div v-if="isExpanded" class="entry-extra">
          <div class="helper-row">
            <span :class="['count', countClass]">{{ prompt.length }} / 2000</span>
            <span class="mode-hint">按 Enter 换行，Shift + Enter 发送</span>
          </div>

          <div class="input-actions">
            <button v-if="canUseImage" title="上传参考图" @click="handleUploadImage">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
            </button>
            <button title="选择模型" @click="showModelSelector = !showModelSelector">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <span class="action-label">高级选项</span>
          </div>
        </div>
      </div>

      <!-- Model Selector Popover -->
      <div v-if="showModelSelector" class="model-selector-popover">
        <div class="model-selector-tabs">
          <button
            v-for="tab in modelTabs"
            :key="tab.id"
            :class="['model-selector-tab', { active: activeModelTab === tab.id }]"
            @click="activeModelTab = tab.id"
          >
            {{ tab.name }}
          </button>
        </div>
        <div class="model-selector-list">
          <button
            v-for="model in currentModels"
            :key="model.id"
            :class="['model-selector-item', { active: selectedModel === model.id }]"
            @click="selectedModel = model.id"
          >
            <span>{{ model.name }}</span>
            <span class="model-tag">{{ model.tag }}</span>
          </button>
        </div>
        <div class="model-selector-actions">
          <button class="btn-ghost" @click="showModelSelector = false">取消</button>
          <button class="btn-primary" @click="showModelSelector = false">确定</button>
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { createProject } from '@/api/projects';
import { fetchGenerationProgress, startGeneration } from '@/api/generation';

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
const canUseImage = ref(true);
const generating = ref(false);
const showModelSelector = ref(false);
const activeModelTab = ref('video');
const selectedModel = ref('default');

const modelTabs = [
  { id: 'video', name: '视频生成' },
  { id: 'image', name: '图像生成' },
  { id: 'audio', name: '音频生成' },
];

const models = {
  video: [
    { id: 'default', name: '默认模型', tag: '推荐' },
    { id: 'fast', name: '快速生成', tag: '2x速度' },
    { id: 'quality', name: '高质量', tag: 'Pro' },
  ],
  image: [
    { id: 'default', name: '默认模型', tag: '推荐' },
    { id: 'realistic', name: '写实风格', tag: '新增' },
  ],
  audio: [
    { id: 'default', name: '默认音色', tag: '推荐' },
    { id: 'voice1', name: '温柔女声', tag: '' },
  ],
};

const currentModels = computed(() => models[activeModelTab.value as keyof typeof models]);

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
  if (len > 1800) return 'count-error';
  if (len > 1500) return 'count-warn';
  return 'count-ok';
});

const handleFocus = () => {
  isExpanded.value = true;
  isMinimal.value = false;
};

const handleBlur = (e: FocusEvent) => {
  // Keep expanded if clicking inside the entry shell
  const target = e.relatedTarget as HTMLElement;
  if (target?.closest('.entry-shell')) return;
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

const handleSubmit = async () => {
  if (!prompt.value.trim()) {
    showToast('请输入创作描述', 'warning');
    return;
  }

  generating.value = true;
  todoItems.value.forEach(item => {
    item.status = 'pending';
  });

  try {
    const projectName = prompt.value.slice(0, 20);
    const project = await createProject({ name: projectName });
    sessionStorage.setItem('currentProjectId', project.id);
    sessionStorage.setItem('currentProjectName', project.name);
    sessionStorage.setItem('currentPrompt', prompt.value);
    sessionStorage.setItem('currentMode', mode.value);

    const task = await startGeneration(project.id, prompt.value);
    let completed = false;
    const updateTodo = (progress: number) => {
      todoItems.value.forEach(item => {
        item.status = 'pending';
      });
      if (progress >= 0) todoItems.value[0].status = 'loading';
      if (progress >= 30) todoItems.value[0].status = 'done';
      if (progress >= 30) todoItems.value[1].status = 'loading';
      if (progress >= 60) todoItems.value[1].status = 'done';
      if (progress >= 60) todoItems.value[2].status = 'loading';
      if (progress >= 80) todoItems.value[2].status = 'done';
      if (progress >= 80) todoItems.value[3].status = 'loading';
      if (progress >= 100) todoItems.value[3].status = 'done';
      if (progress >= 100) todoItems.value[4].status = 'done';
    };

    while (!completed) {
      const progressData = await fetchGenerationProgress(project.id);
      const latest = progressData.list.find(item => item.id === task.id) || task;
      updateTodo(latest.progress || 0);
      if (latest.status === 'completed') {
        completed = true;
      } else {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
    }

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

const handleUploadImage = () => {
  showToast('图片上传功能开发中...', 'info');
};

const getTodoIcon = (status: TodoItem['status']) => {
  switch (status) {
    case 'done': return '✓';
    case 'loading': return '⏳';
    default: return '○';
  }
};

// Scroll handler for sticky effect
const handleScroll = () => {
  const scrollTop = window.scrollY;
  isShrunk.value = scrollTop > 200;
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
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
  background-image: linear-gradient(rgba(121, 116, 126, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(121, 116, 126, 0.12) 1px, transparent 1px);
  background-size: 80px 80px;
  opacity: 0.7;
}

.cyber-grid::after {
  background: radial-gradient(circle at 20% 20%, rgba(103, 80, 164, 0.12), transparent 40%),
    radial-gradient(circle at 80% 10%, rgba(125, 82, 96, 0.1), transparent 36%),
    radial-gradient(circle at 60% 70%, rgba(103, 80, 164, 0.08), transparent 38%);
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
  border: 1px solid rgba(103, 80, 164, 0.35);
  background: rgba(103, 80, 164, 0.12);
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
  text-shadow: 0 0 26px rgba(103, 80, 164, 0.3);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  border-radius: 16px;
  padding: 16px;
  background: var(--md-surface-container);
  box-shadow: 0 15px 32px rgba(26, 18, 44, 0.16);
  transition: all 0.4s cubic-bezier(0.33, 1, 0.68, 1);
}

.entry-shell.minimal {
  background: transparent;
  border: 1px solid rgba(121, 116, 126, 0.2);
  padding: 10px 14px;
}

.entry-shell.expanded {
  border-color: rgba(103, 80, 164, 0.35);
  box-shadow: 0 25px 60px rgba(26, 18, 44, 0.2);
  background: var(--md-surface-container);
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
  background: var(--md-surface-container-low);
  border-radius: 12px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  padding: 12px;
  color: var(--md-on-surface);
}

.entry-shell.expanded textarea::placeholder {
  color: var(--md-on-surface-variant);
}

.entry-line {
  border-bottom: 1px solid rgba(121, 116, 126, 0.25);
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
  width: 42px;
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(103, 80, 164, 0.45);
  background: var(--md-primary);
  color: var(--md-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.entry-submit:hover {
  transform: translateY(-1px);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.input-actions button:hover {
  border-color: rgba(103, 80, 164, 0.35);
  transform: translateY(-1px);
}

.action-label {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-left: auto;
}

/* Mode Toggle */
.mode-toggle {
  width: 120px;
  height: 34px;
  border-radius: 9999px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  position: relative;
  display: flex;
  align-items: center;
  padding: 4px;
  gap: 6px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 12px;
}

.mode-pill {
  position: absolute;
  top: 4px;
  bottom: 4px;
  width: calc(50% - 6px);
  border-radius: 9999px;
  background: rgba(103, 80, 164, 0.2);
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
}

/* Model Selector */
.model-selector-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  max-width: 420px;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.25);
  border-radius: 18px;
  box-shadow: 0 30px 70px rgba(26, 18, 44, 0.2);
  padding: 14px;
  z-index: 100;
}

.model-selector-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.model-selector-tab {
  flex: 1;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  cursor: pointer;
  font-size: 13px;
}

.model-selector-tab.active {
  background: rgba(103, 80, 164, 0.16);
  color: var(--md-on-surface);
  border-color: rgba(103, 80, 164, 0.35);
}

.model-selector-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  margin-bottom: 8px;
  cursor: pointer;
  color: var(--md-on-surface);
  font-size: 14px;
}

.model-selector-item.active {
  border-color: rgba(103, 80, 164, 0.45);
  background: rgba(103, 80, 164, 0.12);
}

.model-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-primary);
}

.model-selector-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.model-selector-actions button {
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
}

.btn-ghost {
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
  color: var(--md-on-surface);
}

.btn-primary {
  background: var(--md-primary);
  border: none;
  color: var(--md-on-primary);
  font-weight: 600;
}

/* Glass Panel */
.glass-panel {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  box-shadow: 0 25px 60px rgba(26, 18, 44, 0.2);
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
  background: conic-gradient(from 120deg, rgba(103, 80, 164, 0.9), rgba(125, 82, 96, 0.8), rgba(103, 80, 164, 0.6), rgba(103, 80, 164, 0.9));
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container);
}

.demo-card:hover {
  transform: translateY(-4px);
  border-color: rgba(103, 80, 164, 0.35);
  background: rgba(103, 80, 164, 0.1);
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
  z-index: 1000;
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
  background: rgba(103, 80, 164, 0.15);
  color: var(--md-primary);
}
</style>
