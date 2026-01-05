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
const currentObject = ref<CurrentObject>({
  type: '',
  path: '请选择中间的对象进行修改',
  kind: '',
  content: '',
});

// Demo data - would come from API
const demoPackage1: AssetPackage = {
  id: 'pkg-1',
  title: '京韵田园绘梦（v1）',
  status: 'done',
  createdAt: Date.now() - 2000,
  summary: '本短片采用微缩模型景观与童话绘本融合的田园风格，描绘理想化的"北京田园生活"：红砖木屋与青瓦屋顶（带青苔）、石径串联绿植与菜地，微距柔光、低饱和。',
  style: '整体视觉设定以微缩模型景观、童话绘本风格、田园风光为核心方向，结合微距视角与手绘质感奠定基础画风。',
  roles: [
    {
      name: '妞妞',
      visuals: [
        { tag: '原图', text: '放松前的状态', img: '', prompt: 'Q版小男孩，圆脸大眼睛，田园劳作姿态', selected: true },
      ],
      voices: [
        { tag: '当前', text: '温和少年音色', audio: '', selected: true },
      ],
    },
    {
      name: '文文',
      visuals: [
        { tag: '原图', text: '乖巧版', img: '', prompt: 'Q版小女孩，圆脸大眼睛，田园场景中', selected: true },
      ],
      voices: [
        { tag: '当前', text: '温柔少女音色', audio: '', selected: true },
      ],
    },
  ],
  scenes: [
    {
      name: '北京微缩田园',
      candidates: [
        { tag: '原图', text: '整体田园氛围', img: '', prompt: '微缩模型田园景观，童话绘本风格', selected: true },
      ],
    },
  ],
  storyboard: [
    {
      name: '分镜 1 · 田园初现',
      candidates: [
        { tag: '文本', text: '【画面】阳光柔和地洒落在一片微缩田园上。\n【构图】全景，平视。\n【运镜】镜头从左向右缓慢平移。\n【旁白】在这方寸之间，藏着一份北京的田园诗意。', selected: true },
      ],
    },
  ],
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

const sendChat = () => {
  const text = chatInput.value.trim();
  if (!text) return;

  const newConvId = `conv-${Date.now()}`;
  const newPkgId = `pkg-${Date.now()}`;

  conversations.value.push({
    id: newConvId,
    displayIndex: conversations.value.length + 1,
    userPrompt: text,
    sysText: '已收到你的需求，正在生成新的素材包...',
    status: 'loading',
    assetPackageId: newPkgId,
  });

  // Add new package
  assetPackages.value[newPkgId] = {
    id: newPkgId,
    title: `新素材包 ${conversations.value.length}`,
    status: 'loading',
    createdAt: Date.now(),
    summary: '生成中…',
    style: '生成中…',
    roles: [],
    scenes: [],
    storyboard: [],
  };

  currentPackageId.value = newPkgId;
  chatInput.value = '';

  // Simulate completion
  setTimeout(() => {
    const conv = conversations.value.find(c => c.id === newConvId);
    if (conv) {
      conv.status = 'done';
      conv.sysText = '素材包生成完成！你可以在中间区域查看结果。';
    }
    const pkg = assetPackages.value[newPkgId];
    if (pkg) {
      pkg.status = 'done';
      pkg.summary = demoPackage1.summary;
      pkg.style = demoPackage1.style;
      pkg.roles = JSON.parse(JSON.stringify(demoPackage1.roles));
      pkg.scenes = JSON.parse(JSON.stringify(demoPackage1.scenes));
      pkg.storyboard = JSON.parse(JSON.stringify(demoPackage1.storyboard));
    }
  }, 3000);
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
  // TODO: Call API to save package
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

onMounted(() => {
  // Initialize with demo data
  assetPackages.value['pkg-1'] = demoPackage1;
  currentPackageId.value = 'pkg-1';

  conversations.value.push({
    id: 'conv-1',
    displayIndex: 1,
    userPrompt: sessionStorage.getItem('currentPrompt') || '北京的田园生活，微缩模型+童话绘本风格',
    sysText: '已生成素材包「京韵田园绘梦（v1）」：完成整体风格、角色妞妞/文文、田园场景与基础分镜。',
    status: 'done',
    assetPackageId: 'pkg-1',
  });
});
</script>

<style scoped>
.materials-page {
  min-height: calc(100vh - 56px);
  background: #05070f;
  color: #dfe8ff;
}

.layout {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  height: calc(100vh - 140px);
}

.col-left {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
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
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px;
  height: 100%;
  overflow-y: auto;
}

.col-right {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
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
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
  transition: background 0.2s;
}

.resize-handle:hover::after {
  background: rgba(108, 249, 224, 0.6);
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
  background: linear-gradient(135deg, rgba(108, 249, 224, 0.16), rgba(124, 93, 255, 0.18));
  color: #e8f7ff;
}

.bubble.user .bubble-meta {
  text-align: right;
  font-size: 11px;
  color: #c7d2fe;
}

.bubble.system {
  margin-right: auto;
  background: linear-gradient(180deg, #1f1f23, #161618);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #dfe8ff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

.assistant-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #c7d2fe;
  margin-bottom: 6px;
}

.assistant-foot {
  font-size: 11px;
  color: #9aa8c7;
  margin-top: 6px;
}

.pkg-chip {
  display: inline-flex;
  align-items: center;
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(108, 249, 224, 0.3);
  background: rgba(108, 249, 224, 0.12);
  color: #9cfbe6;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pkg-chip:hover {
  background: rgba(108, 249, 224, 0.2);
}

.pkg-chip.active {
  border-color: rgba(108, 249, 224, 0.6);
  background: rgba(108, 249, 224, 0.25);
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
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: #e5e7eb;
  padding: 8px;
  resize: vertical;
}

.chat-input button {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(108, 249, 224, 0.4);
  background: linear-gradient(135deg, rgba(108, 249, 224, 0.18), rgba(124, 93, 255, 0.18));
  color: #e5e7eb;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e5e7eb;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 13px;
}

.save-btn {
  background: rgba(108, 249, 224, 0.16);
  border: 1px solid rgba(108, 249, 224, 0.35);
  color: #dffdf5;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.section:last-child {
  border-bottom: none;
}

.section h3 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #e5ecff;
}

.asset-preview {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  text-align: left;
  color: #9bb0e0;
  font-size: 13px;
  line-height: 1.6;
  cursor: pointer;
}

.asset-preview:hover {
  border-color: rgba(108, 249, 224, 0.3);
}

.mb-1 { margin-bottom: 4px; }
.mb-3 { margin-bottom: 12px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-slate-100 { color: #e5ecff; }
.text-slate-300 { color: #c7d2fe; }
.text-slate-400 { color: #9aa8c7; }
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
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: all 0.2s ease;
}

.version-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
}

.version-card.active {
  border-color: rgba(108, 249, 224, 0.5);
  background: rgba(108, 249, 224, 0.08);
}

.version-title {
  font-size: 14px;
  color: #e5e7eb;
}

.version-meta {
  font-size: 12px;
  color: #9aa8c7;
  margin-top: 4px;
}

/* Right Panel */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.box {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
}

.object-header {
  font-size: 13px;
  color: #cbd5f5;
  margin-bottom: 6px;
}

.current-object {
  font-size: 13px;
}

.right-panel textarea {
  width: 100%;
  min-height: 100px;
  background: #0b111d;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e5e7eb;
  border-radius: 8px;
  padding: 8px;
  resize: vertical;
}

.main-action {
  background: rgba(108, 249, 224, 0.16);
  border: 1px solid rgba(108, 249, 224, 0.35);
  color: #dffdf5;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
}

.link-btn {
  border: 1px solid rgba(108, 249, 224, 0.35);
  background: rgba(108, 249, 224, 0.12);
  color: #dffdf5;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
}

.asset-media {
  margin-top: 8px;
}
</style>
