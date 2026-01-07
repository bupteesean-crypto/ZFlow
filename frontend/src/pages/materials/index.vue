<template>
  <div class="materials-page">
    <!-- Three Column Layout -->
    <div class="layout">
      <!-- Left: Chat & Conversations -->
      <div class="col-left" :style="{ width: leftWidth + 'px' }">
        <div class="dialog-list" ref="dialogListRef">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="dialog-item"
          >
            <div class="bubble user">
              <div class="bubble-meta">我 · 对话 #{{ conv.displayIndex }}</div>
              <div class="text-sm mt-1">{{ conv.userPrompt }}</div>
            </div>
            <div class="bubble system">
              <div class="assistant-title">
                <span>{{ conv.status === 'done' ? '✅' : '⏳' }}</span>
                <span>Z.Video 助手</span>
              </div>
              <div class="text-sm leading-relaxed">{{ conv.sysText }}</div>
              <div class="assistant-foot">你可以继续提出修改想法，我会在新一轮更新对应素材。</div>
              <button
                class="pkg-chip"
                :class="{ active: currentPackageId === conv.assetPackageId }"
                @click="selectPackage(conv.assetPackageId)"
              >
                查看 {{ getPackageTitle(conv.assetPackageId) }}
              </button>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <textarea
            v-model="chatInput"
            placeholder="请输入需求，例如：生成一段霓虹夜景动作短片"
            @keydown="handleChatKeydown"
          />
          <button @click="sendChat">发送</button>
        </div>
      </div>

      <div class="resize-handle" @mousedown="startResizeLeft"></div>

      <!-- Center: Workspace -->
      <div class="col-center">
        <div class="center-topbar">
          <label for="pkgSelector" class="text-xs text-slate-400">素材包切换：</label>
          <select id="pkgSelector" v-model="currentPackageId" class="pkg-select" @change="renderWorkspace">
            <option v-for="pkg in sortedPackages" :key="pkg.id" :value="pkg.id">
              {{ pkg.title }} · {{ pkg.status === 'done' ? '已完成' : '生成中' }}
            </option>
          </select>
          <button class="save-btn" @click="savePackage">存档当前素材包</button>
        </div>
        <div class="workspace" v-if="currentPackage">
          <!-- Version List -->
          <div v-if="sortedPackages.length > 1" class="version-list">
            <div
              v-for="pkg in sortedPackages"
              :key="pkg.id"
              :class="['version-card', { active: pkg.id === currentPackageId }]"
              @click="selectPackage(pkg.id)"
            >
              <div class="version-title">{{ pkg.title }}</div>
              <div class="version-meta">
                <StatusBadge :status="pkg.status" />
              </div>
              <div class="version-meta">{{ formatTime(pkg.createdAt) }}</div>
            </div>
          </div>

          <!-- Summary Section -->
          <section class="section" @click="selectObject('summary', '故事梗概', currentPackage.summary)">
            <h3>故事梗概</h3>
            <div class="asset-preview">{{ currentPackage.summary || '生成中…' }}</div>
          </section>

          <!-- Style Section -->
          <section class="section" @click="selectObject('style', '美术风格', currentPackage.style)">
            <h3>美术风格</h3>
            <div class="asset-preview">{{ currentPackage.style || '生成中…' }}</div>
          </section>

          <!-- Roles Section -->
          <section class="section">
            <h3>角色列表</h3>
            <div v-for="role in currentPackage.roles" :key="role.name" class="mb-3">
              <div class="font-semibold mb-1 text-slate-100">{{ role.name }}</div>
              <div class="text-xs text-slate-400 mb-1">形象</div>
              <CandidateRow
                :items="role.visuals"
                type="image"
                @select="(item) => selectObject('role', `角色 · ${role.name} · 形象`, item.prompt, role.visuals)"
              />
              <div class="text-xs text-slate-400 mb-1 mt-2">音色</div>
              <CandidateRow
                :items="role.voices"
                type="audio"
                @select="(item) => selectObject('role', `角色 · ${role.name} · 音色`, item.text, role.voices, 'audio')"
              />
            </div>
          </section>

          <!-- Scenes Section -->
          <section class="section">
            <h3>场景列表</h3>
            <div v-for="scene in currentPackage.scenes" :key="scene.name" class="mb-3">
              <div class="font-semibold mb-1 text-slate-100">{{ scene.name }}</div>
              <CandidateRow
                :items="scene.candidates"
                type="image"
                @select="(item) => selectObject('scene', `场景 · ${scene.name}`, item.prompt, scene.candidates)"
              />
            </div>
          </section>

          <!-- Storyboard Section -->
          <section class="section">
            <h3>分镜剧本</h3>
            <div v-for="shot in currentPackage.storyboard" :key="shot.name" class="mb-3">
              <div class="font-semibold mb-1 text-slate-100">{{ shot.name }}</div>
              <CandidateRow
                :items="shot.candidates"
                type="text"
                @select="(item) => selectObject('shot', `分镜 · ${shot.name}`, item.text, shot.candidates, 'text')"
              />
            </div>
          </section>
        </div>
        <div v-else class="text-sm text-slate-400">暂无素材包，请在左侧发起生成。</div>
      </div>

      <div class="resize-handle" @mousedown="startResizeRight"></div>

      <!-- Right: Edit Panel -->
      <div class="col-right" :style="{ width: rightWidth + 'px' }">
        <div class="right-panel">
          <div class="box">
            <div class="object-header">当前对象</div>
            <div class="current-object">
              <div class="text-xs text-slate-400 mb-1">已选对象</div>
              <div class="text-sm text-slate-100 mb-2">{{ currentObject.path || '未选择' }}</div>
              <div class="text-xs text-slate-300 leading-relaxed max-h-32 overflow-auto">
                {{ truncateContent(currentObject.content) }}
              </div>
              <div v-if="currentObject.kind === 'audio'" class="asset-media mt-2">
                <audio controls :src="currentAudioUrl" class="w-full"></audio>
              </div>
              <div class="text-[11px] text-slate-500 mt-2">提示：提交后会生成新的候选版本并存。</div>
            </div>
          </div>
          <div class="box">
            <div class="object-header">修改意见</div>
            <textarea
              v-model="editInput"
              placeholder="请输入你的修改意见，例如：更成熟 / 更写实 / 换成夜景 / 语气更轻松"
            />
          </div>
          <div class="flex flex-col gap-2">
            <button class="main-action" @click="handleRegenerate">生成修改结果</button>
            <button class="link-btn" @click="goToEditor">进入剪辑页面</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import StatusBadge from '@/components/common/StatusBadge.vue';
import CandidateRow from '@/components/common/CandidateRow.vue';
import { fetchProject } from '@/api/projects';
import { fetchMaterialPackages, type MaterialPackage } from '@/api/material-packages';
import { fetchGenerationProgress, startGeneration } from '@/api/generation';

interface VisualCandidate {
  tag: string;
  text: string;
  img?: string;
  prompt: string;
  selected: boolean;
}

interface VoiceCandidate {
  tag: string;
  text: string;
  audio: string;
  selected: boolean;
}

interface Role {
  name: string;
  visuals: VisualCandidate[];
  voices: VoiceCandidate[];
}

interface Scene {
  name: string;
  candidates: VisualCandidate[];
}

interface TextCandidate {
  tag: string;
  text: string;
  selected: boolean;
}

interface StoryboardShot {
  name: string;
  candidates: TextCandidate[];
}

interface AssetPackage {
  id: string;
  title: string;
  status: 'pending' | 'loading' | 'done';
  createdAt: number;
  summary: string;
  style: string;
  roles: Role[];
  scenes: Scene[];
  storyboard: StoryboardShot[];
}

interface Conversation {
  id: string;
  displayIndex: number;
  userPrompt: string;
  sysText: string;
  status: 'loading' | 'done';
  assetPackageId: string;
}

interface CurrentObject {
  type: string;
  path: string;
  content: string;
  kind: string;
  list?: any[];
  mediaType?: string;
}

const router = useRouter();

// State
const leftWidth = ref(340);
const rightWidth = ref(280);
const chatInput = ref('');
const editInput = ref('');
const conversations = ref<Conversation[]>([]);
const assetPackages = ref<Record<string, AssetPackage>>({});
const currentPackageId = ref('');
const currentProjectId = ref<string | null>(null);
const currentObject = ref<CurrentObject>({
  type: '',
  path: '请选择中间的对象进行修改',
  kind: '',
  content: '',
});

const mapPackageStatus = (status: string) => {
  if (status === 'completed') return 'done';
  if (status === 'generating') return 'loading';
  return 'pending';
};

const mapMaterialPackage = (pkg: MaterialPackage): AssetPackage => {
  const materials = pkg.materials || {};
  const storyline = (materials as any).storyline || {};
  const artStyle = (materials as any).art_style || {};
  const characters = (materials as any).characters || [];
  const scenes = (materials as any).scenes || [];
  const storyboards = (materials as any).storyboards || [];

  return {
    id: pkg.id,
    title: pkg.package_name || '素材包',
    status: mapPackageStatus(pkg.status),
    createdAt: pkg.created_at ? Date.parse(pkg.created_at) : Date.now(),
    summary: storyline.summary || pkg.summary || '生成中…',
    style: artStyle.description || '生成中…',
    roles: characters.map((item: any) => ({
      name: item.character_name || item.name || '角色',
      visuals: [],
      voices: [],
    })),
    scenes: scenes.map((item: any) => ({
      name: item.scene_name || item.name || '场景',
      candidates: [],
    })),
    storyboard: storyboards.map((item: any) => ({
      name: `分镜 ${item.shot_number || ''}`.trim(),
      candidates: item.description
        ? [{ tag: '文本', text: item.description, selected: true }]
        : [],
    })),
  };
};

const rebuildConversations = (packages: AssetPackage[]) => {
  const prompt = sessionStorage.getItem('currentPrompt') || '创作输入';
  conversations.value = packages.map((pkg, index) => ({
    id: `conv-${pkg.id}`,
    displayIndex: index + 1,
    userPrompt: prompt,
    sysText:
      pkg.status === 'done'
        ? `素材包「${pkg.title}」已生成完成。`
        : `素材包「${pkg.title}」生成中...`,
    status: pkg.status === 'done' ? 'done' : 'loading',
    assetPackageId: pkg.id,
  }));
};

const sortedPackages = computed(() => {
  return Object.values(assetPackages.value).sort((a, b) => b.createdAt - a.createdAt);
});

const currentPackage = computed(() => {
  return assetPackages.value[currentPackageId.value];
});

const currentAudioUrl = computed(() => {
  if (currentObject.value.kind === 'audio' && currentObject.value.list) {
    const selected = currentObject.value.list.find((i: any) => i.selected);
    return selected?.audio || '';
  }
  return '';
});

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString();
};

const getPackageTitle = (id: string) => {
  return assetPackages.value[id]?.title || '素材包';
};

const selectPackage = (id: string) => {
  currentPackageId.value = id;
  renderWorkspace();
};

const renderWorkspace = () => {
  // Trigger re-render
};

const selectObject = (type: string, path: string, content: string, list?: any[], kind?: string) => {
  currentObject.value = {
    type,
    path,
    content,
    kind: kind || (type === 'summary' || type === 'style' ? 'text' : 'image'),
    list,
  };
  editInput.value = content;
};

const truncateContent = (content: string) => {
  if (!content) return '';
  return content.length > 200 ? content.substring(0, 200) + '...' : content;
};

const sendChat = async () => {
  const text = chatInput.value.trim();
  if (!text) return;
  if (!currentProjectId.value) {
    return;
  }
  chatInput.value = '';

  const task = await startGeneration(currentProjectId.value, text);
  const convId = `conv-${task.id}`;
  conversations.value.push({
    id: convId,
    displayIndex: conversations.value.length + 1,
    userPrompt: text,
    sysText: '已收到你的需求，正在生成新的素材包...',
    status: 'loading',
    assetPackageId: task.material_package_id || '',
  });

  let completed = false;
  while (!completed) {
    const progress = await fetchGenerationProgress(currentProjectId.value);
    const latest = progress.list.find(item => item.id === task.id) || task;
    if (latest.status === 'completed') {
      completed = true;
    } else {
      await new Promise(resolve => setTimeout(resolve, 800));
    }
  }
  await loadPackages();
};

const handleChatKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
};

const handleRegenerate = () => {
  const text = editInput.value.trim();
  if (!text) {
    alert('请输入修改意见');
    return;
  }

  // TODO: Call API to regenerate
  alert('修改功能开发中，请等待API接入');
};

const savePackage = () => {
  alert('存档功能开发中');
};

const goToEditor = () => {
  router.push('/editor');
};

// Resize handlers
const startResizeLeft = (e: MouseEvent) => {
  const startX = e.clientX;
  const startWidth = leftWidth.value;

  const onMove = (e: MouseEvent) => {
    const delta = e.clientX - startX;
    leftWidth.value = Math.min(520, Math.max(240, startWidth + delta));
  };

  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };

  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};

const startResizeRight = (e: MouseEvent) => {
  const startX = e.clientX;
  const startWidth = rightWidth.value;

  const onMove = (e: MouseEvent) => {
    const delta = e.clientX - startX;
    rightWidth.value = Math.min(480, Math.max(220, startWidth - delta));
  };

  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };

  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};

const loadPackages = async () => {
  if (!currentProjectId.value) {
    return;
  }
  const data = await fetchMaterialPackages(currentProjectId.value);
  const mapped = data.list.map(mapMaterialPackage);
  assetPackages.value = {};
  mapped.forEach(pkg => {
    assetPackages.value[pkg.id] = pkg;
  });
  if (mapped.length > 0) {
    const latest = mapped.sort((a, b) => b.createdAt - a.createdAt)[0];
    currentPackageId.value = latest.id;
    rebuildConversations(mapped);
  }
};

onMounted(async () => {
  const storedProjectId = sessionStorage.getItem('currentProjectId');
  if (!storedProjectId) {
    router.push('/space');
    return;
  }
  currentProjectId.value = storedProjectId;

  try {
    const project = await fetchProject(storedProjectId);
    sessionStorage.setItem('currentProjectName', project.name || '未命名创作');
  } catch (err) {
    alert(err instanceof Error ? err.message : '项目加载失败');
  }

  try {
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '素材包加载失败');
  }
});
</script>

<style scoped>
.materials-page {
  min-height: calc(100vh - 56px);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.layout {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  height: calc(100vh - 140px);
}

.col-left {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  overflow: hidden;
}

.col-center {
  flex: 1;
  min-width: 0;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  padding: 14px;
  height: 100%;
  overflow-y: auto;
}

.col-right {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  overflow-y: auto;
}

.resize-handle {
  width: 8px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.resize-handle::after {
  content: '';
  width: 2px;
  height: 50px;
  background: rgba(121, 116, 126, 0.3);
  border-radius: 2px;
  transition: background 0.2s;
}

.resize-handle:hover::after {
  background: rgba(103, 80, 164, 0.6);
}

/* Dialog List */
.dialog-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.dialog-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bubble {
  padding: 10px 12px;
  border-radius: 14px;
  position: relative;
  line-height: 1.6;
  font-size: 13px;
  max-width: 100%;
}

.bubble.user {
  margin-left: auto;
  background: var(--md-secondary-container);
  color: var(--md-on-secondary-container);
}

.bubble.user .bubble-meta {
  text-align: right;
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.bubble.system {
  margin-right: auto;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  color: var(--md-on-surface);
  box-shadow: 0 10px 26px rgba(26, 18, 44, 0.14);
}

.assistant-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 6px;
}

.assistant-foot {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 6px;
}

.pkg-chip {
  display: inline-flex;
  align-items: center;
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(103, 80, 164, 0.3);
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-primary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pkg-chip:hover {
  background: rgba(103, 80, 164, 0.2);
}

.pkg-chip.active {
  border-color: rgba(103, 80, 164, 0.6);
  background: rgba(103, 80, 164, 0.25);
}

/* Chat Input */
.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input textarea {
  flex: 1;
  min-height: 52px;
  max-height: 120px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
  border-radius: 10px;
  color: var(--md-on-surface);
  padding: 8px;
  resize: vertical;
}

.chat-input button {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(103, 80, 164, 0.3);
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-on-surface);
  cursor: pointer;
}

/* Center Topbar */
.center-topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.pkg-select {
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
  color: var(--md-on-surface);
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 13px;
}

.save-btn {
  background: rgba(103, 80, 164, 0.12);
  border: 1px solid rgba(103, 80, 164, 0.3);
  color: var(--md-primary);
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
}

/* Workspace */
.workspace {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.section {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(121, 116, 126, 0.2);
}

.section:last-child {
  border-bottom: none;
}

.section h3 {
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--md-on-surface);
}

.asset-preview {
  padding: 12px;
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  background: var(--md-surface-container-low);
  text-align: left;
  color: var(--md-on-surface-variant);
  font-size: 13px;
  line-height: 1.6;
  cursor: pointer;
}

.asset-preview:hover {
  border-color: rgba(103, 80, 164, 0.3);
}

.mb-1 { margin-bottom: 4px; }
.mb-3 { margin-bottom: 12px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-slate-100 { color: var(--md-on-surface); }
.text-slate-300 { color: var(--md-on-surface-variant); }
.text-slate-400 { color: var(--md-on-surface-variant); }
.font-semibold { font-weight: 600; }
.leading-relaxed { line-height: 1.6; }
.overflow-auto { overflow: auto; }
.max-h-32 { max-height: 8rem; }
.flex { display: flex; }
.gap-2 { gap: 8px; }
.flex-col { flex-direction: column; }

/* Version List */
.version-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.version-card {
  min-width: 180px;
  padding: 10px;
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  background: var(--md-surface-container-low);
  cursor: pointer;
  transition: all 0.2s ease;
}

.version-card:hover {
  border-color: rgba(121, 116, 126, 0.35);
}

.version-card.active {
  border-color: rgba(103, 80, 164, 0.5);
  background: rgba(103, 80, 164, 0.12);
}

.version-title {
  font-size: 14px;
  color: var(--md-on-surface);
}

.version-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-top: 4px;
}

/* Right Panel */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.box {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  padding: 10px;
  background: var(--md-surface-container-low);
}

.object-header {
  font-size: 13px;
  color: var(--md-on-surface-variant);
  margin-bottom: 6px;
}

.current-object {
  font-size: 13px;
}

.right-panel textarea {
  width: 100%;
  min-height: 100px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
  color: var(--md-on-surface);
  border-radius: 8px;
  padding: 8px;
  resize: vertical;
}

.main-action {
  background: var(--md-primary);
  border: 1px solid rgba(103, 80, 164, 0.3);
  color: var(--md-on-primary);
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
}

.link-btn {
  border: 1px solid rgba(103, 80, 164, 0.3);
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-primary);
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
}

.asset-media {
  margin-top: 8px;
}
</style>
