<template>
  <div class="editor-page">
    <div class="top-ops">
      <div class="project-meta">
        <div class="project-name">{{ projectName }}</div>
        <div class="package-meta">
          <span class="tag">素材包</span>
          <span class="package-name">{{ packageName || '未选择素材包' }}</span>
        </div>
      </div>
      <div class="floating-ops">
        <button
          class="pill-btn"
          :disabled="clips.length === 0 || isBulkGeneratingVideo"
          @click="generateAllVideos"
        >
          一键导出视频
        </button>
        <button class="pill-btn ghost" @click="goBack">← 返回素材</button>
      </div>
    </div>

    <div class="editor-layout">
      <div class="editor-left">
        <div v-if="currentClip" class="shot-panel">
          <div class="panel-title">剪辑操作栏</div>
          <div class="shot-header">
            <div class="shot-title">分镜 {{ currentClip.sequenceLabel }}</div>
            <div class="shot-sub">{{ currentClip.sceneName || '未关联场景' }}</div>
          </div>
          <div class="shot-status" :class="{ pending: currentClip.status !== 'ready' }">
            {{ currentClip.status === 'ready' ? '素材已准备' : '待生成画面' }}
          </div>

          <div class="info-card">
            <div class="info-title">分镜信息</div>
            <div class="info-row">
              <span class="label">时长</span>
              <span class="value">{{ currentClip.durationSec }}s</span>
            </div>
            <div class="info-row">
              <span class="label">镜头</span>
              <span class="value">{{ currentClip.camera || '未指定' }}</span>
            </div>
            <div class="info-row">
              <span class="label">描述</span>
            </div>
            <p class="info-text">{{ currentClip.description || '暂无描述' }}</p>
          </div>

          <div class="info-card">
            <button class="collapse-header" @click="toggleImagePrompt">
              <span>生图提示词</span>
              <span class="collapse-hint">{{ isImagePromptOpen ? '收起' : '展开' }}</span>
            </button>
            <div v-if="isImagePromptOpen" class="collapse-body">
              <div v-if="!isEditingPrompt" class="prompt-readonly" @click="startPromptEdit">
                {{ currentClip.prompt || '暂无提示词，点击编辑补充' }}
              </div>
              <textarea
                v-else
                v-model="promptDraft"
                class="prompt-editor"
                rows="4"
                placeholder="编辑分镜画面提示词"
              ></textarea>
              <div class="action-row">
                <button
                  v-if="!isEditingPrompt"
                  class="pill-btn"
                  :disabled="currentClip.status !== 'ready' || isRegeneratingImage"
                  @click="startPromptEdit"
                >
                  编辑提示词
                </button>
                <button
                  v-else
                  class="pill-btn primary"
                  :disabled="isRegeneratingImage || !promptDraft.trim() || currentClip.status !== 'ready'"
                  @click="regenerateWithPrompt"
                >
                  保存并重新生成
                </button>
                <button v-if="isEditingPrompt" class="pill-btn ghost" @click="cancelPromptEdit">取消</button>
                <button
                  class="pill-btn"
                  :disabled="currentClip.status !== 'ready' || isRegeneratingImage"
                  @click="openImageFeedback"
                >
                  修改意见
                </button>
              </div>
            </div>
            <div v-else class="collapse-note">点击展开查看与编辑</div>
          </div>

          <div class="info-card">
            <div class="info-title">片段操作</div>
            <div class="action-row">
              <button class="pill-btn primary" @click="playCurrentClip">
                {{ isPlaying && (playMode === 'clip' || playMode === 'video') ? '暂停当前分镜' : '播放当前分镜' }}
              </button>
              <button class="pill-btn" @click="jumpToTimeline">定位到时间轴</button>
            </div>
          </div>

          <div class="info-card">
            <div class="info-title">视频片段</div>
            <div class="action-row">
              <button
                class="pill-btn primary"
                :disabled="currentClip.status !== 'ready' || isGeneratingVideo"
                @click="generateVideoForShot"
              >
                生成视频
              </button>
              <span class="video-status-note" :class="{ failed: currentVideoState.status === 'failed' }">
                {{ videoStatusLabel }}
              </span>
            </div>
          </div>

          <div v-if="currentClip && hasVideoForShot(currentClip.shotId)" class="info-card">
            <button class="collapse-header" @click="toggleVideoPrompt">
              <span>生视频提示词</span>
              <span class="collapse-hint">{{ isVideoPromptOpen ? '收起' : '展开' }}</span>
            </button>
            <div v-if="isVideoPromptOpen" class="collapse-body">
              <div v-if="!isEditingVideoPrompt" class="prompt-readonly" @click="isEditingVideoPrompt = true">
                {{ currentVideoState.prompt || '暂无提示词，点击编辑' }}
              </div>
              <textarea
                v-else
                v-model="videoPromptDraft"
                class="prompt-editor"
                rows="4"
                placeholder="编辑分镜视频提示词"
              ></textarea>
              <div class="action-row">
                <button
                  v-if="!isEditingVideoPrompt"
                  class="pill-btn"
                  @click="isEditingVideoPrompt = true"
                >
                  编辑提示词
                </button>
                <button
                  v-else
                  class="pill-btn primary"
                  :disabled="!videoPromptDraft.trim() || isGeneratingVideo"
                  @click="saveVideoPrompt"
                >
                  保存并重新生成
                </button>
                <button v-if="isEditingVideoPrompt" class="pill-btn ghost" @click="cancelVideoPromptEdit">
                  取消
                </button>
                <button class="pill-btn" :disabled="isGeneratingVideo" @click="openVideoFeedback">修改意见</button>
              </div>
            </div>
            <div v-else class="collapse-note">点击展开查看与编辑</div>
          </div>
        </div>
        <div v-else class="empty-panel">暂无分镜素材，请先生成素材包。</div>
      </div>

      <div class="drag-bar"><div class="rail"></div></div>

      <div class="editor-center">
        <div class="canvas-toolbar">
          <button class="pill-btn primary" @click="togglePlayAll" :disabled="clips.length === 0">
            {{ isPlaying && playMode === 'all' ? '暂停整片' : '播放整片' }}
          </button>
          <div class="time-pill">{{ formatTime(currentTimeSec) }} / {{ formatTime(totalDuration) }}</div>
        </div>
        <div class="canvas" :class="{ empty: !currentClip?.imageUrl && !hasReadyVideo }">
          <video
            v-if="hasReadyVideo"
            ref="videoRef"
            :src="currentVideoState.videoUrl"
            class="canvas-video"
            controls
            playsinline
            @ended="handleVideoEnded"
          ></video>
          <img v-else-if="currentClip?.imageUrl" :src="currentClip.imageUrl" alt="分镜画面" class="canvas-image" />
          <div v-else class="canvas-placeholder">待生成画面</div>
          <div class="canvas-overlay">
            <div class="overlay-title">镜头 {{ currentClip?.sequenceLabel || '-' }}</div>
            <div class="overlay-sub">{{ currentClip?.description || '暂无描述' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div ref="timelineRef" class="timeline-panel">
      <div class="timeline-header">
        <div class="view-switch">
          <button :class="['view-btn', { active: viewMode === 'timeline' }]" @click="viewMode = 'timeline'">
            时间轴视图
          </button>
          <button :class="['view-btn', { active: viewMode === 'story' }]" @click="viewMode = 'story'">
            故事面板
          </button>
        </div>
        <div class="timeline-actions">
          <span v-if="isGeneratingStoryboard" class="timeline-status">正在生成分镜画面…</span>
          <span v-else-if="storyboardError" class="timeline-error">{{ storyboardError }}</span>
          <button
            class="pill-btn"
            :disabled="clips.length === 0 || isGeneratingStoryboard"
            @click="forceRegenerateStoryboard"
          >
            强制重生成分镜
          </button>
          <button class="pill-btn" @click="togglePlayAll" :disabled="clips.length === 0">
            {{ isPlaying && playMode === 'all' ? '暂停' : '播放' }}
          </button>
          <span class="timeline-meta">总时长 {{ formatTime(totalDuration) }}</span>
        </div>
      </div>

      <div v-if="clips.length === 0" class="timeline-empty">暂无分镜片段</div>

      <div v-else-if="viewMode === 'timeline'" class="timeline-scroll">
        <div class="timeline-track">
          <div class="playhead" :style="{ left: playheadPercent + '%' }"></div>
          <div class="clip-row" :style="clipGridStyle">
            <button
              v-for="(clip, index) in clips"
              :key="clip.id"
              :class="['clip', { active: index === currentShotIndex }]"
              @click="selectShot(index)"
            >
              <div class="clip-thumb" :class="{ pending: clip.status !== 'ready' }">
                <img v-if="clip.imageUrl" :src="clip.imageUrl" alt="分镜缩略图" />
                <span v-else>待生成</span>
                <div class="clip-badge">{{ videoBadgeLabel(clip.shotId) }}</div>
              </div>
              <div class="clip-info">
                <div class="clip-title">{{ clip.sequenceLabel }}</div>
                <div class="clip-meta">{{ clip.durationSec }}s</div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <div v-else class="story-grid">
        <button
          v-for="(clip, index) in clips"
          :key="clip.id"
          :class="['story-card', { active: index === currentShotIndex }]"
          @click="selectShot(index)"
        >
          <div class="story-thumb" :class="{ pending: clip.status !== 'ready' }">
            <img v-if="clip.imageUrl" :src="clip.imageUrl" alt="分镜画面" />
            <span v-else>待生成</span>
            <div class="clip-badge">{{ videoBadgeLabel(clip.shotId) }}</div>
          </div>
          <div class="story-body">
          <div class="story-title">{{ clip.sequenceLabel }}</div>
            <div class="story-desc">{{ clip.description || '暂无描述' }}</div>
            <div class="story-meta">{{ clip.durationSec }}s</div>
          </div>
        </button>
      </div>
    </div>

    <div v-if="showImageFeedbackModal" class="modal-backdrop">
      <div class="modal-card">
        <div class="modal-title">修改分镜画面</div>
        <textarea
          v-model="feedbackDraft"
          class="prompt-editor"
          rows="4"
          placeholder="输入修改意见，重新生成分镜画面"
        ></textarea>
        <div class="modal-actions">
          <button class="pill-btn ghost" @click="closeImageFeedback">取消</button>
          <button
            class="pill-btn primary"
            :disabled="!feedbackDraft.trim() || isRegeneratingImage"
            @click="regenerateWithFeedback"
          >
            提交并重新生成
          </button>
        </div>
      </div>
    </div>

    <div v-if="showVideoFeedbackModal" class="modal-backdrop">
      <div class="modal-card">
        <div class="modal-title">修改分镜视频</div>
        <textarea
          v-model="videoFeedbackDraft"
          class="prompt-editor"
          rows="4"
          placeholder="输入意见，重新生成视频"
        ></textarea>
        <div class="modal-actions">
          <button class="pill-btn ghost" @click="closeVideoFeedback">取消</button>
          <button
            class="pill-btn primary"
            :disabled="!videoFeedbackDraft.trim() || isGeneratingVideo"
            @click="submitVideoFeedback"
          >
            提交并重新生成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import {
  fetchMaterialPackage,
  fetchMaterialPackages,
  fetchStoryboardVideoTask,
  generateStoryboardImages,
  generateStoryboardVideos,
  type MaterialPackage,
} from '@/api/material-packages';
import { adoptImage, regenerateImage, rewriteImagePrompt } from '@/api/images';
import { fetchProject } from '@/api/projects';

interface Clip {
  id: string;
  shotId: string;
  shotNumber: number;
  sequenceLabel: string;
  sceneBlock: number;
  sceneIndex: number;
  sceneId: string;
  sceneName: string;
  description: string;
  durationSec: number;
  camera: string;
  prompt: string;
  imageId: string;
  imageUrl: string;
  status: 'ready' | 'pending';
  type: 'image' | 'video';
}

const router = useRouter();

const projectName = ref('未命名创作');
const packageName = ref('');
const currentPackageId = ref<string | null>(null);
const clips = ref<Clip[]>([]);
const viewMode = ref<'timeline' | 'story'>('timeline');

const currentShotIndex = ref(0);
const currentTimeSec = ref(0);
const timelineRef = ref<HTMLElement | null>(null);

const currentClip = computed(() => clips.value[currentShotIndex.value] || null);
const isGeneratingStoryboard = ref(false);
const storyboardGenerationAttempted = ref(false);
const storyboardError = ref('');
const isEditingPrompt = ref(false);
const isImagePromptOpen = ref(false);
const isVideoPromptOpen = ref(false);
const promptDraft = ref('');
const feedbackDraft = ref('');
const isRegeneratingImage = ref(false);
const isGeneratingVideo = ref(false);
const isBulkGeneratingVideo = ref(false);
const showImageFeedbackModal = ref(false);
const showVideoFeedbackModal = ref(false);

type VideoStatus = 'none' | 'processing' | 'ready' | 'failed';
type VideoState = {
  status: VideoStatus;
  prompt: string;
  feedback: string;
  taskStatus?: string;
  videoId?: string;
  taskId?: string;
  videoUrl?: string;
  coverImageUrl?: string;
  provider?: string;
  size?: string;
};
const videoState = ref<Record<string, VideoState>>({});
const isEditingVideoPrompt = ref(false);
const videoPromptDraft = ref('');
const videoFeedbackDraft = ref('');

const clipStartTimes = computed(() => {
  const starts: number[] = [];
  let acc = 0;
  clips.value.forEach(clip => {
    starts.push(acc);
    acc += clip.durationSec;
  });
  return starts;
});

const totalDuration = computed(() => clips.value.reduce((sum, clip) => sum + clip.durationSec, 0));
const playheadPercent = computed(() => {
  if (!totalDuration.value) return 0;
  return Math.min(100, Math.max(0, (currentTimeSec.value / totalDuration.value) * 100));
});
const clipGridStyle = computed(() => {
  const count = clips.value.length;
  if (!count) return {};
  return { gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` };
});

const defaultVideoStateForClip = (clip?: Clip): VideoState => ({
  status: 'none',
  prompt: clip?.prompt || '',
  feedback: '',
});

const currentVideoState = computed(() => {
  if (!currentClip.value) {
    return defaultVideoStateForClip();
  }
  return videoState.value[currentClip.value.shotId] || defaultVideoStateForClip(currentClip.value);
});
const hasReadyVideo = computed(() => {
  const state = currentVideoState.value;
  return Boolean(state && state.status === 'ready' && state.videoUrl);
});

const isPlaying = ref(false);
const playMode = ref<'all' | 'clip' | 'video' | null>(null);
const playRange = ref<{ start: number; end: number; mode: 'all' | 'clip' } | null>(null);
let playTimer: number | null = null;
let videoPollTimer: number | null = null;
const videoRef = ref<HTMLVideoElement | null>(null);

const videoStatusLabel = computed(() => {
  if (!currentClip.value) return '';
  const state = videoState.value[currentClip.value.shotId];
  if (!state || state.status === 'none') return '未生成视频';
  if (state.status === 'failed') return '生成失败';
  if (state.status === 'processing') return '生成中…';
  return '已生成';
});

const formatTime = (seconds: number) => {
  if (!Number.isFinite(seconds)) return '00:00';
  const safe = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(safe / 60).toString().padStart(2, '0');
  const secs = (safe % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
};


const stopPlayback = () => {
  if (playTimer !== null) {
    window.clearInterval(playTimer);
    playTimer = null;
  }
  if (videoRef.value && !videoRef.value.paused) {
    videoRef.value.pause();
  }
  isPlaying.value = false;
  playMode.value = null;
  playRange.value = null;
};

const stopVideoPolling = () => {
  if (videoPollTimer !== null) {
    window.clearInterval(videoPollTimer);
    videoPollTimer = null;
  }
};

const pausePlayback = () => {
  if (playTimer !== null) {
    window.clearInterval(playTimer);
    playTimer = null;
  }
  if (playMode.value === 'video' && videoRef.value && !videoRef.value.paused) {
    videoRef.value.pause();
    playMode.value = null;
  }
  isPlaying.value = false;
};

const handleVideoEnded = () => {
  if (playMode.value === 'video') {
    isPlaying.value = false;
    playMode.value = null;
  }
};

const updateShotByTime = (time: number) => {
  if (!clips.value.length) return;
  const starts = clipStartTimes.value;
  for (let i = 0; i < starts.length; i += 1) {
    const end = starts[i] + clips.value[i].durationSec;
    if (time < end) {
      if (currentShotIndex.value !== i) {
        currentShotIndex.value = i;
      }
      return;
    }
  }
  currentShotIndex.value = clips.value.length - 1;
};

const startPlayback = (start: number, end: number, mode: 'all' | 'clip') => {
  if (!Number.isFinite(end) || end <= start) return;
  pausePlayback();
  playMode.value = mode;
  playRange.value = { start, end, mode };
  isPlaying.value = true;
  const origin = start;
  const startAt = performance.now();
  playTimer = window.setInterval(() => {
    const elapsed = (performance.now() - startAt) / 1000;
    const nextTime = Math.min(origin + elapsed, end);
    currentTimeSec.value = nextTime;
    updateShotByTime(nextTime);
    if (nextTime >= end) {
      stopPlayback();
    }
  }, 120);
};

const resumePlayback = () => {
  if (!playRange.value) return;
  startPlayback(currentTimeSec.value, playRange.value.end, playRange.value.mode);
};

const updateVideoStateFromTask = (shotId: string, task: Record<string, unknown>, video: Record<string, unknown>) => {
  const taskStatus = normalizeText(task?.task_status ?? video?.task_status, '');
  const videoUrl = normalizeText(video?.url ?? task?.video_url, '');
  const coverImageUrl = normalizeText(video?.cover_image_url ?? task?.cover_image_url, '');
  let status: VideoStatus = 'processing';
  if (taskStatus === 'SUCCESS' || videoUrl) {
    status = 'ready';
  } else if (taskStatus === 'FAIL') {
    status = 'failed';
  }
  const prev = videoState.value[shotId];
  videoState.value = {
    ...videoState.value,
    [shotId]: {
      status,
      prompt: prev?.prompt || '',
      feedback: prev?.feedback || '',
      taskStatus: taskStatus || undefined,
      videoId: normalizeText(video?.id, prev?.videoId || '') || prev?.videoId,
      taskId: normalizeText(task?.task_id ?? task?.id ?? video?.task_id ?? prev?.taskId, '') || prev?.taskId,
      videoUrl: videoUrl || prev?.videoUrl,
      coverImageUrl: coverImageUrl || prev?.coverImageUrl,
      provider: normalizeText(video?.provider, prev?.provider || '') || prev?.provider,
      size: normalizeText(video?.size, prev?.size || '') || prev?.size,
    },
  };
};

const pollVideoTasks = async () => {
  if (!currentPackageId.value) return;
  const entries = Object.entries(videoState.value).filter(
    ([, state]) => state?.status === 'processing' && state.taskId
  );
  if (!entries.length) {
    stopVideoPolling();
    return;
  }

  try {
    const results = await Promise.all(
      entries.map(([, state]) => fetchStoryboardVideoTask(currentPackageId.value as string, state.taskId as string))
    );
    results.forEach(result => {
      const video = (result.video || {}) as Record<string, unknown>;
      const shotId = normalizeText(video.shot_id ?? video.shotId, '');
      if (!shotId) return;
      updateVideoStateFromTask(shotId, result.task || {}, video);
    });
  } catch (err) {
    console.warn(err);
  }
};

const syncVideoPolling = () => {
  if (!currentPackageId.value) {
    stopVideoPolling();
    return;
  }
  const hasProcessing = Object.values(videoState.value).some(state => state?.status === 'processing' && state.taskId);
  if (hasProcessing && videoPollTimer === null) {
    pollVideoTasks();
    videoPollTimer = window.setInterval(pollVideoTasks, 5000);
  } else if (!hasProcessing) {
    stopVideoPolling();
  }
};

const togglePlayAll = () => {
  if (!clips.value.length) return;
  if (playMode.value === 'video') {
    stopPlayback();
  }
  if (playMode.value === 'all') {
    if (isPlaying.value) {
      pausePlayback();
      return;
    }
    resumePlayback();
    return;
  }
  startPlayback(0, totalDuration.value, 'all');
};

const playCurrentClip = () => {
  if (!currentClip.value) return;
  if (hasReadyVideo.value) {
    const video = videoRef.value;
    if (!video) return;
    if (playMode.value === 'video' && isPlaying.value) {
      video.pause();
      isPlaying.value = false;
      playMode.value = null;
      return;
    }
    stopPlayback();
    playMode.value = 'video';
    isPlaying.value = true;
    const playPromise = video.play();
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch(() => {
        isPlaying.value = false;
        playMode.value = null;
      });
    }
    return;
  }
  if (playMode.value === 'clip' && isPlaying.value) {
    pausePlayback();
    return;
  }
  const start = clipStartTimes.value[currentShotIndex.value] ?? 0;
  const end = start + currentClip.value.durationSec;
  startPlayback(start, end, 'clip');
};

const selectShot = (index: number) => {
  if (index < 0 || index >= clips.value.length) return;
  stopPlayback();
  currentShotIndex.value = index;
  currentTimeSec.value = clipStartTimes.value[index] ?? 0;
};

const jumpToTimeline = () => {
  timelineRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const toggleImagePrompt = () => {
  isImagePromptOpen.value = !isImagePromptOpen.value;
  if (!isImagePromptOpen.value) {
    cancelPromptEdit();
  }
};

const toggleVideoPrompt = () => {
  isVideoPromptOpen.value = !isVideoPromptOpen.value;
  if (!isVideoPromptOpen.value) {
    cancelVideoPromptEdit();
  }
};

const openImageFeedback = () => {
  if (!currentClip.value || currentClip.value.status !== 'ready') return;
  feedbackDraft.value = '';
  showImageFeedbackModal.value = true;
};

const closeImageFeedback = () => {
  showImageFeedbackModal.value = false;
  feedbackDraft.value = '';
};

const openVideoFeedback = () => {
  if (!currentClip.value || !hasVideoForShot(currentClip.value.shotId)) return;
  videoFeedbackDraft.value = '';
  showVideoFeedbackModal.value = true;
};

const closeVideoFeedback = () => {
  showVideoFeedbackModal.value = false;
  videoFeedbackDraft.value = '';
};

watch(
  () => currentClip.value,
  clip => {
    if (!clip) return;
    isEditingPrompt.value = false;
    isImagePromptOpen.value = false;
    promptDraft.value = clip.prompt || '';
    feedbackDraft.value = '';
    isEditingVideoPrompt.value = false;
    isVideoPromptOpen.value = false;
    const currentVideo = videoState.value[clip.shotId];
    videoPromptDraft.value = currentVideo?.prompt || clip.prompt || '';
    videoFeedbackDraft.value = '';
    showImageFeedbackModal.value = false;
    showVideoFeedbackModal.value = false;
  },
  { immediate: true }
);

watch(
  () => videoState.value,
  () => {
    syncVideoPolling();
  },
  { deep: true }
);

const normalizeText = (value: unknown, fallback = '') => {
  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }
  return fallback;
};

const normalizeDuration = (value: unknown, fallback = 5) => {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value;
  }
  return fallback;
};

const buildClipsFromPackage = (pkg: MaterialPackage) => {
  const materials = (pkg.materials || {}) as Record<string, any>;
  const metadata = materials.metadata || {};
  const blueprint = metadata.blueprint_v1 || {};
  const scenesRaw = Array.isArray(blueprint.scenes) ? blueprint.scenes : [];
  let storyboardRaw = Array.isArray(blueprint.storyboard) ? blueprint.storyboard : [];
  const imagesRaw = Array.isArray(metadata.images) ? metadata.images : [];

  const sceneNameById = new Map<string, string>();
  const scenePromptById = new Map<string, string>();
  scenesRaw.forEach((scene: any, index: number) => {
    const id = normalizeText(scene?.id, `scene_${index + 1}`);
    const name = normalizeText(scene?.name, `场景 ${index + 1}`);
    sceneNameById.set(id, name);
    scenePromptById.set(id, normalizeText(scene?.prompt_hint || scene?.prompt, ''));
  });

  if (!storyboardRaw.length && scenesRaw.length) {
    storyboardRaw = scenesRaw.map((scene: any, index: number) => ({
      id: normalizeText(scene?.id, `shot_${index + 1}`),
      shot_number: index + 1,
      scene_id: normalizeText(scene?.id, `scene_${index + 1}`),
      description: normalizeText(scene?.description, ''),
      duration_sec: 5,
      camera: '',
      prompt_hint: normalizeText(scene?.prompt_hint || scene?.prompt, ''),
    }));
  }

  const storyboardImageByShot = new Map<string, { id: string; url: string; prompt: string }>();
  imagesRaw.forEach((image: any) => {
    if (!image || typeof image !== 'object') return;
    if (image.type !== 'storyboard') return;
    const shotId = normalizeText(image.shot_id || image.shotId, '');
    const url = normalizeText(image.url, '');
    if (!shotId || !url) return;
    const isActive = image.is_active === true || image.isActive === true;
    if (isActive || !storyboardImageByShot.has(shotId)) {
      storyboardImageByShot.set(shotId, {
        id: normalizeText(image.id, ''),
        url,
        prompt: normalizeText(image.prompt, ''),
      });
    }
  });

  const clipList: Clip[] = storyboardRaw.map((shot: any, index: number) => {
    const shotNumber = typeof shot?.shot_number === 'number' ? shot.shot_number : index + 1;
    const shotId = normalizeText(shot?.id, `shot_${shotNumber}`);
    const sceneId = normalizeText(shot?.scene_id, '');
    const sceneName = sceneNameById.get(sceneId) || normalizeText(shot?.scene_name, '');
    const description = normalizeText(shot?.description, '');
    const camera = normalizeText(shot?.camera, '');
    const imageData = storyboardImageByShot.get(shotId);
    const prompt = normalizeText(
      imageData?.prompt,
      normalizeText(shot?.prompt_hint, scenePromptById.get(sceneId) || description)
    );
    const durationSec = normalizeDuration(shot?.duration_sec, 5);
    const imageUrl = imageData?.url || '';
    const imageId = imageData?.id || '';
    const status: Clip['status'] = imageUrl ? 'ready' : 'pending';

    return {
      id: shotId,
      shotId,
      shotNumber,
      sequenceLabel: '',
      sceneBlock: 0,
      sceneIndex: 0,
      sceneId,
      sceneName,
      description,
      durationSec,
      camera,
      prompt,
      imageId,
      imageUrl,
      status,
      type: 'image',
    };
  });

  let block = 0;
  let blockIndex = 0;
  let prevSceneKey = '';
  clipList.forEach(clip => {
    const sceneKey = clip.sceneId || clip.shotId;
    if (sceneKey !== prevSceneKey) {
      block += 1;
      blockIndex = 1;
      prevSceneKey = sceneKey;
    } else {
      blockIndex += 1;
    }
    clip.sceneBlock = block;
    clip.sceneIndex = blockIndex;
    clip.sequenceLabel = `${block}-${blockIndex}`;
  });

  return clipList;
};

const buildVideoStateFromPackage = (pkg: MaterialPackage, clipList: Clip[]) => {
  const materials = (pkg.materials || {}) as Record<string, any>;
  const metadata = materials.metadata || {};
  const videosRaw = Array.isArray(metadata.videos) ? metadata.videos : [];
  const videosByShot = new Map<string, any[]>();
  videosRaw.forEach((video: any) => {
    if (!video || typeof video !== 'object') return;
    if (video.type !== 'storyboard_video') return;
    const shotId = normalizeText(video.shot_id || video.shotId, '');
    if (!shotId) return;
    if (!videosByShot.has(shotId)) {
      videosByShot.set(shotId, []);
    }
    videosByShot.get(shotId)?.push(video);
  });

  const nextState: Record<string, VideoState> = {};
  clipList.forEach(clip => {
    const candidates = videosByShot.get(clip.shotId) || [];
    const active =
      candidates.find(item => item && item.is_active === true) ||
      candidates.find(item => item && item.task_status === 'SUCCESS') ||
      candidates[0];
    if (active && typeof active === 'object') {
      const taskStatus = normalizeText(active.task_status, '');
      const videoUrl = normalizeText(active.url || active.video_url, '');
      const coverImageUrl = normalizeText(active.cover_image_url || active.coverImageUrl, '');
      const status: VideoStatus = taskStatus
        ? taskStatus === 'SUCCESS'
          ? 'ready'
          : taskStatus === 'FAIL'
          ? 'failed'
          : 'processing'
        : videoUrl
        ? 'ready'
        : 'processing';
      nextState[clip.shotId] = {
        status,
        prompt: normalizeText(active.prompt, clip.prompt || ''),
        feedback: '',
        taskStatus: taskStatus || undefined,
        videoId: normalizeText(active.id, '') || undefined,
        taskId: normalizeText(active.task_id, '') || undefined,
        videoUrl: videoUrl || undefined,
        coverImageUrl: coverImageUrl || undefined,
        provider: normalizeText(active.provider, '') || undefined,
        size: normalizeText(active.size, '') || undefined,
      };
    } else {
      nextState[clip.shotId] = defaultVideoStateForClip(clip);
    }
  });
  videoState.value = nextState;
};

const hasMissingStoryboardImages = (pkg: MaterialPackage) => {
  const materials = (pkg.materials || {}) as Record<string, any>;
  const metadata = materials.metadata || {};
  const blueprint = metadata.blueprint_v1 || {};
  const storyboardRaw = Array.isArray(blueprint.storyboard) ? blueprint.storyboard : [];
  if (!storyboardRaw.length) return false;
  const imagesRaw = Array.isArray(metadata.images) ? metadata.images : [];
  const storyboardByShot = new Map<string, any>();
  imagesRaw.forEach((image: any) => {
    if (!image || typeof image !== 'object') return;
    if (image.type !== 'storyboard') return;
    const shotId = normalizeText(image.shot_id || image.shotId, '');
    if (!shotId) return;
    const isActive = image.is_active === true || image.isActive === true;
    if (isActive || !storyboardByShot.has(shotId)) {
      storyboardByShot.set(shotId, image);
    }
  });
  return storyboardRaw.some((shot: any) => {
    const shotId = normalizeText(shot?.id, '');
    if (!shotId) return false;
    const image = storyboardByShot.get(shotId);
    if (!image) return true;
    const promptSource = normalizeText(image.prompt_source || image.promptSource, '');
    const provider = normalizeText(image.provider, '');
    if (promptSource === 'demo_seed' || provider === 'demo') return true;
    return false;
  });
};

const refreshPackage = async (packageId: string, preserveShotId?: string) => {
  const refreshed = await fetchMaterialPackage(packageId);
  const nextClips = buildClipsFromPackage(refreshed);
  clips.value = nextClips;
  buildVideoStateFromPackage(refreshed, nextClips);
  const shotId = preserveShotId || currentClip.value?.shotId;
  if (shotId) {
    const nextIndex = clips.value.findIndex(item => item.shotId === shotId);
    if (nextIndex >= 0) {
      currentShotIndex.value = nextIndex;
      currentTimeSec.value = clipStartTimes.value[nextIndex] ?? 0;
    }
  }
};

const ensureStoryboardImages = async (pkg: MaterialPackage) => {
  if (storyboardGenerationAttempted.value || isGeneratingStoryboard.value) return;
  if (!hasMissingStoryboardImages(pkg)) return;
  storyboardGenerationAttempted.value = true;
  isGeneratingStoryboard.value = true;
  storyboardError.value = '';
  try {
    const result = await generateStoryboardImages(pkg.id);
    if (!result.generated || result.generated.length === 0) {
      storyboardError.value = '分镜图生成失败，可能素材图不可访问或模型返回为空';
    }
    await refreshPackage(pkg.id);
  } catch (err) {
    storyboardError.value = err instanceof Error ? err.message : '分镜图生成失败，请稍后重试';
  } finally {
    isGeneratingStoryboard.value = false;
  }
};

const forceRegenerateStoryboard = async () => {
  if (!currentPackageId.value) return;
  isGeneratingStoryboard.value = true;
  storyboardError.value = '';
  try {
    const result = await generateStoryboardImages(currentPackageId.value, true);
    if (!result.generated || result.generated.length === 0) {
      storyboardError.value = '分镜图生成失败，可能素材图不可访问或模型返回为空';
    }
    await refreshPackage(currentPackageId.value);
  } catch (err) {
    storyboardError.value = err instanceof Error ? err.message : '分镜图生成失败，请稍后重试';
  } finally {
    isGeneratingStoryboard.value = false;
  }
};

const startPromptEdit = () => {
  if (!currentClip.value) return;
  if (currentClip.value.status !== 'ready') return;
  isEditingPrompt.value = true;
  isImagePromptOpen.value = true;
  promptDraft.value = currentClip.value.prompt || '';
};

const cancelPromptEdit = () => {
  if (!currentClip.value) return;
  isEditingPrompt.value = false;
  promptDraft.value = currentClip.value.prompt || '';
};

const regenerateWithPrompt = async () => {
  if (!currentClip.value || !currentPackageId.value) return;
  if (!currentClip.value.imageId) return;
  const prompt = promptDraft.value.trim();
  if (!prompt) return;
  isRegeneratingImage.value = true;
  try {
    const result = await regenerateImage(currentClip.value.imageId, prompt, 'user_edit');
    if (result?.image?.id) {
      await adoptImage(result.image.id);
    }
    await refreshPackage(currentPackageId.value, currentClip.value.shotId);
    isEditingPrompt.value = false;
  } catch (err) {
    alert(err instanceof Error ? err.message : '分镜画面生成失败');
  } finally {
    isRegeneratingImage.value = false;
  }
};

const regenerateWithFeedback = async () => {
  if (!currentClip.value || !currentPackageId.value) return;
  if (!currentClip.value.imageId) return;
  const feedback = feedbackDraft.value.trim();
  if (!feedback) return;
  isRegeneratingImage.value = true;
  try {
    const rewritten = await rewriteImagePrompt(currentClip.value.imageId, feedback);
    const result = await regenerateImage(currentClip.value.imageId, rewritten.rewritten_prompt, 'user_feedback');
    if (result?.image?.id) {
      await adoptImage(result.image.id);
    }
    await refreshPackage(currentPackageId.value, currentClip.value.shotId);
    closeImageFeedback();
  } catch (err) {
    alert(err instanceof Error ? err.message : '分镜画面生成失败');
  } finally {
    isRegeneratingImage.value = false;
  }
};

const generateVideoForShot = async () => {
  if (!currentClip.value || !currentPackageId.value) return;
  const prompt = videoPromptDraft.value.trim() || currentClip.value.prompt || '';
  if (!prompt) return;
  isGeneratingVideo.value = true;
  try {
    await generateStoryboardVideos(currentPackageId.value, {
      shot_id: currentClip.value.shotId,
      prompt,
    });
    await refreshPackage(currentPackageId.value, currentClip.value.shotId);
    isVideoPromptOpen.value = false;
    isEditingVideoPrompt.value = false;
    showVideoFeedbackModal.value = false;
  } catch (err) {
    alert(err instanceof Error ? err.message : '分镜视频生成失败');
  } finally {
    isGeneratingVideo.value = false;
  }
};

const saveVideoPrompt = async () => {
  if (!currentClip.value || !currentPackageId.value) return;
  const prompt = videoPromptDraft.value.trim();
  if (!prompt) return;
  isGeneratingVideo.value = true;
  try {
    await generateStoryboardVideos(currentPackageId.value, {
      shot_id: currentClip.value.shotId,
      prompt,
      force: true,
    });
    await refreshPackage(currentPackageId.value, currentClip.value.shotId);
    isEditingVideoPrompt.value = false;
  } catch (err) {
    alert(err instanceof Error ? err.message : '分镜视频生成失败');
  } finally {
    isGeneratingVideo.value = false;
  }
};

const cancelVideoPromptEdit = () => {
  if (!currentClip.value) return;
  const state = currentVideoState.value;
  videoPromptDraft.value = state.prompt || currentClip.value.prompt || '';
  isEditingVideoPrompt.value = false;
};

const submitVideoFeedback = async () => {
  if (!currentClip.value || !currentPackageId.value) return;
  const feedback = videoFeedbackDraft.value.trim();
  if (!feedback) return;
  isGeneratingVideo.value = true;
  try {
    await generateStoryboardVideos(currentPackageId.value, {
      shot_id: currentClip.value.shotId,
      feedback,
      force: true,
    });
    await refreshPackage(currentPackageId.value, currentClip.value.shotId);
    closeVideoFeedback();
  } catch (err) {
    alert(err instanceof Error ? err.message : '分镜视频生成失败');
  } finally {
    isGeneratingVideo.value = false;
  }
};

const hasVideoForShot = (shotId: string) => {
  const state = videoState.value[shotId];
  return Boolean(state && state.status !== 'none');
};

const videoBadgeLabel = (shotId: string) => {
  const state = videoState.value[shotId];
  if (!state || state.status === 'none') return '图片';
  if (state.status === 'failed') return '失败';
  if (state.status === 'processing') return '视频中';
  return '视频';
};

const generateAllVideos = async () => {
  if (!currentPackageId.value || !clips.value.length) return;
  isBulkGeneratingVideo.value = true;
  try {
    await generateStoryboardVideos(currentPackageId.value, {});
    await refreshPackage(currentPackageId.value);
  } catch (err) {
    alert(err instanceof Error ? err.message : '批量生成视频失败');
  } finally {
    isBulkGeneratingVideo.value = false;
  }
};

const loadEditorData = async () => {
  const storedProjectId = sessionStorage.getItem('currentProjectId');
  if (!storedProjectId) {
    router.push('/space');
    return;
  }

  try {
    const project = await fetchProject(storedProjectId);
    projectName.value = project.name || '未命名创作';
    sessionStorage.setItem('currentProjectName', projectName.value);
  } catch (err) {
    projectName.value = sessionStorage.getItem('currentProjectName') || '未命名创作';
  }

  try {
    const data = await fetchMaterialPackages(storedProjectId);
    const list = data.list || [];
    const active = list.find(item => (item as any).is_active) || list.find(item => item.status === 'completed') || list[0];
    if (!active) {
      clips.value = [];
      packageName.value = '';
      currentPackageId.value = null;
      videoState.value = {};
      storyboardError.value = '';
      stopPlayback();
      return;
    }
    currentPackageId.value = active.id;
    packageName.value = active.package_name || '素材包';
    const nextClips = buildClipsFromPackage(active);
    clips.value = nextClips;
    buildVideoStateFromPackage(active, nextClips);
    await ensureStoryboardImages(active);
    stopPlayback();
    currentShotIndex.value = 0;
    currentTimeSec.value = 0;
  } catch (err) {
    clips.value = [];
    storyboardError.value = err instanceof Error ? err.message : '素材包加载失败';
    videoState.value = {};
  }
};

const goBack = () => {
  router.push('/materials');
};

onMounted(() => {
  loadEditorData();
});

onUnmounted(() => {
  stopPlayback();
  stopVideoPolling();
});
</script>

<style scoped>
.editor-page {
  min-height: calc(100vh - 56px);
  background: var(--md-surface);
  color: var(--md-on-surface);
  padding-bottom: 16px;
}

.top-ops {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  margin-bottom: 12px;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-name {
  font-size: 16px;
  font-weight: 700;
}

.package-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.package-name {
  font-size: 12px;
  color: var(--md-on-surface);
}

.tag {
  padding: 4px 8px;
  border-radius: 10px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
}

.floating-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 9999px;
  padding: 8px 12px;
}

.pill-btn {
  padding: 8px 14px;
  border-radius: 9999px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn:hover {
  border-color: rgba(121, 116, 126, 0.35);
  background: rgba(103, 80, 164, 0.1);
}

.pill-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pill-btn.primary {
  background: var(--md-primary);
  color: var(--md-on-primary);
  font-weight: 700;
}

.pill-btn.ghost {
  background: transparent;
  border-color: rgba(121, 116, 126, 0.2);
}

.editor-layout {
  display: grid;
  grid-template-columns: 340px 8px 1fr;
  gap: 12px;
  min-height: 420px;
  height: calc(100vh - 320px);
}

.editor-left {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 12px;
  overflow-y: auto;
}

.shot-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-title {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.shot-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shot-title {
  font-size: 16px;
  font-weight: 700;
}

.shot-sub {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.shot-status {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-on-surface);
  width: fit-content;
}

.shot-status.pending {
  background: rgba(251, 146, 60, 0.15);
  color: #fbbf24;
}

.info-card {
  border-radius: 12px;
  padding: 12px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
}

.collapse-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent;
  border: none;
  color: var(--md-on-surface);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.collapse-hint {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.collapse-body {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.collapse-note {
  margin-top: 8px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.info-title {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
  color: var(--md-on-surface);
}

.info-row .label {
  color: var(--md-on-surface-variant);
}

.info-text {
  font-size: 12px;
  color: var(--md-on-surface);
  line-height: 1.5;
  margin: 0;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.prompt-readonly {
  font-size: 12px;
  color: var(--md-on-surface);
  background: rgba(121, 116, 126, 0.12);
  border-radius: 10px;
  padding: 10px;
  line-height: 1.5;
  cursor: pointer;
  white-space: pre-wrap;
}

.prompt-editor {
  width: 100%;
  border-radius: 10px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface);
  color: var(--md-on-surface);
  padding: 8px;
  resize: vertical;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  padding: 20px;
}

.modal-card {
  width: min(420px, 90vw);
  background: var(--md-surface-container);
  border-radius: 16px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-title {
  font-size: 14px;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.empty-panel {
  color: var(--md-on-surface-variant);
  font-size: 13px;
  padding: 16px;
}

.editor-center {
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}

.drag-bar {
  width: 8px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drag-bar .rail {
  width: 2px;
  height: 52px;
  background: rgba(121, 116, 126, 0.4);
  border-radius: 10px;
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  justify-content: space-between;
}

.time-pill {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.canvas {
  width: min(360px, 90%);
  aspect-ratio: 3 / 4;
  background: linear-gradient(180deg, #3b3b3b, #222);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
}

.canvas.empty {
  background: #1b1b1f;
}

.canvas-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.canvas-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #000;
}

.canvas-placeholder {
  font-size: 14px;
  color: var(--md-on-surface-variant);
}

.canvas-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.65));
  color: #fff;
}

.overlay-title {
  font-size: 13px;
  font-weight: 600;
}

.overlay-sub {
  font-size: 12px;
  opacity: 0.85;
}

.timeline-panel {
  margin-top: 16px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 12px;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.view-switch {
  display: flex;
  gap: 8px;
}

.view-btn {
  padding: 6px 12px;
  border-radius: 9999px;
  border: 1px solid rgba(121, 116, 126, 0.3);
  background: var(--md-surface-container);
  color: var(--md-on-surface);
  cursor: pointer;
  font-size: 12px;
}

.view-btn.active {
  background: var(--md-primary);
  color: var(--md-on-primary);
  border-color: transparent;
}

.timeline-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-status-note {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.video-status-note.failed {
  color: #d65b5b;
}

.timeline-status {
  font-size: 11px;
  color: #fbbf24;
  background: rgba(251, 146, 60, 0.15);
  padding: 4px 8px;
  border-radius: 9999px;
  border: 1px solid rgba(251, 146, 60, 0.35);
}

.timeline-error {
  font-size: 11px;
  color: #f87171;
  background: rgba(248, 113, 113, 0.15);
  padding: 4px 8px;
  border-radius: 9999px;
  border: 1px solid rgba(248, 113, 113, 0.35);
}

.timeline-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.timeline-empty {
  padding: 20px;
  font-size: 13px;
  color: var(--md-on-surface-variant);
}

.timeline-scroll {
  overflow-x: auto;
  padding-bottom: 6px;
}

.timeline-track {
  position: relative;
  min-height: 120px;
  width: 100%;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #6cf9e0;
  box-shadow: 0 0 6px rgba(108, 249, 224, 0.7);
  pointer-events: none;
}

.clip-row {
  display: grid;
  gap: 10px;
  align-items: stretch;
  width: 100%;
}

.clip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: 12px;
  padding: 6px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container);
  cursor: pointer;
  position: relative;
  width: 100%;
}

.clip.active {
  border-color: rgba(108, 249, 224, 0.6);
  box-shadow: 0 0 0 2px rgba(108, 249, 224, 0.2);
}

.clip-thumb,
.story-thumb {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.story-thumb {
  height: 120px;
}

.clip-thumb.pending,
.story-thumb.pending {
  background: rgba(251, 146, 60, 0.12);
  color: #fbbf24;
}

.clip-thumb img,
.story-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.clip-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 9999px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
}

.clip-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.clip-title {
  font-size: 12px;
  color: var(--md-on-surface);
}

.clip-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.story-card {
  border-radius: 14px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  text-align: left;
}

.story-card.active {
  border-color: rgba(108, 249, 224, 0.6);
  box-shadow: 0 0 0 2px rgba(108, 249, 224, 0.2);
}

.story-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.story-title {
  font-size: 13px;
  font-weight: 600;
}

.story-desc {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  line-height: 1.4;
}

.story-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

@media (max-width: 960px) {
  .editor-layout {
    grid-template-columns: 1fr;
    height: auto;
  }

  .drag-bar {
    display: none;
  }

  .editor-center {
    min-height: 360px;
  }
}
</style>
