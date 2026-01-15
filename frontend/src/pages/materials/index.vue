<template>
  <div class="materials-page">
    <!-- Three Column Layout -->
    <div class="layout">
      <!-- Left: Chat & Conversations -->
      <div class="col-left" :style="{ width: leftWidth + 'px' }">
        <div class="dialog-list" ref="dialogListRef">
          <div
            v-for="message in conversationMessages"
            :key="message.id"
            class="dialog-item"
          >
            <div v-if="message.role === 'user'" class="bubble user">
              <div class="bubble-meta">我</div>
              <div class="text-sm mt-1">{{ message.text }}</div>
            </div>
            <div v-else class="bubble system">
              <div class="assistant-title">
                <span :class="['status-icon', message.status || 'completed']"></span>
                <span>系统进度</span>
              </div>
              <div class="text-sm leading-relaxed">{{ message.text }}</div>
              <div v-if="message.step === 'done'" class="assistant-foot">内容已更新到右侧策划文档。</div>
              <button
                v-if="message.status === 'error'"
                class="link-btn mt-2"
                :disabled="isRetrying"
                @click="retryGeneration"
              >
                重试生成
              </button>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <textarea
            v-model="chatInput"
            placeholder="对当前素材包的修改意见，例如：更温暖的色调 / 场景更细腻"
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
              v{{ pkg.version }} · {{ pkg.title }} · {{ pkg.status === 'done' ? '已完成' : '生成中' }}
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
                <StatusBadge :status="pkg.status" /> · v{{ pkg.version }}
              </div>
              <div class="version-meta">{{ formatTime(pkg.createdAt) }}</div>
            </div>
          </div>

          <!-- Story Summary Section -->
          <section class="section" @click="selectObject('summary', '故事摘要', currentPackage.storySummary)">
            <h3>故事摘要</h3>
            <div class="asset-preview">{{ currentPackage.storySummary || '生成中…' }}</div>
          </section>

          <!-- Art Style Section -->
          <section
            :class="['section', { selected: selectedTextTarget?.type === 'art_style' }]"
            @click="selectTextTarget({ type: 'art_style' }, '美术风格', buildArtStyleContent(currentPackage.artStyle))"
          >
            <h3>美术风格</h3>
            <div class="asset-preview">
              <div class="detail-row">风格：{{ currentPackage.artStyle.styleName || '生成中…' }}</div>
              <div class="detail-row" v-if="currentPackage.artStyle.palette.length">
                调色盘：{{ currentPackage.artStyle.palette.join(' / ') }}
              </div>
              <div class="detail-row" v-if="currentPackage.artStyle.stylePrompt">
                提示词：{{ currentPackage.artStyle.stylePrompt }}
              </div>
            </div>
          </section>

          <!-- Subjects Section -->
          <section class="section">
            <h3>角色列表</h3>
            <div v-if="currentPackage.subjects.length === 0" class="empty-text">暂无角色</div>
            <div
              v-for="subject in currentPackage.subjects"
              :key="subject.id || subject.name"
              :class="['detail-card', { selected: isSubjectSelected(subject) }]"
              @click="selectObject('subject', `角色 · ${subject.name}`, buildSubjectContent(subject), undefined, 'text')"
            >
              <div class="detail-title">{{ subject.name || '角色' }}</div>
              <div class="detail-row">角色定位：{{ subject.role || '未指定' }}</div>
              <div class="detail-row">描述：{{ subject.description || '暂无描述' }}</div>
              <div class="detail-row">视角：{{ subject.viewLabel }}</div>
              <div v-if="subject.images.length" class="thumb-grid">
                <div
                  v-for="(img, idx) in subject.images"
                  :key="`${img.url}-${idx}`"
                  :class="['thumb-card', { selected: img.id && img.id === selectedImageId, loading: isLoadingImage(img) }]"
                  :title="buildPromptTooltip(img)"
                  @click.stop="handleImageClick(img, `角色 · ${subject.name}`)"
                >
                  <img :src="img.url" :alt="img.prompt || 'Character view'" class="thumb-image" />
                  <div v-if="img.isActive" class="thumb-active">✅</div>
                  <div class="thumb-meta">{{ formatImageLabel(img) }}</div>
                </div>
                <div v-if="isLoadingSubject(subject)" class="thumb-card loading-card">
                  <div class="loading-text">生成中...</div>
                </div>
              </div>
              <div v-else class="empty-text">暂无角色三视图图片</div>
            </div>
          </section>

          <!-- Scenes Section -->
          <section class="section">
            <h3>场景列表</h3>
            <div v-if="currentPackage.scenes.length === 0" class="empty-text">暂无场景</div>
            <div v-for="scene in currentPackage.scenes" :key="scene.id || scene.name" class="detail-card">
              <div class="detail-title">{{ scene.name || '场景' }}</div>
              <div class="detail-row">情绪：{{ scene.mood || '未指定' }}</div>
              <div class="detail-row">描述：{{ scene.description || '暂无描述' }}</div>
              <div v-if="scene.images.length" class="thumb-grid">
                <div
                  v-for="(img, idx) in scene.images"
                  :key="`${img.url}-${idx}`"
                  :class="['thumb-card', { selected: img.id && img.id === selectedImageId, loading: isLoadingImage(img) }]"
                  :title="buildPromptTooltip(img)"
                  @click.stop="handleImageClick(img, `场景 · ${scene.name}`)"
                >
                  <img :src="img.url" :alt="img.prompt || 'Scene'" class="thumb-image" />
                  <div v-if="img.isActive" class="thumb-active">✅</div>
                  <div class="thumb-meta">{{ formatImageLabel(img) }}</div>
                </div>
                <div v-if="isLoadingScene(scene)" class="thumb-card loading-card">
                  <div class="loading-text">生成中...</div>
                </div>
              </div>
              <div v-else class="empty-text">暂无场景图片</div>
            </div>
          </section>

          <!-- Storyboard Section -->
          <section class="section">
            <h3>分镜剧本</h3>
            <div v-if="currentPackage.storyboard.length === 0" class="empty-text">暂无分镜</div>
            <ol v-else class="storyboard-list">
              <li
                v-for="shot in currentPackage.storyboard"
                :key="shot.id || shot.shotNumber"
                :class="['storyboard-item', { selected: selectedTextTarget?.type === 'storyboard_description' && selectedTextTarget?.shotId === shot.id }]"
                @click="selectTextTarget({ type: 'storyboard_description', shotId: shot.id }, `分镜 · ${shot.shotNumber}`, shot.description)"
              >
                <div class="storyboard-title">镜头 {{ shot.shotNumber }}</div>
                <div class="storyboard-meta">
                  场景：{{ shot.sceneName || shot.sceneId || '未关联' }} · 时长：{{ shot.durationSec }}s · 镜头：{{ shot.camera || '未指定' }}
                </div>
                <div class="storyboard-desc">{{ shot.description || '暂无描述' }}</div>
              </li>
            </ol>
          </section>

          <ImageSection
            v-if="currentPackage.unassignedImages.length"
            :images="currentPackage.unassignedImages"
            :selected-image-id="selectedImageId"
            :loading-group-key="regeneratingGroupKey"
            :is-loading="isRegenerating"
            :show-loading-placeholder="showUnassignedPlaceholder"
            @select="(img) => handleImageClick(img, '未归类图片')"
          />
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
              <div class="text-sm text-slate-100 mb-2">{{ currentObject.path || '未选择' }}</div>
              <div
                v-if="isImageSelected"
                class="prompt-readonly"
              >
                {{ currentObject.content || '暂无提示词' }}
              </div>
              <div v-if="isImageSelected" class="prompt-source">
                来源：{{ formatPromptSource(selectedImage?.promptSource) }}
              </div>
              <div v-else class="text-xs text-slate-300 leading-relaxed max-h-32 overflow-auto">
                {{ truncateContent(currentObject.content) }}
              </div>
              <div v-if="currentObject.kind === 'audio'" class="asset-media mt-2">
                <audio controls :src="currentAudioUrl" class="w-full"></audio>
              </div>
              <div class="text-11 text-slate-500 mt-2">提示：提交后会生成新的候选版本并存。</div>
            </div>
          </div>
          <div class="box">
            <div class="object-header">修改内容</div>
            <div v-if="isImageSelected">
              <div class="field-label">直接编辑提示词</div>
              <textarea v-model="editInput" placeholder="请输入新的图片生成提示词" />
              <div class="field-label mt-2">生成尺寸</div>
              <div class="size-config">
                <input
                  v-model="imageSizeInput"
                  class="size-input"
                  placeholder="960x1280"
                  :disabled="isSavingImageSize"
                />
                <button class="link-btn" :disabled="isSavingImageSize" @click="applyImageSize">
                  应用尺寸
                </button>
              </div>
              <div class="size-hint">默认 3:4，修改后用于后续图片生成。</div>
              <button class="main-action mt-2" :disabled="isImageBusy" @click="handleRegenerate">
                保存并重新生成
              </button>
              <button class="link-btn mt-2" :disabled="isImageBusy" @click="cancelPromptEdit">取消</button>
              <div class="divider"></div>
              <div class="field-label">修改意见</div>
              <textarea v-model="feedbackInput" placeholder="例如：更柔和的光线 / 换成夜景 / 增加环境细节" />
              <button class="link-btn mt-2" :disabled="isImageBusy" @click="submitFeedback">提交修改意见</button>
              <div v-if="isRegenerating" class="status-hint">图片生成中…</div>
              <div v-if="isPropagating" class="status-hint">正在应用美术风格传播…</div>
            </div>
            <div v-else-if="isTextSelected">
              <div class="field-label">修改意见</div>
              <textarea v-model="textFeedbackInput" placeholder="例如：更温暖的色调 / 语气更紧张" />
              <button class="link-btn mt-2" :disabled="isTextBusy" @click="submitTextFeedback">提交修改意见</button>
            </div>
            <div v-else-if="currentObject.kind === 'text'" class="empty-text">该对象暂不支持修改。</div>
            <div v-else class="empty-text">请选择图片或文本对象。</div>
          </div>
          <div class="box">
            <div class="object-header">候选版本</div>
            <div v-if="isImageSelected">
              <div v-if="currentImageCandidates.length === 0" class="empty-text">暂无候选版本</div>
              <div
                v-for="candidate in currentImageCandidates"
                :key="candidate.id || candidate.url"
                :class="['candidate-card', { selected: candidate.id && candidate.id === selectedImageId }]"
              >
                <div class="candidate-header">
                  <span>{{ candidate.isActive ? '✅ 已采用' : '候选版本' }}</span>
                  <span class="candidate-meta">{{ formatPromptSource(candidate.promptSource) }}</span>
                </div>
                <div class="candidate-body">{{ candidate.prompt || '无提示词' }}</div>
                <button
                  class="link-btn mt-2"
                  :disabled="candidate.isActive || isImageBusy || !candidate.id"
                  @click="candidate.id && handleImageClick(candidate, currentObject.path)"
                >
                  采用
                </button>
              </div>
            </div>
            <div v-else-if="isTextSelected">
              <div v-if="currentTextCandidates.length === 0" class="empty-text">暂无候选版本</div>
              <div v-for="candidate in currentTextCandidates" :key="candidate.id" class="candidate-card">
                <div class="candidate-header">
                  <span>{{ candidate.isActive ? '✅ 已采用' : '候选版本' }}</span>
                  <span class="candidate-meta">{{ candidate.source || 'user_feedback' }}</span>
                </div>
                <div v-if="candidate.feedback" class="candidate-feedback">反馈：{{ candidate.feedback }}</div>
                <div class="candidate-body">
                  <div v-if="candidate.value.styleName || candidate.value.stylePrompt">
                    <div>风格：{{ candidate.value.styleName || '未命名' }}</div>
                    <div v-if="candidate.value.stylePrompt">提示词：{{ candidate.value.stylePrompt }}</div>
                    <div v-if="candidate.value.palette && candidate.value.palette.length">
                      调色盘：{{ candidate.value.palette.join(' / ') }}
                    </div>
                  </div>
                  <div v-else>{{ candidate.value.description || '无内容' }}</div>
                </div>
                <button
                  class="link-btn mt-2"
                  :disabled="candidate.isActive || isTextBusy"
                  @click="adoptText(candidate.id)"
                >
                  采用
                </button>
              </div>
            </div>
            <div v-else-if="currentObject.kind === 'text'" class="empty-text">该对象暂无候选版本。</div>
            <div v-else class="empty-text">请选择图片或文本对象。</div>
          </div>
          <div class="flex flex-col gap-2">
            <button class="link-btn" @click="goToEditor">进入剪辑页面</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import StatusBadge from '@/components/common/StatusBadge.vue';
import ImageSection from '@/components/common/ImageSection.vue';
import { fetchProject } from '@/api/projects';
import {
  fetchMaterialPackage,
  fetchMaterialPackages,
  submitMaterialPackageFeedback,
  updateMaterialPackage,
  type MaterialPackage,
} from '@/api/material-packages';
import { startGeneration } from '@/api/generation';
import { adoptImage, regenerateImage, rewriteImagePrompt } from '@/api/images';
import { adoptTextCandidate, submitArtStyleFeedback, submitStoryboardFeedback } from '@/api/text';
import request from '@/api/request';

interface GeneratedImage {
  id?: string;
  url: string;
  prompt?: string;
  promptSource?: string;
  provider?: string;
  model?: string;
  size?: string;
  type?: string;
  sceneId?: string;
  sceneName?: string;
  subjectId?: string;
  subjectName?: string;
  view?: string;
  isActive?: boolean;
  promptParts?: {
    content?: string;
    style?: string;
    constraints?: string;
  };
}

interface ArtStyleDisplay {
  styleName: string;
  stylePrompt: string;
  palette: string[];
}

interface TextCandidate<T> {
  id: string;
  source: string;
  feedback: string;
  value: T;
  createdAt: string;
  isActive: boolean;
}

interface ArtStyleCandidateGroup {
  activeId: string;
  candidates: TextCandidate<ArtStyleDisplay>[];
}

interface StoryboardCandidateGroup {
  activeId: string;
  candidates: TextCandidate<{ description: string }>[];
}

interface SubjectDisplay {
  id?: string;
  name: string;
  role: string;
  description: string;
  views: string[];
  viewLabel: string;
  images: GeneratedImage[];
}

interface SceneDisplay {
  id?: string;
  name: string;
  description: string;
  mood: string;
  images: GeneratedImage[];
}

interface StoryboardDisplay {
  id?: string;
  shotNumber: number;
  description: string;
  sceneId: string;
  sceneName: string;
  durationSec: number;
  camera: string;
}

interface AssetPackage {
  id: string;
  title: string;
  status: 'pending' | 'loading' | 'done';
  createdAt: number;
  version: number;
  parentPackageId?: string;
  userPrompt: string;
  userFeedback: string;
  storySummary: string;
  artStyle: ArtStyleDisplay;
  artStyleCandidates: ArtStyleCandidateGroup;
  subjects: SubjectDisplay[];
  scenes: SceneDisplay[];
  storyboard: StoryboardDisplay[];
  storyboardCandidates: Record<string, StoryboardCandidateGroup>;
  unassignedImages: GeneratedImage[];
  allImages: GeneratedImage[];
  imageSize: string;
}

interface ConversationMessage {
  id: string;
  text: string;
  createdAt: number;
  role: 'user' | 'system';
  status?: 'loading' | 'completed' | 'warning' | 'error';
  step?: string;
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
const feedbackInput = ref('');
const textFeedbackInput = ref('');
const imageSizeInput = ref('960x1280');
const isSavingImageSize = ref(false);
const baseMessages = ref<ConversationMessage[]>([]);
const pendingMessages = ref<ConversationMessage[]>([]);
const streamMessages = ref<ConversationMessage[]>([]);
const conversationMessages = computed(() => {
  return [...baseMessages.value, ...pendingMessages.value, ...streamMessages.value].sort(
    (a, b) => a.createdAt - b.createdAt
  );
});
const assetPackages = ref<Record<string, AssetPackage>>({});
const currentPackageId = ref('');
const currentProjectId = ref<string | null>(null);
const selectedImage = ref<GeneratedImage | null>(null);
const originalPrompt = ref('');
const selectedTextTarget = ref<{ type: 'art_style' | 'storyboard_description'; shotId?: string } | null>(null);
const currentObject = ref<CurrentObject>({
  type: '',
  path: '请选择中间的对象进行修改',
  kind: '',
  content: '',
});
const dialogListRef = ref<HTMLDivElement | null>(null);
const streamSource = ref<EventSource | null>(null);
const streamDone = ref(false);
const streamWarningShown = ref(false);
const fallbackPollingId = ref<number | null>(null);
const streamWatchdogId = ref<number | null>(null);
const lastStreamEventAt = ref(0);
const generationSnapshotIds = ref<Set<string>>(new Set());
const lastGenerationContext = ref<{
  type: 'start' | 'feedback';
  projectId: string;
  packageId?: string;
  input: string;
} | null>(null);
const isRetrying = ref(false);

const isImageSelected = computed(() => currentObject.value.kind === 'image' && !!selectedImage.value);
const selectedImageId = computed(() => selectedImage.value?.id || '');
const isRegenerating = ref(false);
const regeneratingGroupKey = ref('');
const isTextSelected = computed(() => !!selectedTextTarget.value);
const isImageAdopting = ref(false);
const isPropagating = ref(false);
const isImageBusy = computed(() => isRegenerating.value || isImageAdopting.value || isPropagating.value);
const isTextBusy = computed(() => isTextAdopting.value || isPropagating.value);

const mapPackageStatus = (status: string) => {
  if (status === 'completed') return 'done';
  if (status === 'generating') return 'loading';
  return 'pending';
};

const formatPromptSource = (source?: string) => {
  const normalized = (source || '').trim();
  if (normalized === 'user_edit') return '直接编辑';
  if (normalized === 'user_feedback') return '修改意见生成';
  if (normalized === 'art_style_propagation') return '风格传播';
  if (normalized) return normalized;
  return '系统生成';
};

const formatImageLabel = (image: GeneratedImage) => {
  if (image.type === 'character_sheet') {
    return '三视图';
  }
  return image.prompt || '暂无提示词';
};

const buildPromptTooltip = (image: GeneratedImage) => {
  const prompt = image.prompt || '暂无提示词';
  return `提示词：${prompt}\n来源：${formatPromptSource(image.promptSource)}`;
};

const buildArtStyleContent = (artStyle: ArtStyleDisplay) => {
  const lines = [`风格：${artStyle.styleName || '未命名'}`];
  if (artStyle.stylePrompt) {
    lines.push(`提示词：${artStyle.stylePrompt}`);
  }
  if (artStyle.palette.length) {
    lines.push(`调色盘：${artStyle.palette.join(' / ')}`);
  }
  return lines.join('\n');
};

const buildSubjectContent = (subject: SubjectDisplay) => {
  const lines = [`角色：${subject.name || '未命名'}`];
  if (subject.role) {
    lines.push(`定位：${subject.role}`);
  }
  if (subject.description) {
    lines.push(`描述：${subject.description}`);
  }
  if (subject.viewLabel) {
    lines.push(`视角：${subject.viewLabel}`);
  }
  return lines.join('\n');
};

const isSubjectSelected = (subject: SubjectDisplay) => {
  return currentObject.value.type === 'subject' && currentObject.value.path === `角色 · ${subject.name}`;
};

const getImageGroupKey = (image: GeneratedImage) => {
  const type = image.type || 'scene';
  if (image.subjectId && type === 'character_sheet') {
    return `subject:${image.subjectId}:${type}`;
  }
  if (image.subjectId && image.view) {
    return `subject:${image.subjectId}:${image.view}:${type}`;
  }
  if (image.sceneId) {
    return `scene:${image.sceneId}:${type}`;
  }
  return `single:${image.id || image.url}`;
};

const startRegeneration = (image: GeneratedImage) => {
  isRegenerating.value = true;
  regeneratingGroupKey.value = getImageGroupKey(image);
};

const finishRegeneration = () => {
  isRegenerating.value = false;
  regeneratingGroupKey.value = '';
};

const isLoadingImage = (image: GeneratedImage) => {
  if (!isRegenerating.value) return false;
  return regeneratingGroupKey.value === getImageGroupKey(image);
};

const isLoadingSubject = (subject: SubjectDisplay) => {
  if (!isRegenerating.value || !selectedImage.value) return false;
  if (selectedImage.value.type !== 'character_view' && selectedImage.value.type !== 'character_sheet') return false;
  const subjectId = selectedImage.value.subjectId;
  if (subjectId && subject.id) {
    return subjectId === subject.id;
  }
  const subjectName = selectedImage.value.subjectName;
  return Boolean(subjectName && subjectName === subject.name);
};

const isLoadingScene = (scene: SceneDisplay) => {
  if (!isRegenerating.value || !selectedImage.value) return false;
  if (selectedImage.value.type !== 'scene') return false;
  const sceneId = selectedImage.value.sceneId;
  if (sceneId && scene.id) {
    return sceneId === scene.id;
  }
  const sceneName = selectedImage.value.sceneName;
  return Boolean(sceneName && sceneName === scene.name);
};

const showUnassignedPlaceholder = computed(() => {
  if (!isRegenerating.value || !selectedImage.value) return false;
  const pkg = currentPackage.value;
  if (!pkg) return false;
  return pkg.unassignedImages.some(img => img.id && img.id === selectedImage.value?.id);
});

const currentImageCandidates = computed(() => {
  const pkg = currentPackage.value;
  const image = selectedImage.value;
  if (!pkg || !image) {
    return [] as GeneratedImage[];
  }
  const groupKey = getImageGroupKey(image);
  return pkg.allImages.filter(item => getImageGroupKey(item) === groupKey);
});

const currentTextCandidates = computed(() => {
  const pkg = currentPackage.value;
  const target = selectedTextTarget.value;
  if (!pkg || !target) {
    return [] as TextCandidate<any>[];
  }
  if (target.type === 'art_style') {
    return pkg.artStyleCandidates.candidates;
  }
  if (target.type === 'storyboard_description' && target.shotId) {
    return pkg.storyboardCandidates[target.shotId]?.candidates || [];
  }
  return [] as TextCandidate<any>[];
});

const isTextAdopting = ref(false);

const submitTextFeedback = async () => {
  const pkg = currentPackage.value;
  const target = selectedTextTarget.value;
  if (!pkg || !target) {
    alert('请选择要修改的文本项');
    return;
  }
  const feedback = textFeedbackInput.value.trim();
  if (!feedback) {
    alert('请输入修改意见');
    return;
  }
  try {
    if (target.type === 'art_style') {
      await submitArtStyleFeedback(pkg.id, feedback);
    } else if (target.type === 'storyboard_description' && target.shotId) {
      await submitStoryboardFeedback(pkg.id, target.shotId, feedback);
    }
    textFeedbackInput.value = '';
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '提交修改意见失败');
  }
};

const adoptText = async (candidateId: string) => {
  const pkg = currentPackage.value;
  const target = selectedTextTarget.value;
  if (!pkg || !target) {
    alert('请选择要采用的文本项');
    return;
  }
  if (!candidateId) {
    alert('候选版本缺少 ID');
    return;
  }
  isTextAdopting.value = true;
  try {
    if (target.type === 'art_style') {
      await adoptTextCandidate(pkg.id, 'art_style', candidateId);
      await loadPackages();
      await confirmArtStylePropagation();
      return;
    } else if (target.type === 'storyboard_description' && target.shotId) {
      await adoptTextCandidate(pkg.id, 'storyboard_description', candidateId, target.shotId);
    }
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '采用候选版本失败');
  } finally {
    isTextAdopting.value = false;
  }
};

const buildArtStyleSuffix = (artStyle: ArtStyleDisplay) => {
  const parts: string[] = [];
  if (artStyle.stylePrompt) {
    parts.push(artStyle.stylePrompt.trim());
  }
  if (artStyle.palette.length) {
    parts.push(`Palette: ${artStyle.palette.join(', ')}`);
  }
  return parts.filter(Boolean).join('\n').trim();
};

const buildPropagationPrompt = (image: GeneratedImage, artStyle: ArtStyleDisplay) => {
  const content = (image.promptParts?.content || image.prompt || '').trim();
  const style = buildArtStyleSuffix(artStyle);
  if (content && style) {
    return `${content}\n\nStyle: ${style}`.trim();
  }
  return content || style;
};

const propagateArtStyleToImages = async (artStyle: ArtStyleDisplay) => {
  const pkg = currentPackage.value;
  if (!pkg) {
    return;
  }
  const candidates = pkg.allImages.filter(image => image.id);
  if (candidates.length === 0) {
    alert('当前素材包没有可重新生成的图片');
    return;
  }
  isPropagating.value = true;
  try {
    for (const image of candidates) {
      if (!image.id) continue;
      const prompt = buildPropagationPrompt(image, artStyle);
      if (!prompt) continue;
      const size = getImageSizeForGeneration();
      await regenerateImage(image.id, prompt, "art_style_propagation", size || undefined);
    }
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '美术风格传播失败');
  } finally {
    isPropagating.value = false;
  }
};

const confirmArtStylePropagation = async () => {
  const pkg = currentPackage.value;
  if (!pkg) return;
  const confirmed = window.confirm('是否基于当前美术风格，重新生成相关图片？');
  if (!confirmed) return;
  await propagateArtStyleToImages(pkg.artStyle);
};

const normalizeText = (value: unknown, fallback = '') => {
  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }
  return fallback;
};

const normalizeList = (value: unknown) => (Array.isArray(value) ? value : []);

const parseImageSize = (value: string) => {
  const match = String(value || '').trim().match(/^(\d+)\s*[xX]\s*(\d+)$/);
  if (!match) return null;
  const width = Number(match[1]);
  const height = Number(match[2]);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return null;
  }
  return { width, height, size: `${width}x${height}` };
};

const formatAspectRatio = (width: number, height: number) => {
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(width, height) || 1;
  return `${Math.round(width / divisor)}:${Math.round(height / divisor)}`;
};

const getImageSizeForGeneration = () => {
  const parsed = parseImageSize(imageSizeInput.value);
  if (parsed) {
    return parsed.size;
  }
  const fallback = currentPackage.value?.imageSize || '';
  const fallbackParsed = parseImageSize(fallback);
  return fallbackParsed?.size || '';
};

const mapMaterialPackage = (pkg: MaterialPackage): AssetPackage => {
  const materials = pkg.materials || {};
  const metadata = (materials as any).metadata || {};
  const blueprint = (metadata as any).blueprint_v1 || {};
  const summary = (blueprint as any).summary || {};
  const generation = (blueprint as any).generation || {};
  const artStyleRaw = (blueprint as any).art_style || {};
  const textCandidatesRaw = (metadata as any).text_candidates_v1 || {};
  const packageVersion = Number.isFinite((metadata as any).package_version)
    ? Number((metadata as any).package_version)
    : 1;
  const packageName = normalizeText((metadata as any).package_name, normalizeText(pkg.package_name, '素材包'));
  const parentPackageId = normalizeText((metadata as any).parent_package_id, normalizeText((pkg as any).parent_id, ''));
  const imageSize = normalizeText(
    (metadata as any).image_size,
    normalizeText((metadata as any).image_plan?.size, '960x1280')
  );

  const storySummary = normalizeText(
    summary.logline,
    normalizeText(summary.synopsis, pkg.summary || '生成中…')
  );
  const userPrompt = normalizeText(
    (metadata as any).user_prompt,
    normalizeText(generation.source_prompt, '')
  );
  const userFeedback = normalizeText((metadata as any).user_feedback, '');

  const blueprintArtStyle: ArtStyleDisplay = {
    styleName: normalizeText(artStyleRaw.style_name || artStyleRaw.styleName || artStyleRaw.name, '生成中…'),
    stylePrompt: normalizeText(artStyleRaw.style_prompt || artStyleRaw.stylePrompt, ''),
    palette: normalizeList(artStyleRaw.palette)
      .map(item => (typeof item === 'string' ? item.trim() : String(item)))
      .filter(item => item),
  };

  const artStyleCandidatesRaw = (textCandidatesRaw as any).art_style || {};
  const artStyleCandidateList = normalizeList(artStyleCandidatesRaw.candidates).map((item: any) => {
    const value = item?.value || {};
    return {
      id: normalizeText(item?.id, ''),
      source: normalizeText(item?.source, ''),
      feedback: normalizeText(item?.feedback, ''),
      value: {
        styleName: normalizeText(value.style_name || value.styleName || value.name, ''),
        stylePrompt: normalizeText(value.style_prompt || value.stylePrompt, ''),
        palette: normalizeList(value.palette)
          .map((paletteItem: any) => (typeof paletteItem === 'string' ? paletteItem.trim() : String(paletteItem)))
          .filter((paletteItem: string) => paletteItem),
      },
      createdAt: normalizeText(item?.created_at, ''),
      isActive: normalizeText(item?.id, '') === normalizeText(artStyleCandidatesRaw.active_id, ''),
    };
  });
  const artStyleCandidates: ArtStyleCandidateGroup = {
    activeId: normalizeText(artStyleCandidatesRaw.active_id, ''),
    candidates: artStyleCandidateList,
  };
  const activeArtStyleCandidate = artStyleCandidates.candidates.find(candidate => candidate.isActive);
  const artStyle: ArtStyleDisplay = activeArtStyleCandidate?.value || blueprintArtStyle;

  const rawImages = Array.isArray(metadata.images)
    ? metadata.images.filter((item: any) => !(item && typeof item === 'object' && item.type === 'storyboard'))
    : [];
  const images: GeneratedImage[] = rawImages
    .filter((item: any) => item && typeof item.url === 'string' && item.url.length > 0)
    .map((item: any) => {
      const sceneId = normalizeText(item.scene_id || item.sceneId, '');
      const sceneName = normalizeText(item.scene_name || item.sceneName, '');
      const subjectId = normalizeText(item.subject_id || item.character_id || item.subjectId || item.characterId, '');
      const subjectName = normalizeText(item.subject_name || item.character_name || item.subjectName || item.characterName, '');
      const rawType = typeof item.type === 'string' ? item.type : '';
      const type = rawType || (subjectId ? 'character_sheet' : 'scene');
      const parts = item.prompt_parts && typeof item.prompt_parts === 'object' ? item.prompt_parts : null;
      const promptParts = parts
        ? {
            content: normalizeText(parts.content, ''),
            style: normalizeText(parts.style, ''),
            constraints: normalizeText(parts.constraints, ''),
          }
        : undefined;
      return {
        id: normalizeText(item.id, ''),
        url: item.url,
        prompt: typeof item.prompt === 'string' ? item.prompt : undefined,
        promptSource: normalizeText(item.prompt_source, ''),
        provider: typeof item.provider === 'string' ? item.provider : undefined,
        model: typeof item.model === 'string' ? item.model : undefined,
        size: typeof item.size === 'string' ? item.size : undefined,
        type,
        sceneId,
        sceneName,
        subjectId,
        subjectName,
        view: normalizeText(item.view, ''),
        isActive: typeof item.is_active === 'boolean' ? item.is_active : undefined,
        promptParts,
      };
    });

  const groupKey = (image: GeneratedImage) => {
    const type = image.type || 'scene';
    if (image.subjectId && image.view) {
      return `subject:${image.subjectId}:${image.view}:${type}`;
    }
    if (image.sceneId) {
      return `scene:${image.sceneId}:${type}`;
    }
    return `single:${image.id || image.url}`;
  };

  const activeByGroup = new Map<string, string>();
  images.forEach(image => {
    if (!image.isActive) return;
    const key = groupKey(image);
    if (!activeByGroup.has(key)) {
      activeByGroup.set(key, image.id || image.url);
    }
  });

  const seenGroup = new Set<string>();
  images.forEach(image => {
    const key = groupKey(image);
    if (!activeByGroup.has(key) && !seenGroup.has(key)) {
      activeByGroup.set(key, image.id || image.url);
      seenGroup.add(key);
    }
  });

  images.forEach(image => {
    const key = groupKey(image);
    const activeKey = activeByGroup.get(key);
    image.isActive = Boolean(activeKey && activeKey === (image.id || image.url));
  });

  const subjectImages = images.filter(item => item.type === 'character_view' || item.type === 'character_sheet');
  const sceneImages = images.filter(item => item.type === 'scene');

  const subjectsRaw = normalizeList((blueprint as any).subjects);
  const scenesRaw = normalizeList((blueprint as any).scenes);
  const storyboardRaw = normalizeList((blueprint as any).storyboard);

  const sceneNameById = new Map<string, string>();
  scenesRaw.forEach((scene: any, index: number) => {
    const id = normalizeText(scene.id, `scene_${index + 1}`);
    const name = normalizeText(scene.name, `场景 ${index + 1}`);
    sceneNameById.set(id, name);
  });

  const subjects: SubjectDisplay[] = subjectsRaw.map((subject: any, index: number) => {
    const id = normalizeText(subject.id, `char_${index + 1}`);
    const name = normalizeText(subject.name, `角色 ${index + 1}`);
    const role = normalizeText(subject.role, '未指定');
    const description = normalizeText(subject.description, '');
    const views = normalizeList(subject.views).map((view: any) => String(view)).filter(view => view) as string[];
    const resolvedViews = views.length > 0 ? views : ['front', 'side', 'back'];
    const imagesForSubject = subjectImages.filter(img => {
      if (img.subjectId && id) {
        return img.subjectId === id;
      }
      if (img.subjectName && name) {
        return img.subjectName.toLowerCase() === name.toLowerCase();
      }
      return false;
    });
    const hasSheet = imagesForSubject.some(img => img.type === 'character_sheet');
    const viewLabel = hasSheet ? '三视图' : resolvedViews.join(' / ');
    return {
      id,
      name,
      role,
      description,
      views: resolvedViews,
      viewLabel,
      images: imagesForSubject,
    };
  });

  const scenes: SceneDisplay[] = scenesRaw.map((scene: any, index: number) => {
    const id = normalizeText(scene.id, `scene_${index + 1}`);
    const name = normalizeText(scene.name, `场景 ${index + 1}`);
    const description = normalizeText(scene.description, '');
    const mood = normalizeText(scene.mood, '未指定');
    const imagesForScene = sceneImages.filter(img => {
      if (img.sceneId && id) {
        return img.sceneId === id;
      }
      if (img.sceneName && name) {
        return img.sceneName.toLowerCase() === name.toLowerCase();
      }
      return false;
    });
    return {
      id,
      name,
      description,
      mood,
      images: imagesForScene,
    };
  });

  const storyboardCandidateRaw = (textCandidatesRaw as any).storyboard || {};
  const storyboardCandidates: Record<string, StoryboardCandidateGroup> = {};

  const storyboard: StoryboardDisplay[] = storyboardRaw.map((shot: any, index: number) => {
    const shotNumber = typeof shot.shot_number === 'number' ? shot.shot_number : index + 1;
    const sceneId = normalizeText(shot.scene_id, 'scene_1');
    const sceneName = sceneNameById.get(sceneId) || '';
    const shotId = normalizeText(shot.id, `shot_${index + 1}`);
    const shotCandidatesRaw = storyboardCandidateRaw[shotId] || {};
    const shotCandidateList = normalizeList(shotCandidatesRaw.candidates).map((item: any) => ({
      id: normalizeText(item?.id, ''),
      source: normalizeText(item?.source, ''),
      feedback: normalizeText(item?.feedback, ''),
      value: { description: normalizeText(item?.value?.description, '') },
      createdAt: normalizeText(item?.created_at, ''),
      isActive: normalizeText(item?.id, '') === normalizeText(shotCandidatesRaw.active_id, ''),
    }));
    storyboardCandidates[shotId] = {
      activeId: normalizeText(shotCandidatesRaw.active_id, ''),
      candidates: shotCandidateList,
    };
    const activeShotCandidate = shotCandidateList.find(candidate => candidate.isActive);
    const description = activeShotCandidate?.value.description || normalizeText(shot.description, '');
    const durationSec = typeof shot.duration_sec === 'number' && shot.duration_sec > 0 ? shot.duration_sec : 3;
    const camera = normalizeText(shot.camera, '');
    return {
      id: shotId,
      shotNumber,
      description,
      sceneId,
      sceneName,
      durationSec,
      camera,
    };
  });

  const imageKey = (img: GeneratedImage) =>
    [img.url, img.type, img.sceneId, img.subjectId, img.view].filter(Boolean).join('|');
  const usedImageKeys = new Set<string>();
  subjects.forEach(subject => subject.images.forEach(img => usedImageKeys.add(imageKey(img))));
  scenes.forEach(scene => scene.images.forEach(img => usedImageKeys.add(imageKey(img))));
  const unassignedImages = images.filter(img => !usedImageKeys.has(imageKey(img)));

  return {
    id: pkg.id,
    title: packageName,
    status: mapPackageStatus(pkg.status),
    createdAt: pkg.created_at ? Date.parse(pkg.created_at) : Date.now(),
    version: packageVersion,
    parentPackageId: parentPackageId || undefined,
    userPrompt,
    userFeedback,
    storySummary,
    artStyle,
    artStyleCandidates,
    subjects,
    scenes,
    storyboard,
    storyboardCandidates,
    unassignedImages,
    allImages: images,
    imageSize,
  };
};

const addPendingUserMessage = (text: string, createdAt = Date.now()) => {
  const normalized = text.trim();
  if (!normalized) return;
  const existingTexts = new Set([
    ...baseMessages.value.map(item => item.text),
    ...pendingMessages.value.map(item => item.text),
  ]);
  if (existingTexts.has(normalized)) {
    return;
  }
  pendingMessages.value.push({
    id: `pending-${createdAt}-${Math.random().toString(16).slice(2)}`,
    text: normalized,
    createdAt,
    role: 'user',
  });
};

const resetStreamMessages = () => {
  streamMessages.value = [];
};

const upsertStreamMessage = (payload: { step?: string; status?: string; message?: string }) => {
  const step = typeof payload.step === 'string' ? payload.step : '';
  const status = payload.status === 'completed' ? 'completed' : 'loading';
  const text = typeof payload.message === 'string' ? payload.message : '';
  const existingIndex = streamMessages.value.findIndex(item => item.step === step);
  if (existingIndex >= 0) {
    const existing = streamMessages.value[existingIndex];
    streamMessages.value[existingIndex] = {
      ...existing,
      text: text || existing.text,
      status,
    };
    return;
  }
  streamMessages.value.push({
    id: `stream-${step || 'step'}-${Date.now()}`,
    text,
    createdAt: Date.now(),
    role: 'system',
    status,
    step: step || undefined,
  });
};

const pushStreamError = (message: string, step?: string) => {
  streamMessages.value.push({
    id: `stream-error-${Date.now()}`,
    text: message,
    createdAt: Date.now(),
    role: 'system',
    status: 'error',
    step,
  });
};

const pushStreamWarning = (message: string) => {
  if (streamWarningShown.value) return;
  streamWarningShown.value = true;
  streamMessages.value.push({
    id: `stream-warning-${Date.now()}`,
    text: message,
    createdAt: Date.now(),
    role: 'system',
    status: 'warning',
  });
};

const stepLabels: Record<string, string> = {
  outline: '故事梗概',
  art_style: '美术风格',
  characters: '角色设定',
  character_images: '角色三视图',
  scenes: '场景设定',
  scene_images: '场景图',
  storyboard: '分镜剧本',
  done: '素材包',
};

const formatErrorMessage = (step?: string) => {
  const label = step && stepLabels[step] ? stepLabels[step] : '生成步骤';
  return `在生成【${label}】时遇到问题`;
};

const stopFallbackPolling = () => {
  if (fallbackPollingId.value) {
    window.clearInterval(fallbackPollingId.value);
    fallbackPollingId.value = null;
  }
};

const startFallbackPolling = () => {
  if (fallbackPollingId.value) {
    return;
  }
  // Fallback polling avoids leaving users without updates when SSE disconnects.
  pushStreamWarning('正在生成中，如未自动更新，你可以稍后查看结果');
  fallbackPollingId.value = window.setInterval(async () => {
    if (!currentProjectId.value) {
      return;
    }
    try {
      const data = await fetchMaterialPackages(currentProjectId.value);
      const hasNewCompleted = (data.list || []).some(item => {
        const id = item?.id;
        if (!id || generationSnapshotIds.value.has(id)) {
          return false;
        }
        return item.status === 'completed';
      });
      if (hasNewCompleted) {
        await loadPackages();
        stopFallbackPolling();
      }
    } catch (err) {
      // Ignore polling errors to avoid loops; SSE may recover.
    }
  }, 10000);
};

const stopStreamWatchdog = () => {
  if (streamWatchdogId.value) {
    window.clearInterval(streamWatchdogId.value);
    streamWatchdogId.value = null;
  }
};

const startStreamWatchdog = () => {
  stopStreamWatchdog();
  streamWatchdogId.value = window.setInterval(() => {
    if (streamDone.value) {
      return;
    }
    const now = Date.now();
    if (now - lastStreamEventAt.value > 30000) {
      startFallbackPolling();
    }
  }, 5000);
};

const closeGenerationStream = () => {
  if (streamSource.value) {
    streamSource.value.close();
    streamSource.value = null;
  }
  stopStreamWatchdog();
  stopFallbackPolling();
};

const openGenerationStream = (
  projectId: string,
  context?: { type: 'start' | 'feedback'; input: string; packageId?: string }
) => {
  if (!projectId) return;
  closeGenerationStream();
  stopFallbackPolling();
  resetStreamMessages();
  streamDone.value = false;
  streamWarningShown.value = false;
  lastStreamEventAt.value = Date.now();
  generationSnapshotIds.value = new Set(Object.keys(assetPackages.value));
  if (context) {
    lastGenerationContext.value = {
      type: context.type,
      projectId,
      packageId: context.packageId,
      input: context.input,
    };
  }
  const baseUrl = request.defaults.baseURL || '';
  const streamUrl = `${baseUrl}/generation/stream/${projectId}`;
  const source = new EventSource(streamUrl);
  streamSource.value = source;
  startStreamWatchdog();

  source.onmessage = event => {
    if (!event.data) return;
    lastStreamEventAt.value = Date.now();
    let payload: any;
    try {
      payload = JSON.parse(event.data);
    } catch (err) {
      return;
    }
    if (payload?.type === 'generation.step') {
      upsertStreamMessage(payload);
      if (payload.step === 'done' && payload.status === 'completed') {
        streamDone.value = true;
        stopFallbackPolling();
        closeGenerationStream();
        sessionStorage.removeItem('streamProjectId');
        sessionStorage.removeItem('streamPrompt');
        sessionStorage.removeItem('streamStartedAt');
        sessionStorage.removeItem('streamType');
        sessionStorage.removeItem('streamFeedback');
        sessionStorage.removeItem('streamFeedbackPackageId');
        loadPackages().catch(() => null);
      }
      return;
    }
    if (payload?.type === 'generation.error') {
      const errorText = formatErrorMessage(payload.step);
      pushStreamError(errorText, payload.step);
      stopFallbackPolling();
      closeGenerationStream();
    }
  };

  source.onerror = () => {
    if (!streamDone.value) {
      startFallbackPolling();
    }
  };
};

const retryGeneration = async () => {
  const context = lastGenerationContext.value;
  if (!context || !context.projectId || !context.input) {
    alert('缺少可重试的生成信息');
    return;
  }
  if (isRetrying.value) {
    return;
  }
  isRetrying.value = true;
  resetStreamMessages();
  try {
    // Retry uses the same entry point that initiated generation to preserve package semantics.
    if (context.type === 'feedback' && context.packageId) {
      sessionStorage.setItem('streamProjectId', context.projectId);
      sessionStorage.setItem('streamType', 'feedback');
      sessionStorage.setItem('streamFeedback', context.input);
      sessionStorage.setItem('streamFeedbackPackageId', context.packageId);
      sessionStorage.setItem('streamStartedAt', String(Date.now()));
      openGenerationStream(context.projectId, context);
      await submitMaterialPackageFeedback(context.packageId, context.input);
      return;
    }
    sessionStorage.setItem('streamProjectId', context.projectId);
    sessionStorage.setItem('streamType', 'start');
    sessionStorage.setItem('streamPrompt', context.input);
    sessionStorage.setItem('streamStartedAt', String(Date.now()));
    const mode = sessionStorage.getItem('currentMode') || undefined;
    openGenerationStream(context.projectId, context);
    await startGeneration(context.projectId, context.input, mode || undefined);
  } catch (err) {
    closeGenerationStream();
    alert(err instanceof Error ? err.message : '重试失败');
  } finally {
    isRetrying.value = false;
  }
};

const rebuildConversationMessages = (packages: AssetPackage[]) => {
  const sorted = [...packages].sort((a, b) => a.createdAt - b.createdAt);
  const messages: ConversationMessage[] = [];
  sorted.forEach(pkg => {
    if (!pkg.parentPackageId) {
      if (pkg.userPrompt) {
        messages.push({
          id: `msg-${pkg.id}-prompt`,
          text: pkg.userPrompt,
          createdAt: pkg.createdAt,
          role: 'user',
        });
      }
      return;
    }
    if (pkg.userFeedback) {
      messages.push({
        id: `msg-${pkg.id}-feedback`,
        text: pkg.userFeedback,
        createdAt: pkg.createdAt,
        role: 'user',
      });
    }
  });
  baseMessages.value = messages;
  const existingTexts = new Set(messages.map(item => item.text));
  pendingMessages.value = pendingMessages.value.filter(item => !existingTexts.has(item.text));
};

const sortedPackages = computed(() => {
  return Object.values(assetPackages.value).sort((a, b) => b.createdAt - a.createdAt);
});

const currentPackage = computed(() => {
  return assetPackages.value[currentPackageId.value];
});

watch(
  () => currentPackage.value?.id,
  () => {
    imageSizeInput.value = currentPackage.value?.imageSize || '960x1280';
  },
  { immediate: true }
);

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
  selectedImage.value = null;
  originalPrompt.value = '';
  feedbackInput.value = '';
  selectedTextTarget.value = null;
  textFeedbackInput.value = '';
};

const selectImage = (image: GeneratedImage, path: string) => {
  currentObject.value = {
    type: 'image',
    path,
    content: image.prompt || '',
    kind: 'image',
  };
  selectedImage.value = image;
  originalPrompt.value = image.prompt || '';
  editInput.value = image.prompt || '';
  feedbackInput.value = '';
  selectedTextTarget.value = null;
  textFeedbackInput.value = '';
};

const selectTextTarget = (
  target: { type: 'art_style' | 'storyboard_description'; shotId?: string },
  path: string,
  content: string
) => {
  currentObject.value = {
    type: target.type,
    path,
    content,
    kind: 'text',
  };
  selectedTextTarget.value = target;
  textFeedbackInput.value = '';
  selectedImage.value = null;
  originalPrompt.value = '';
  editInput.value = '';
  feedbackInput.value = '';
};

const handleImageClick = async (image: GeneratedImage, path: string) => {
  selectImage(image, path);
  if (image.isActive || isImageBusy.value) {
    return;
  }
  if (!image.id) {
    alert('当前图片缺少 ID，无法设为采用');
    return;
  }
  try {
    isImageAdopting.value = true;
    await adoptImage(image.id);
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '设为采用失败');
  } finally {
    isImageAdopting.value = false;
  }
};

const truncateContent = (content: string) => {
  if (!content) return '';
  return content.length > 200 ? content.substring(0, 200) + '...' : content;
};

const sendChat = async () => {
  const text = chatInput.value.trim();
  if (!text) return;
  if (!currentProjectId.value || !currentPackageId.value) {
    return;
  }
  chatInput.value = '';
  addPendingUserMessage(text);
  sessionStorage.setItem('streamProjectId', currentProjectId.value);
  sessionStorage.setItem('streamType', 'feedback');
  sessionStorage.setItem('streamFeedback', text);
  sessionStorage.setItem('streamFeedbackPackageId', currentPackageId.value);
  sessionStorage.setItem('streamStartedAt', String(Date.now()));
  openGenerationStream(currentProjectId.value, {
    type: 'feedback',
    input: text,
    packageId: currentPackageId.value,
  });

  try {
    await submitMaterialPackageFeedback(currentPackageId.value, text);
  } catch (err) {
    closeGenerationStream();
    alert(err instanceof Error ? err.message : '提交修改意见失败');
  }
};

const handleChatKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
};

const handleRegenerate = async () => {
  if (!selectedImage.value) {
    alert('请选择图片以编辑提示词');
    return;
  }
  if (!selectedImage.value.id) {
    alert('当前图片缺少 ID，无法重新生成');
    return;
  }
  const prompt = editInput.value.trim();
  if (!prompt) {
    alert('请输入图片生成提示词');
    return;
  }
  startRegeneration(selectedImage.value);
  try {
    const size = getImageSizeForGeneration();
    await regenerateImage(selectedImage.value.id, prompt, "user_edit", size || undefined);
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '重新生成失败');
  } finally {
    finishRegeneration();
  }
};

const applyImageSize = async () => {
  if (!currentPackageId.value) {
    return;
  }
  const parsed = parseImageSize(imageSizeInput.value);
  if (!parsed) {
    alert('尺寸格式应为 960x1280');
    return;
  }
  imageSizeInput.value = parsed.size;
  isSavingImageSize.value = true;
  try {
    const pkgDetail = await fetchMaterialPackage(currentPackageId.value);
    const materials = typeof pkgDetail.materials === 'object' && pkgDetail.materials ? { ...pkgDetail.materials } : {};
    const metadata = typeof (materials as any).metadata === 'object' ? { ...(materials as any).metadata } : {};
    metadata.image_size = parsed.size;
    const imagePlan = typeof metadata.image_plan === 'object' ? { ...metadata.image_plan } : {};
    imagePlan.size = parsed.size;
    imagePlan.aspect_ratio = formatAspectRatio(parsed.width, parsed.height);
    metadata.image_plan = imagePlan;
    const blueprint = typeof metadata.blueprint_v1 === 'object' ? { ...metadata.blueprint_v1 } : {};
    const generation = typeof blueprint.generation === 'object' ? { ...blueprint.generation } : {};
    generation.aspect_ratio = formatAspectRatio(parsed.width, parsed.height);
    generation.image_size = parsed.size;
    blueprint.generation = generation;
    metadata.blueprint_v1 = blueprint;
    (materials as any).metadata = metadata;
    await updateMaterialPackage(currentPackageId.value, { materials });
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '更新尺寸失败');
  } finally {
    isSavingImageSize.value = false;
  }
};

const cancelPromptEdit = () => {
  editInput.value = originalPrompt.value;
};

const submitFeedback = async () => {
  if (!selectedImage.value) {
    alert('请选择图片以提交修改意见');
    return;
  }
  if (!selectedImage.value.id) {
    alert('当前图片缺少 ID，无法提交修改意见');
    return;
  }
  const feedback = feedbackInput.value.trim();
  if (!feedback) {
    alert('请输入修改意见');
    return;
  }
  startRegeneration(selectedImage.value);
  try {
    const result = await rewriteImagePrompt(selectedImage.value.id, feedback);
    const size = getImageSizeForGeneration();
    await regenerateImage(selectedImage.value.id, result.rewritten_prompt, "user_feedback", size || undefined);
    feedbackInput.value = '';
    await loadPackages();
  } catch (err) {
    alert(err instanceof Error ? err.message : '提交修改意见失败');
  } finally {
    finishRegeneration();
  }
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
    rebuildConversationMessages(mapped);
  } else {
    baseMessages.value = [];
  }
  if (streamSource.value && generationSnapshotIds.value.size === 0) {
    generationSnapshotIds.value = new Set(Object.keys(assetPackages.value));
  }
};

const maybeStartStreamFromSession = () => {
  const streamProjectId = sessionStorage.getItem('streamProjectId');
  if (!streamProjectId || streamProjectId !== currentProjectId.value) {
    return;
  }
  const streamType = sessionStorage.getItem('streamType') || 'start';
  const startedAt = Number(sessionStorage.getItem('streamStartedAt')) || Date.now();
  if (streamType === 'feedback') {
    const feedback = sessionStorage.getItem('streamFeedback') || '';
    const packageId = sessionStorage.getItem('streamFeedbackPackageId') || undefined;
    if (feedback) {
      addPendingUserMessage(feedback, startedAt);
    }
    openGenerationStream(streamProjectId, {
      type: 'feedback',
      input: feedback,
      packageId,
    });
    return;
  }
  const streamPrompt = sessionStorage.getItem('streamPrompt') || '';
  if (streamPrompt) {
    addPendingUserMessage(streamPrompt, startedAt);
  }
  openGenerationStream(streamProjectId, {
    type: 'start',
    input: streamPrompt,
  });
};

onMounted(async () => {
  const storedProjectId = sessionStorage.getItem('currentProjectId');
  if (!storedProjectId) {
    router.push('/space');
    return;
  }
  currentProjectId.value = storedProjectId;
  maybeStartStreamFromSession();

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

onUnmounted(() => {
  closeGenerationStream();
  stopFallbackPolling();
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

.status-icon {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(121, 116, 126, 0.35);
  border-top-color: var(--md-primary);
  animation: spin 0.9s linear infinite;
  flex-shrink: 0;
}

.status-icon.completed {
  border: none;
  background: #28c76f;
  animation: none;
  position: relative;
}

.status-icon.warning {
  border: none;
  background: #f6c343;
  animation: none;
}

.status-icon.completed::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 2px;
  width: 3px;
  height: 6px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.status-icon.error {
  border: none;
  background: #ff5c5c;
  animation: none;
}

.assistant-foot {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 6px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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

.section.selected {
  border-color: rgba(103, 80, 164, 0.6);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.15);
  border-radius: 12px;
  padding: 12px;
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

.size-config {
  display: flex;
  align-items: center;
  gap: 8px;
}

.size-input {
  flex: 1;
  height: 36px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
  color: var(--md-on-surface);
  border-radius: 8px;
  padding: 6px 8px;
}

.size-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
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

.prompt-readonly {
  font-size: 12px;
  color: var(--md-on-surface);
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 8px;
  padding: 8px;
  max-height: 180px;
  overflow: auto;
  white-space: pre-wrap;
}

.prompt-source {
  margin-top: 6px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.candidate-card {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 8px;
  padding: 8px;
  background: var(--md-surface-container-low);
  margin-top: 8px;
}

.candidate-card.selected {
  border-color: rgba(103, 80, 164, 0.8);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.2);
}

.candidate-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--md-on-surface);
}

.candidate-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.candidate-feedback {
  margin-top: 4px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.candidate-body {
  margin-top: 6px;
  font-size: 12px;
  color: var(--md-on-surface);
  white-space: pre-wrap;
}

.field-label {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 6px;
}

.divider {
  height: 1px;
  background: rgba(121, 116, 126, 0.2);
  margin: 10px 0;
}

.status-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.detail-card {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  padding: 10px;
  background: var(--md-surface-container-low);
  margin-bottom: 12px;
}

.detail-card.selected {
  border-color: rgba(103, 80, 164, 0.8);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.2);
}

.detail-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--md-on-surface);
  margin-bottom: 6px;
}

.detail-row {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 4px;
}

.empty-text {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.thumb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin-top: 8px;
}

.thumb-card {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 8px;
  overflow: hidden;
  background: var(--md-surface);
  position: relative;
}

.thumb-card.selected {
  border-color: rgba(103, 80, 164, 0.8);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.2);
}

.thumb-card.loading {
  opacity: 0.7;
}

.thumb-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
  background: rgba(0, 0, 0, 0.04);
  display: block;
}

.thumb-active {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 11px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 2px 6px;
  border-radius: 999px;
}

.loading-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  color: var(--md-on-surface-variant);
  font-size: 12px;
  border-style: dashed;
}

.loading-text {
  padding: 6px;
}

.thumb-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  padding: 6px;
  max-height: 40px;
  overflow: hidden;
}

.storyboard-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.storyboard-item {
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 10px;
  padding: 10px;
  background: var(--md-surface-container-low);
}

.storyboard-item.selected {
  border-color: rgba(103, 80, 164, 0.8);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.2);
}

.storyboard-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--md-on-surface);
}

.storyboard-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin: 4px 0;
}

.storyboard-desc {
  font-size: 12px;
  color: var(--md-on-surface);
}
</style>
