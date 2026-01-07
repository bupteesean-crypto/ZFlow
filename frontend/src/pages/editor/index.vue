<template>
  <div class="editor-page">
    <!-- Top Operations Bar -->
    <div class="top-ops">
      <div class="flex items-center gap-3">
        <div class="sub-nav">
          <span class="text-xs text-slate-400">分栏：</span>
          <button
            v-for="tab in subTabs"
            :key="tab.id"
            :class="['nav-link-sm', { active: activeSubTab === tab.id }]"
            @click="activeSubTab = tab.id"
          >
            {{ tab.icon }}
          </button>
        </div>
        <span class="text-sm text-slate-200 font-semibold">{{ projectName }}</span>
      </div>
      <div class="floating-ops">
        <button class="pill-btn ghost" @click="goBack">← 返回素材</button>
        <button class="pill-btn primary" @click="handleGenerateAll">一键生成视频</button>
        <button class="pill-btn" @click="handleExport">导出</button>
      </div>
    </div>

    <!-- Editor Layout -->
    <div class="editor-layout">
      <!-- Left Panel -->
      <div class="editor-left">
        <!-- Visual Panel -->
        <div v-show="activeSubTab === 'visual'" class="sub-panel active">
          <div class="visual-header">
            <span class="tag">🎬 分镜 {{ currentShotIndex + 1 }}</span>
            <span class="text-xs text-slate-400">当前所有画面生成都作用于该分镜</span>
          </div>
          <div class="divider"></div>
          <div class="visual-stream">
            <!-- Image Card -->
            <div class="ai-card">
              <div class="card-header">
                <div class="card-title">
                  <span>🖼️</span>
                  <span>图片提示词</span>
                </div>
              </div>
              <div class="img-preview" @click="updateCanvas('image', currentShot.img)">
                <img :src="currentShot?.img" alt="分镜图" />
                <div class="prompt-overlay">
                  <div class="overlay-text">生成依据（AI）：{{ currentShot?.prompt || 'AI 生成的画面描述' }}</div>
                  <div class="overlay-actions">
                    <button class="btn-edit-prompt">✏️ 修改生成描述</button>
                  </div>
                </div>
              </div>
              <div class="card-footer">
                <div class="cta-hint">下一步：基于该画面生成视频</div>
                <div class="cta-row">
                  <button class="btn-video primary" @click="generateVideo(currentShotIndex)">生成视频</button>
                </div>
              </div>
            </div>

            <!-- Video Card (if generated) -->
            <div v-if="currentShot?.hasVideo" class="ai-card video-card">
              <div class="card-header">
                <div class="card-title">
                  <span>🎞️</span>
                  <span>视频提示词</span>
                </div>
              </div>
              <div class="video-preview" @click="updateCanvas('video', currentShot.videoUrl)">
                <span class="video-badge">智能选择</span>
                <img :src="currentShot?.img" alt="视频封面" />
              </div>
            </div>
          </div>
        </div>

        <!-- Voice Panel -->
        <div v-show="activeSubTab === 'voice'" class="sub-panel">
          <div class="e-card">
            <h4>分镜 {{ currentShotIndex + 1 }}</h4>
            <div class="divider"></div>
            <h4>旁白台词</h4>
            <textarea class="editor-textarea" rows="4" placeholder="结合我们的素材包生成一个。">{{ currentShot?.narration || '' }}</textarea>
            <div class="inline-actions">
              <div class="flex gap-2">
                <button class="pill-ghost">▶︎ 试听</button>
                <button class="pill-ghost">⏸ 停顿</button>
              </div>
              <span class="text-xs text-slate-400">约 5s 音频</span>
            </div>
          </div>
          <div class="e-card">
            <h4>声音音色</h4>
            <div class="voice-card">
              <div class="meta">
                <div class="icon">▶</div>
                <div class="info">
                  <span class="font-semibold">温柔学姐</span>
                  <span class="tags">女性 / 青年 / 普通话</span>
                </div>
              </div>
              <button class="swap">⇄ 切换</button>
            </div>
          </div>
          <div class="e-card">
            <h4>声音音量</h4>
            <div class="form-row inline">
              <input class="form-control" type="range" min="0" max="100" value="100" />
              <span class="text-xs text-slate-300 w-10 text-right">100</span>
            </div>
          </div>
          <button class="cta-apply">应用修改</button>
        </div>

        <!-- Music Panel -->
        <div v-show="activeSubTab === 'music'" class="sub-panel">
          <div class="e-card">
            <h4>分镜 {{ currentShotIndex + 1 }}</h4>
            <div class="divider"></div>
            <div class="segmented mb-2">
              <button class="active" @click="musicMode = 'ai'">AI生成</button>
              <button @click="musicMode = 'lib'">音乐库</button>
            </div>
            <div v-if="musicMode === 'ai'">
              <textarea class="editor-textarea" rows="3" placeholder="描述你想要生成的音乐"></textarea>
              <div class="inline-actions">
                <span class="text-xs text-slate-400 flex items-center gap-1">✨ 3</span>
                <button class="pill-ghost">发送/生成</button>
              </div>
              <div class="music-card mt-2">
                <div class="music-cover"></div>
                <div class="music-body">
                  <p class="music-title">AI 生成音乐 01</p>
                  <div class="music-progress"></div>
                  <div class="music-time">00:00 / 02:44</div>
                </div>
              </div>
            </div>
          </div>
          <div class="e-card">
            <h4>声音音量</h4>
            <div class="form-row inline">
              <input class="form-control" type="range" min="0" max="100" value="35" />
              <span class="text-xs text-slate-300 w-10 text-right">35</span>
            </div>
          </div>
          <button class="cta-apply">应用</button>
        </div>
      </div>

      <div class="drag-bar"><div class="rail"></div></div>

      <!-- Center Canvas -->
      <div class="editor-center">
        <div class="canvas-wrap">
          <div class="canvas">
            <video
              v-if="canvasMedia.type === 'video' && canvasMedia.src"
              :src="canvasMedia.src"
              :poster="canvasMedia.poster"
              controls
              class="canvas-video"
            ></video>
            <img
              v-else
              :src="canvasMedia.poster || currentShot?.img"
              alt="预览"
              class="canvas-image"
            />
            <div class="subtitle">{{ currentShot?.title || '' }}</div>
          </div>
          <div class="thumb-stack">
            <div class="mini">
              <img :src="currentShot?.img" alt="当前分镜" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Timeline -->
    <div class="timeline mt-4">
      <button class="pill-btn">▶︎</button>
      <span class="text-sm text-slate-300 ml-2 mr-4">00:00 / 00:35</span>
      <div
        v-for="(shot, index) in shots"
        :key="index"
        :class="['clip', { active: index === currentShotIndex }]"
        @click="selectShot(index)"
      >
        <img :src="shot.img" alt="" />
        <span>分镜{{ index + 1 }}</span>
        <span v-if="shot.hasVideo" class="video-flag">视频</span>
      </div>
    </div>
    <div class="audio-tracks">
      <div class="audio-row">
        <div class="label">🎵 背景音乐</div>
        <audio controls preload="metadata" class="audio-control"></audio>
      </div>
      <div class="audio-row">
        <div class="label">🗣️ 旁白</div>
        <audio controls preload="metadata" class="audio-control"></audio>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

interface Shot {
  name: string;
  img: string;
  videoUrl?: string;
  hasVideo: boolean;
  prompt?: string;
  narration?: string;
  title: string;
}

const subTabs = [
  { id: 'visual', icon: '▣', label: '画面' },
  { id: 'voice', icon: '♫', label: '配音' },
  { id: 'music', icon: '♪', label: '音乐' },
];

const activeSubTab = ref('visual');
const currentShotIndex = ref(0);
const musicMode = ref<'ai' | 'lib'>('ai');
const projectName = ref(sessionStorage.getItem('currentProjectName') || '北京都市奇遇记');
const canvasMedia = ref<{ type: 'image' | 'video'; src?: string; poster?: string }>({
  type: 'image',
  poster: '',
});

// Demo shots data
const shots = ref<Shot[]>([
  { name: '分镜 1', img: '/images/shot-01.png', hasVideo: false, title: '夜幕降临 · 城市航拍', prompt: '航拍视角，城市夜景' },
  { name: '分镜 2', img: '/images/shot-02.png', hasVideo: false, title: '街角相遇', prompt: '街角场景，角色出现' },
  { name: '分镜 3', img: '/images/shot-03.png', hasVideo: false, title: '餐厅对话', prompt: '餐厅内部，温暖灯光' },
  { name: '分镜 4', img: '/images/shot-04.png', hasVideo: false, title: '漫步街道', prompt: '街道漫步，霓虹灯光' },
  { name: '分镜 5', img: '/images/shot-05.png', hasVideo: false, title: '告别时刻', prompt: '告别场景，温柔氛围' },
]);

const currentShot = computed(() => shots.value[currentShotIndex.value]);

const selectShot = (index: number) => {
  currentShotIndex.value = index;
  updateCanvas('image', shots.value[index].img);
};

const updateCanvas = (type: 'image' | 'video', src: string) => {
  canvasMedia.value = {
    type,
    src: type === 'video' ? src : undefined,
    poster: type === 'video' ? shots.value[currentShotIndex.value].img : src,
  };
};

const generateVideo = (index: number) => {
  const shot = shots.value[index];
  if (shot) {
    shot.hasVideo = true;
    shot.videoUrl = `/videos/shot-${index}.mp4`;
    alert(`正在生成分镜 ${index + 1} 的视频...`);
  }
};

const handleGenerateAll = () => {
  shots.value.forEach((shot, index) => {
    setTimeout(() => {
      shot.hasVideo = true;
      shot.videoUrl = `/videos/shot-${index}.mp4`;
    }, index * 500);
  });
  alert('正在生成所有分镜的视频...');
};

const handleExport = () => {
  const path = prompt('请选择保存位置（示例：/Users/you/Movies/output.mp4）');
  if (path) {
    alert(`已保存至：${path}（Demo 提示）`);
  }
};

const goBack = () => {
  router.push('/materials');
};
</script>

<style scoped>
.editor-page {
  min-height: calc(100vh - 56px);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.top-ops {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  margin-bottom: 12px;
}

.sub-nav {
  display: flex;
  gap: 10px;
  align-items: center;
}

.nav-link-sm {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-link-sm:hover {
  border-color: rgba(121, 116, 126, 0.35);
  background: rgba(103, 80, 164, 0.08);
}

.nav-link-sm.active {
  border-color: rgba(103, 80, 164, 0.5);
  background: rgba(103, 80, 164, 0.15);
  color: var(--md-on-surface);
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

.pill-btn.primary {
  background: var(--md-primary);
  color: var(--md-on-primary);
  font-weight: 700;
}

.pill-btn.ghost {
  background: transparent;
  border-color: rgba(121, 116, 126, 0.2);
}

/* Editor Layout */
.editor-layout {
  display: grid;
  grid-template-columns: 340px 8px 1fr;
  gap: 12px;
  height: calc(100vh - 300px);
}

.editor-left {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 12px;
  overflow-y: auto;
}

.editor-center {
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.sub-panel {
  display: none;
}

.sub-panel.active {
  display: block;
}

.visual-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #e5e7eb;
  margin-bottom: 8px;
}

.tag {
  padding: 4px 8px;
  border-radius: 10px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
}

.divider {
  border-bottom: 1px solid rgba(121, 116, 126, 0.2);
  margin-bottom: 12px;
}

.visual-stream {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-card {
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--md-on-surface);
}

.img-preview,
.video-preview {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(121, 116, 126, 0.25);
  margin-bottom: 10px;
  cursor: pointer;
}

.img-preview img,
.video-preview img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
}

.prompt-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(103, 80, 164, 0.05), rgba(28, 27, 31, 0.35));
  color: var(--md-on-surface);
  opacity: 0;
  transition: opacity 0.2s ease;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 12px;
  gap: 8px;
}

.img-preview:hover .prompt-overlay,
.video-preview:hover .prompt-overlay {
  opacity: 1;
}

.overlay-text {
  font-size: 12px;
  color: var(--md-on-surface);
  background: rgba(103, 80, 164, 0.12);
  padding: 8px;
  border-radius: 10px;
}

.overlay-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-edit-prompt {
  background: #fff;
  color: #000;
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
}

.video-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(108, 249, 224, 0.2);
  color: #c8fff1;
  padding: 4px 8px;
  border-radius: 10px;
  font-size: 11px;
  border: 1px solid rgba(108, 249, 224, 0.4);
}

.card-footer {
  display: flex;
  gap: 10px;
  flex-direction: column;
}

.cta-hint {
  font-size: 11px;
  color: #9aa8c7;
}

.cta-row {
  display: flex;
  gap: 10px;
}

.btn-video {
  flex: 1;
  border-radius: 9999px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: #e5e7eb;
  cursor: pointer;
  font-weight: 600;
}

.btn-video.primary {
  background: #fff;
  color: #000;
}

/* Editor Cards */
.e-card {
  background: #1a1a1e;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 14px;
  font-size: 13px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.e-card h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #cbd5ff;
}

.editor-textarea {
  width: 100%;
  background: #0f1013;
  border: 1px solid #2a2a2e;
  color: #eee;
  border-radius: 10px;
  padding: 8px;
  resize: vertical;
}

.inline-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}

.pill-ghost {
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: #e5e7eb;
  font-size: 12px;
  cursor: pointer;
}

.voice-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.voice-card .meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.voice-card .meta .icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(108, 249, 224, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9cfbe6;
}

.voice-card .meta .info {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #e5e7eb;
}

.voice-card .meta .info .tags {
  color: #9aa8c7;
  font-size: 11px;
}

.voice-card .swap {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: #e5e7eb;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row.inline {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.form-control {
  flex: 1;
}

.cta-apply {
  width: 100%;
  padding: 12px 14px;
  border-radius: 9999px;
  background: #fff;
  color: #000;
  font-weight: 700;
  border: none;
  cursor: pointer;
}

.segmented {
  display: flex;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  overflow: hidden;
}

.segmented button {
  flex: 1;
  padding: 10px;
  background: rgba(255, 255, 255, 0.04);
  color: #e5e7eb;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.segmented button.active {
  background: #fff;
  color: #000;
  font-weight: 700;
}

.music-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
}

.music-cover {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: linear-gradient(135deg, #334155, #0ea5e9);
  flex-shrink: 0;
}

.music-body {
  flex: 1;
}

.music-title {
  font-size: 13px;
  color: #e5e7eb;
  margin: 0;
}

.music-progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 9999px;
  margin-top: 6px;
}

.music-progress::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, #6cf9e0, #7c5dff);
  border-radius: 9999px;
}

.music-time {
  font-size: 11px;
  color: #9aa8c7;
}

/* Canvas */
.canvas-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
  padding-right: 120px;
}

.canvas {
  width: 300px;
  height: 480px;
  background: linear-gradient(180deg, #3b3b3b, #222);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
}

.canvas-video,
.canvas-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 24px;
}

.subtitle {
  position: absolute;
  bottom: 18px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 13px;
  color: #e6e6e6;
}

.thumb-stack {
  position: absolute;
  right: -90px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.mini {
  width: 70px;
  height: 70px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.mini img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Timeline */
.timeline {
  height: 96px;
  background: #121214;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 10px 14px;
  overflow-x: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.clip {
  min-width: 120px;
  height: 72px;
  background: #1f1f22;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #aaa;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  position: relative;
  cursor: pointer;
}

.clip img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  inset: 0;
}

.clip span {
  position: absolute;
  left: 8px;
  bottom: 6px;
  font-size: 11px;
  background: rgba(0, 0, 0, 0.45);
  padding: 2px 6px;
  border-radius: 6px;
  color: #fff;
}

.clip.active {
  border-color: rgba(108, 249, 224, 0.5);
  box-shadow: 0 0 0 2px rgba(108, 249, 224, 0.25);
}

.video-flag {
  position: absolute;
  right: 8px;
  top: 6px;
  font-size: 10px;
  background: rgba(108, 249, 224, 0.18);
  color: #c8fff1;
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid rgba(108, 249, 224, 0.35);
}

.audio-tracks {
  margin-top: 10px;
  background: #0e0f12;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audio-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.audio-row .label {
  width: 100px;
  font-size: 12px;
  color: #cbd5ff;
}

.audio-control {
  flex: 1;
  height: 28px;
}

/* Utilities */
.flex { display: flex; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-slate-200 { color: var(--md-on-surface); }
.text-slate-300 { color: var(--md-on-surface-variant); }
.text-slate-400 { color: var(--md-on-surface-variant); }
.font-semibold { font-weight: 600; }
.w-10 { width: 40px; }
.w-full { width: 100%; }
.text-right { text-align: right; }
.ml-2 { margin-left: 8px; }
.mr-4 { margin-right: 16px; }
.mb-1 { margin-bottom: 4px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
.mb-12 { margin-bottom: 48px; }
.mb-14 { margin-bottom: 56px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
.mt-8 { margin-top: 32px; }
</style>
