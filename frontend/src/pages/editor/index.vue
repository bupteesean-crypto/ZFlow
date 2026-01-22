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
          :disabled="clips.length === 0 || isExporting"
          @click="openExportModal"
        >
          导出
        </button>
        <button class="pill-btn ghost" @click="goBack">← 返回素材</button>
      </div>
    </div>

    <div class="editor-layout">
      <div class="editor-left">
        <div class="panel-tabs">
          <button :class="['tab-btn', { active: leftTab === 'visual' }]" @click="leftTab = 'visual'">画面</button>
          <button :class="['tab-btn', { active: leftTab === 'voice' }]" @click="leftTab = 'voice'">配音</button>
          <button :class="['tab-btn', { active: leftTab === 'music' }]" @click="leftTab = 'music'">音乐</button>
        </div>
        <div v-if="currentClip" class="shot-panel">
          <template v-if="leftTab === 'visual'">
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
                <div class="field-row">
                  <span class="label">图片模型</span>
                  <select v-model="selectedImageModelId" class="model-select" :disabled="isRegeneratingImage">
                    <option v-for="model in imageModels" :key="model.id" :value="model.id" :disabled="!model.enabled">
                      {{ model.label }}{{ model.enabled ? '' : '（未启用）' }}
                    </option>
                  </select>
                </div>
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
              <div class="field-row">
                <span class="label">视频模型</span>
                <select v-model="selectedVideoModelId" class="model-select" :disabled="isGeneratingVideo">
                  <option v-for="model in videoModels" :key="model.id" :value="model.id" :disabled="!model.enabled">
                    {{ model.label }}{{ model.enabled ? '' : '（未启用）' }}
                  </option>
                </select>
              </div>
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
          </template>

          <template v-else-if="leftTab === 'voice'">
            <div class="panel-title">配音设置</div>
            <div class="info-card">
              <div class="info-title">旁白台词</div>
              <textarea
                v-model="narrationText"
                class="prompt-editor"
                rows="4"
                :maxlength="narrationLimit"
                placeholder="输入需要配音的旁白内容"
              ></textarea>
              <div class="row-between">
                <span :class="['count-label', { warn: narrationOverLimit }]">
                  {{ narrationCount }}/{{ narrationLimit }}
                </span>
                <span class="count-hint">{{ narrationDurationLabel }}</span>
              </div>
              <div class="action-row">
                <button class="pill-btn" :disabled="!narrationText.trim() || isPreviewingTts" @click="previewNarration">
                  {{ isPreviewingTts ? '生成中…' : '试听' }}
                </button>
                <button class="pill-btn ghost" :disabled="!isPreviewingTts" @click="stopNarrationPreview">
                  停顿
                </button>
                <span v-if="previewAudioUrl" class="status-note">已生成试听音频</span>
              </div>
              <div v-if="ttsError" class="status-error">{{ ttsError }}</div>
            </div>

            <div class="info-card">
              <div class="info-title">声音音色</div>
              <div class="voice-card" @click="showVoicePicker = true">
                <div class="voice-name">{{ selectedVoiceOption?.name || '选择音色' }}</div>
                <div class="voice-meta">
                  <span>{{ selectedVoiceOption?.gender || '未知' }}</span>
                  <span>{{ selectedVoiceOption?.age_group || '-' }}</span>
                  <span>{{ selectedVoiceOption?.locale || '' }}</span>
                </div>
              </div>
              <div class="field-row">
                <span class="label">情绪</span>
                <select v-model="selectedEmotion" class="model-select">
                  <option v-for="item in emotionOptions" :key="item" :value="item">{{ item }}</option>
                </select>
              </div>
              <label class="checkbox-row">
                <input type="checkbox" v-model="bindVoiceToRole" @change="handleRoleBinding('voice')" />
                <span>应用关联角色</span>
              </label>
              <div v-if="selectedVoiceRole" class="role-note">已绑定角色：{{ selectedVoiceRole.name }}</div>
            </div>

            <div class="info-card">
              <div class="info-title">声音参数</div>
              <div class="slider-row">
                <span class="label">音量</span>
                <input v-model.number="voiceVolume" type="range" min="0" max="100" step="1" />
                <span class="value">{{ voiceVolume }}</span>
              </div>
              <div class="slider-row">
                <span class="label">语速</span>
                <input v-model.number="voiceSpeed" type="range" min="0.5" max="2" step="0.1" />
                <span class="value">{{ voiceSpeed.toFixed(1) }}x</span>
              </div>
              <label class="checkbox-row">
                <input type="checkbox" v-model="bindParamsToRole" @change="handleRoleBinding('params')" />
                <span>应用关联角色</span>
              </label>
              <div v-if="selectedVoiceRole" class="role-note">已绑定角色：{{ selectedVoiceRole.name }}</div>
            </div>

            <div class="info-card">
              <div class="info-title">应用到当前分镜</div>
              <div class="action-row">
                <button
                  class="pill-btn primary"
                  :disabled="isGeneratingTts || !narrationText.trim() || narrationOverLimit"
                  @click="applyNarration"
                >
                  {{ isGeneratingTts ? '生成中…' : '应用修改' }}
                </button>
                <span v-if="currentClip.audioUrl" class="status-note">已绑定音频</span>
              </div>
              <div v-if="currentClip.audioDurationSec" class="status-hint">
                当前音频时长：{{ Math.round(currentClip.audioDurationSec) }}s
              </div>
            </div>
          </template>

          <template v-else>
            <div class="panel-title">音乐设置</div>
            <div class="music-tabs">
              <button :class="['music-tab', { active: musicTab === 'ai' }]" @click="musicTab = 'ai'">AI 生成</button>
              <button :class="['music-tab', { active: musicTab === 'library' }]" @click="musicTab = 'library'">
                音乐库
              </button>
            </div>

            <div v-if="musicTab === 'ai'" class="info-card">
              <div class="info-title">AI 生成音乐</div>
              <div class="music-input">
                <textarea
                  v-model="musicPrompt"
                  class="prompt-editor"
                  rows="3"
                  :maxlength="musicPromptLimit"
                  placeholder="描述你想要生成的音乐"
                ></textarea>
                <div class="row-between">
                  <span :class="['count-label', { warn: musicPromptOverLimit }]">
                    {{ musicPromptCount }}/{{ musicPromptLimit }}
                  </span>
                  <button
                    class="pill-btn"
                    :disabled="isGeneratingMusic || !musicPrompt.trim() || musicPromptOverLimit"
                    @click="generateMusicTrack"
                  >
                    {{ isGeneratingMusic ? '生成中…' : '生成' }}
                  </button>
                </div>
                <div v-if="musicError" class="status-error">{{ musicError }}</div>
              </div>

              <div class="music-list" v-if="musicAiResults.length">
                <div
                  v-for="item in musicAiResults"
                  :key="item.id"
                  :class="['music-card', { active: item.id === selectedMusicId }]"
                  @click="selectMusicItem(item)"
                >
                  <div class="music-cover" :style="{ background: item.cover_style || defaultCoverStyle }"></div>
                  <div class="music-info">
                    <div class="music-title">{{ item.title }}</div>
                    <div class="music-meta">
                      <span>{{ formatDuration(item.duration_sec) }}</span>
                      <span>{{ item.source === 'ai' ? 'AI' : '' }}</span>
                    </div>
                    <div class="music-progress">
                      <div class="music-progress-bar" :style="{ width: musicProgressFor(item) + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-panel">暂无生成记录</div>
            </div>

            <div v-else class="info-card">
              <div class="info-title">音乐库</div>
              <div class="music-upload">
                <input
                  ref="musicFileInputRef"
                  type="file"
                  accept="audio/*"
                  class="file-input"
                  @change="handleMusicUpload"
                />
                <button class="pill-btn" :disabled="isUploadingMusic" @click="triggerMusicUpload">
                  {{ isUploadingMusic ? '上传中…' : '从本地上传' }}
                </button>
              </div>
              <div class="music-list">
                <div
                  v-for="item in musicLibrary"
                  :key="item.id"
                  :class="['music-card', { active: item.id === selectedMusicId }]"
                  @click="selectMusicItem(item)"
                >
                  <div class="music-cover" :style="{ background: item.cover_style || defaultCoverStyle }"></div>
                  <div class="music-info">
                    <div class="music-title">{{ item.title }}</div>
                    <div class="music-meta">
                      <span>{{ formatDuration(item.duration_sec) }}</span>
                      <span>{{ item.source === 'library' ? '库' : '上传' }}</span>
                    </div>
                    <div class="music-progress">
                      <div class="music-progress-bar" :style="{ width: musicProgressFor(item) + '%' }"></div>
                    </div>
                  </div>
                </div>
                <div v-if="musicLibrary.length === 0" class="empty-panel">暂无音乐</div>
              </div>
              <div v-if="musicError" class="status-error">{{ musicError }}</div>
            </div>

            <div class="music-footer">
              <div class="slider-row">
                <span class="label">音量</span>
                <input v-model.number="musicVolume" type="range" min="0" max="100" step="1" />
                <span class="value">{{ musicVolume }}</span>
              </div>
              <button class="pill-btn primary" :disabled="!selectedMusicId" @click="applyMusicToShot">
                应用
              </button>
            </div>
          </template>
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
            @play="handleVideoPlay"
            @pause="handleVideoPause"
            @timeupdate="handleVideoTimeUpdate"
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

    <div v-if="showExportModal" class="modal-backdrop">
      <div class="modal-card export-modal">
        <div class="modal-title">导出配置</div>
        <div class="export-grid">
          <label class="field-row">
            <span class="label">分辨率</span>
            <select v-model="exportConfig.resolution" class="model-select">
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
              <option value="4k">4K</option>
            </select>
          </label>
          <label class="field-row">
            <span class="label">格式</span>
            <select v-model="exportConfig.format" class="model-select">
              <option value="mp4">MP4</option>
              <option value="mov">MOV</option>
            </select>
          </label>
          <label class="field-row">
            <span class="label">画幅</span>
            <select v-model="exportConfig.aspectRatio" class="model-select">
              <option value="16:9">16:9</option>
              <option value="9:16">9:16</option>
              <option value="1:1">1:1</option>
            </select>
          </label>
        </div>

        <div class="export-section">
          <div class="field-row">
            <span class="label">字幕</span>
            <label class="toggle">
              <input type="checkbox" v-model="exportConfig.subtitleEnabled" />
              <span>启用字幕</span>
            </label>
          </div>
          <div v-if="exportConfig.subtitleEnabled" class="export-grid">
            <label class="field-row">
              <span class="label">烧录</span>
              <label class="toggle">
                <input type="checkbox" v-model="exportConfig.subtitleBurnIn" />
                <span>烧录字幕</span>
              </label>
            </label>
            <label class="field-row">
              <span class="label">字体</span>
              <input v-model="exportConfig.subtitleFont" class="text-input" placeholder="思源黑体" />
            </label>
            <label class="field-row">
              <span class="label">颜色</span>
              <input v-model="exportConfig.subtitleColor" class="text-input" placeholder="#FFFFFF" />
            </label>
            <label class="field-row">
              <span class="label">字号</span>
              <input v-model="exportConfig.subtitleSize" class="text-input" placeholder="36" />
            </label>
          </div>
        </div>

        <div class="export-section">
          <div class="field-row">
            <span class="label">封面</span>
            <select v-model="exportConfig.coverMode" class="model-select">
              <option value="auto">自动生成</option>
              <option value="none">不生成</option>
            </select>
          </div>
        </div>

        <div v-if="exportEstimatedMinutes" class="export-note">
          导出可能需要较长时间，预计完成时间为 {{ exportEstimatedMinutes }} 分钟。
        </div>
        <div v-if="exportStatus === 'running'" class="export-note">
          导出进度：{{ exportProgress }}%
        </div>

        <div v-if="exportStatus === 'completed'" class="export-success">
          导出完成！您可以下载文件。
        </div>
        <div v-if="exportStatus === 'failed'" class="export-error">
          导出失败，请稍后重试。
        </div>

        <div v-if="exportFiles.length" class="export-files">
          <div v-for="file in exportFiles" :key="file.id" class="export-file">
            <div class="export-file-meta">
              <span>{{ file.format || 'MP4' }}</span>
              <span>{{ file.resolution || exportConfig.resolution }}</span>
            </div>
            <button class="pill-btn primary" @click="downloadExportFile(file.id)">下载</button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="pill-btn ghost" @click="closeExportModal">后台导出</button>
          <button
            class="pill-btn primary"
            :disabled="isExporting || exportStatus === 'running'"
            @click="startExport"
          >
            {{ exportStatus === 'running' ? '导出中…' : '开始导出' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showVoicePicker" class="modal-backdrop">
      <div class="modal-card">
        <div class="modal-title">选择音色</div>
        <div class="voice-list">
          <button
            v-for="voice in voiceOptions"
            :key="voice.id"
            :class="['voice-option', { active: voice.id === selectedVoiceId }]"
            @click="pickVoice(voice)"
          >
            <div class="voice-name">{{ voice.name }}</div>
            <div class="voice-meta">
              <span>{{ voice.gender || '未知' }}</span>
              <span>{{ voice.age_group || '-' }}</span>
              <span>{{ voice.locale || '' }}</span>
            </div>
            <div class="voice-desc">{{ voice.description || '适合通用旁白' }}</div>
          </button>
          <div v-if="voiceOptions.length === 0" class="empty-text">暂无可用音色</div>
        </div>
        <div class="modal-actions">
          <button class="pill-btn ghost" @click="showVoicePicker = false">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showRolePicker" class="modal-backdrop">
      <div class="modal-card">
        <div class="modal-title">选择角色</div>
        <div class="role-list">
          <button
            v-for="role in voiceRoles"
            :key="role.id"
            :class="['role-option', { active: role.id === roleSelectionId }]"
            @click="roleSelectionId = role.id"
          >
            <span class="role-name">{{ role.name }}</span>
            <span class="role-meta">{{ role.voice_id || '未绑定音色' }}</span>
          </button>
          <div v-if="voiceRoles.length === 0" class="empty-text">暂无角色，请新建</div>
        </div>
        <div class="role-create">
          <input v-model="roleDraftName" class="prompt-editor" placeholder="新建角色名称" />
          <button class="pill-btn" @click="createRoleAndBind">创建并绑定</button>
        </div>
        <div class="modal-actions">
          <button class="pill-btn ghost" @click="closeRolePicker">取消</button>
          <button class="pill-btn primary" :disabled="!roleSelectionId" @click="confirmRolePicker">确认绑定</button>
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
import {
  createExportTask,
  fetchExportDownloadUrl,
  fetchExportFiles,
  fetchExportTask,
  type ExportFile,
} from '@/api/exports';
import { adoptImage, regenerateImage, rewriteImagePrompt } from '@/api/images';
import { fetchModels, type ModelOption } from '@/api/models';
import { fetchProject } from '@/api/projects';
import { fetchVoiceOptions, generateStoryboardAudio, previewTts, type VoiceOption } from '@/api/tts';
import { createVoiceRole, fetchVoiceRoles, updateVoiceRole, type VoiceRole } from '@/api/voiceRoles';
import { applyStoryboardMusic, fetchMusicLibrary, generateMusic, uploadMusic, type MusicItem } from '@/api/music';

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
  audioId?: string;
  audioUrl?: string;
  audioText?: string;
  audioDurationSec?: number;
  audioVoiceId?: string;
  audioEmotion?: string;
  audioVolume?: number;
  audioSpeed?: number;
  audioRoleId?: string;
  status: 'ready' | 'pending';
  type: 'image' | 'video';
}

const router = useRouter();

const projectName = ref('未命名创作');
const packageName = ref('');
const currentPackageId = ref<string | null>(null);
const clips = ref<Clip[]>([]);
const viewMode = ref<'timeline' | 'story'>('timeline');
const leftTab = ref<'visual' | 'voice' | 'music'>('visual');
const musicTab = ref<'ai' | 'library'>('ai');

const currentShotIndex = ref(0);
const currentTimeSec = ref(0);
const timelineRef = ref<HTMLElement | null>(null);

const currentClip = computed(() => clips.value[currentShotIndex.value] || null);
const narrationCount = computed(() => narrationText.value.length);
const narrationOverLimit = computed(() => narrationCount.value > narrationLimit);
const narrationDurationSec = computed(() => {
  if (!narrationCount.value) return 0;
  const safeSpeed = Math.max(0.1, voiceSpeed.value);
  return Math.max(1, Math.round((narrationCount.value * 0.12) / safeSpeed));
});
const narrationDurationLabel = computed(() => {
  if (!narrationCount.value) return '未输入';
  return `约 ${narrationDurationSec.value}s 音频`;
});
const selectedVoiceOption = computed(() => {
  return voiceOptions.value.find(item => item.id === selectedVoiceId.value) || voiceOptions.value[0] || null;
});
const selectedVoiceRole = computed(() => {
  if (!selectedRoleId.value) return null;
  return voiceRoles.value.find(item => item.id === selectedRoleId.value) || null;
});
const musicPromptCount = computed(() => musicPrompt.value.length);
const musicPromptOverLimit = computed(() => musicPromptCount.value > musicPromptLimit);
const defaultCoverStyle = 'linear-gradient(135deg, #c7d2fe, #fbcfe8)';
const isGeneratingStoryboard = ref(false);
const storyboardError = ref('');
const storyboardRetryCount = ref(0);
const MAX_STORYBOARD_RETRIES = 2;
const STORYBOARD_RETRY_DELAY_MS = 5000;
let storyboardRetryTimer: number | null = null;
const isEditingPrompt = ref(false);
const isImagePromptOpen = ref(false);
const isVideoPromptOpen = ref(false);
const promptDraft = ref('');
const feedbackDraft = ref('');
const isRegeneratingImage = ref(false);
const isGeneratingVideo = ref(false);
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
const imageModels = ref<ModelOption[]>([]);
const videoModels = ref<ModelOption[]>([]);
const selectedImageModelId = ref('');
const selectedVideoModelId = ref('');
const voiceOptions = ref<VoiceOption[]>([]);
const voiceRoles = ref<VoiceRole[]>([]);
const showVoicePicker = ref(false);
const showRolePicker = ref(false);
const rolePickerMode = ref<'voice' | 'params' | null>(null);
const roleSelectionId = ref('');
const roleDraftName = ref('');
const narrationText = ref('');
const narrationLimit = 240;
const selectedVoiceId = ref('');
const selectedEmotion = ref('默认');
const voiceVolume = ref(100);
const voiceSpeed = ref(1.0);
const bindVoiceToRole = ref(false);
const bindParamsToRole = ref(false);
const selectedRoleId = ref('');
const isPreviewingTts = ref(false);
const isGeneratingTts = ref(false);
const ttsError = ref('');
const previewAudio = ref<HTMLAudioElement | null>(null);
const previewAudioUrl = ref('');
const emotionOptions = ['默认', '开心', '悲伤', '愤怒', '温柔', '激动'];
const musicPrompt = ref('');
const musicPromptLimit = 30;
const isGeneratingMusic = ref(false);
const isUploadingMusic = ref(false);
const musicError = ref('');
const musicLibrary = ref<MusicItem[]>([]);
const musicAiResults = ref<MusicItem[]>([]);
const selectedMusicId = ref('');
const musicVolume = ref(35);
const musicFileInputRef = ref<HTMLInputElement | null>(null);
const musicPreviewAudio = ref<HTMLAudioElement | null>(null);
const musicPlayingId = ref('');
const musicPlayingTime = ref(0);
const musicPlayingDuration = ref(0);
const showExportModal = ref(false);
const exportTaskId = ref('');
const exportStatus = ref<'idle' | 'running' | 'completed' | 'failed'>('idle');
const exportProgress = ref(0);
const exportEstimatedMinutes = ref(0);
const exportFiles = ref<ExportFile[]>([]);
const isExporting = ref(false);
const exportConfig = ref({
  resolution: '1080p',
  format: 'mp4',
  aspectRatio: '16:9',
  subtitleEnabled: false,
  subtitleBurnIn: false,
  subtitleFont: '思源黑体',
  subtitleColor: '#FFFFFF',
  subtitleSize: '36',
  coverMode: 'auto',
});
let exportPollTimer: number | null = null;

const getExportTaskStorageKey = (projectId: string) => `exportTaskId:${projectId}`;

const storeExportTaskId = (projectId: string, taskId: string) => {
  sessionStorage.setItem(getExportTaskStorageKey(projectId), taskId);
};

const clearExportTaskId = (projectId: string) => {
  sessionStorage.removeItem(getExportTaskStorageKey(projectId));
};

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

const pickModel = (items: ModelOption[], storedId: string, type: 'image' | 'video') => {
  if (!items.length) return;
  const enabled = items.filter(item => item.enabled);
  const fallback = enabled.find(item => item.is_default) || enabled[0];
  if (!fallback) return;
  const matched = items.find(item => item.id === storedId && item.enabled)?.id || fallback.id;
  if (type === 'image') {
    selectedImageModelId.value = matched;
    sessionStorage.setItem('selectedImageModelId', matched);
  } else {
    selectedVideoModelId.value = matched;
    sessionStorage.setItem('selectedVideoModelId', matched);
  }
};

const openExportModal = () => {
  showExportModal.value = true;
  restoreExportTask().catch(() => null);
  refreshExportFiles().catch(() => null);
};

const closeExportModal = () => {
  showExportModal.value = false;
  stopExportPolling();
};

const stopExportPolling = () => {
  if (exportPollTimer !== null) {
    window.clearInterval(exportPollTimer);
    exportPollTimer = null;
  }
};

const refreshExportFiles = async () => {
  const projectId = sessionStorage.getItem('currentProjectId');
  if (!projectId) return;
  const files = await fetchExportFiles(projectId);
  exportFiles.value = files;
};

const pollExportTask = async () => {
  if (!exportTaskId.value) return;
  const task = await fetchExportTask(exportTaskId.value);
  exportProgress.value = Number(task.progress || 0);
  if (task.status === 'completed') {
    exportStatus.value = 'completed';
    await refreshExportFiles();
    const projectId = sessionStorage.getItem('currentProjectId');
    if (projectId) {
      clearExportTaskId(projectId);
    }
    stopExportPolling();
    return;
  }
  if (task.status === 'failed') {
    exportStatus.value = 'failed';
    const projectId = sessionStorage.getItem('currentProjectId');
    if (projectId) {
      clearExportTaskId(projectId);
    }
    stopExportPolling();
    return;
  }
  exportStatus.value = 'running';
};

const startExportPolling = () => {
  stopExportPolling();
  exportPollTimer = window.setInterval(() => {
    pollExportTask().catch(() => null);
  }, 5000);
};

const startExport = async () => {
  const projectId = sessionStorage.getItem('currentProjectId');
  if (!projectId) {
    alert('缺少项目 ID，无法导出');
    return;
  }
  if (isExporting.value) return;
  isExporting.value = true;
  exportStatus.value = 'running';
  exportProgress.value = 0;
  exportFiles.value = [];
  try {
    const result = await createExportTask(projectId, {
      resolution: exportConfig.value.resolution,
      format: exportConfig.value.format,
      aspect_ratio: exportConfig.value.aspectRatio,
      subtitle_enabled: exportConfig.value.subtitleEnabled,
      subtitle_burn_in: exportConfig.value.subtitleBurnIn,
      subtitle_style: {
        font: exportConfig.value.subtitleFont,
        color: exportConfig.value.subtitleColor,
        size: exportConfig.value.subtitleSize,
      },
      cover_mode: exportConfig.value.coverMode,
    });
    exportTaskId.value = result.export_task_id;
    storeExportTaskId(projectId, exportTaskId.value);
    exportEstimatedMinutes.value = result.estimated_minutes || 0;
    startExportPolling();
    pollExportTask().catch(() => null);
  } catch (err) {
    exportStatus.value = 'failed';
    alert(err instanceof Error ? err.message : '导出失败');
  } finally {
    isExporting.value = false;
  }
};

const restoreExportTask = async () => {
  const projectId = sessionStorage.getItem('currentProjectId');
  if (!projectId) return;
  const storedTaskId = sessionStorage.getItem(getExportTaskStorageKey(projectId));
  if (!storedTaskId) return;
  exportTaskId.value = storedTaskId;
  exportStatus.value = 'running';
  exportProgress.value = 0;
  try {
    await pollExportTask();
    if (exportStatus.value === 'running') {
      startExportPolling();
    }
  } catch (err) {
    clearExportTaskId(projectId);
  }
};

const downloadExportFile = async (fileId: string) => {
  if (!fileId) return;
  try {
    const url = await fetchExportDownloadUrl(fileId);
    if (url) {
      window.open(url, '_blank');
    }
  } catch (err) {
    alert(err instanceof Error ? err.message : '获取下载链接失败');
  }
};

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

const clearStoryboardRetry = () => {
  if (storyboardRetryTimer !== null) {
    window.clearTimeout(storyboardRetryTimer);
    storyboardRetryTimer = null;
  }
  storyboardRetryCount.value = 0;
};

const scheduleStoryboardRetry = (packageId: string) => {
  if (storyboardRetryCount.value >= MAX_STORYBOARD_RETRIES) {
    storyboardError.value = '分镜图生成失败，请稍后重试';
    return;
  }
  storyboardRetryCount.value += 1;
  storyboardError.value = `分镜图生成失败，正在自动重试（${storyboardRetryCount.value}/${MAX_STORYBOARD_RETRIES}）`;
  if (storyboardRetryTimer !== null) {
    window.clearTimeout(storyboardRetryTimer);
  }
  storyboardRetryTimer = window.setTimeout(async () => {
    storyboardRetryTimer = null;
    try {
      const latest = await fetchMaterialPackage(packageId);
      await ensureStoryboardImages(latest);
    } catch (err) {
      storyboardError.value = err instanceof Error ? err.message : '素材包刷新失败';
    }
  }, STORYBOARD_RETRY_DELAY_MS);
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

const handleVideoPlay = () => {
  if (!videoRef.value) return;
  if (playMode.value !== 'video') {
    stopPlayback();
  }
  playMode.value = 'video';
  isPlaying.value = true;
  const start = clipStartTimes.value[currentShotIndex.value] ?? 0;
  currentTimeSec.value = start + (videoRef.value.currentTime || 0);
};

const handleVideoPause = () => {
  if (playMode.value === 'video') {
    isPlaying.value = false;
    playMode.value = null;
  }
};

const handleVideoTimeUpdate = () => {
  if (!videoRef.value) return;
  const start = clipStartTimes.value[currentShotIndex.value] ?? 0;
  currentTimeSec.value = start + (videoRef.value.currentTime || 0);
};

const handleVideoEnded = () => {
  if (playMode.value === 'video') {
    const start = clipStartTimes.value[currentShotIndex.value] ?? 0;
    const clipDuration = currentClip.value?.durationSec || 0;
    currentTimeSec.value = start + clipDuration;
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
    if (playMode.value === 'video') {
      isPlaying.value = false;
      playMode.value = null;
    }
    if (videoRef.value) {
      videoRef.value.pause();
      videoRef.value.currentTime = 0;
    }
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
  const audiosRaw = Array.isArray(metadata.audios) ? metadata.audios : [];
  const musicBindingsRaw = Array.isArray(metadata.music_bindings) ? metadata.music_bindings : [];

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

  const storyboardAudioByShot = new Map<string, any>();
  audiosRaw.forEach((audio: any) => {
    if (!audio || typeof audio !== 'object') return;
    if (audio.type !== 'storyboard_audio') return;
    const shotId = normalizeText(audio.shot_id || audio.shotId, '');
    if (!shotId) return;
    const isActive = audio.is_active === true || audio.isActive === true;
    if (isActive || !storyboardAudioByShot.has(shotId)) {
      storyboardAudioByShot.set(shotId, audio);
    }
  });

  const storyboardMusicByShot = new Map<string, any>();
  musicBindingsRaw.forEach((binding: any) => {
    if (!binding || typeof binding !== 'object') return;
    if (binding.type !== 'storyboard_music') return;
    const shotId = normalizeText(binding.shot_id || binding.shotId, '');
    if (!shotId) return;
    const isActive = binding.is_active === true || binding.isActive === true;
    if (isActive || !storyboardMusicByShot.has(shotId)) {
      storyboardMusicByShot.set(shotId, binding);
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
    const audioData = storyboardAudioByShot.get(shotId);
    const musicData = storyboardMusicByShot.get(shotId);

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
      audioId: normalizeText(audioData?.id, ''),
      audioUrl: normalizeText(audioData?.url, ''),
      audioText: normalizeText(audioData?.text, ''),
      audioDurationSec: typeof audioData?.duration_sec === 'number' ? audioData.duration_sec : undefined,
      audioVoiceId: normalizeText(audioData?.voice_id, ''),
      audioEmotion: normalizeText(audioData?.emotion, ''),
      audioVolume: typeof audioData?.volume === 'number' ? audioData.volume : undefined,
      audioSpeed: typeof audioData?.speed === 'number' ? audioData.speed : undefined,
      audioRoleId: normalizeText(audioData?.role_id, ''),
      musicId: normalizeText(musicData?.music_id, ''),
      musicTitle: normalizeText(musicData?.music_title, ''),
      musicUrl: normalizeText(musicData?.music_url, ''),
      musicVolume: typeof musicData?.volume === 'number' ? musicData.volume : undefined,
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

const resolveProjectId = () => sessionStorage.getItem('currentProjectId') || '';

const loadVoiceAssets = async () => {
  const projectId = resolveProjectId();
  if (!projectId) return;
  try {
    const [voices, roles] = await Promise.all([fetchVoiceOptions(), fetchVoiceRoles(projectId)]);
    voiceOptions.value = voices;
    voiceRoles.value = roles;
    if (!selectedVoiceId.value && voices.length) {
      selectedVoiceId.value = voices[0].id;
    }
  } catch (err) {
    // Ignore to avoid blocking editor load.
  }
};

const syncVoicePanelFromClip = (clip: Clip | null) => {
  if (!clip) {
    narrationText.value = '';
    previewAudioUrl.value = '';
    ttsError.value = '';
    return;
  }
  stopNarrationPreview();
  narrationText.value = clip.audioText || '';
  voiceVolume.value = clip.audioVolume ?? 100;
  voiceSpeed.value = clip.audioSpeed ?? 1.0;
  selectedEmotion.value = clip.audioEmotion || '默认';
  if (clip.audioVoiceId) {
    selectedVoiceId.value = clip.audioVoiceId;
  } else if (!selectedVoiceId.value && voiceOptions.value.length) {
    selectedVoiceId.value = voiceOptions.value[0].id;
  }
  selectedRoleId.value = clip.audioRoleId || '';
  bindVoiceToRole.value = Boolean(clip.audioRoleId);
  bindParamsToRole.value = Boolean(clip.audioRoleId);
  previewAudioUrl.value = clip.audioUrl || '';
  ttsError.value = '';
};

const syncMusicPanelFromClip = (clip: Clip | null) => {
  if (!clip) {
    selectedMusicId.value = '';
    musicVolume.value = 35;
    return;
  }
  selectedMusicId.value = clip.musicId || '';
  musicVolume.value = typeof clip.musicVolume === 'number' ? clip.musicVolume : 35;
  stopMusicPreview();
};

const pickVoice = (voice: VoiceOption) => {
  selectedVoiceId.value = voice.id;
  showVoicePicker.value = false;
};

const openRolePicker = (mode: 'voice' | 'params') => {
  rolePickerMode.value = mode;
  roleSelectionId.value = selectedRoleId.value;
  roleDraftName.value = '';
  showRolePicker.value = true;
};

const closeRolePicker = () => {
  showRolePicker.value = false;
  rolePickerMode.value = null;
};

const confirmRolePicker = () => {
  if (!roleSelectionId.value) return;
  selectedRoleId.value = roleSelectionId.value;
  showRolePicker.value = false;
  rolePickerMode.value = null;
};

const createRoleAndBind = async () => {
  const name = roleDraftName.value.trim();
  if (!name) {
    alert('请输入角色名称');
    return;
  }
  const projectId = resolveProjectId();
  if (!projectId) {
    alert('缺少项目 ID');
    return;
  }
  try {
    const role = await createVoiceRole({
      project_id: projectId,
      name,
      voice_id: selectedVoiceId.value || undefined,
      emotion: selectedEmotion.value !== '默认' ? selectedEmotion.value : undefined,
      volume: voiceVolume.value,
      speed: voiceSpeed.value,
    });
    voiceRoles.value = [role, ...voiceRoles.value.filter(item => item.id !== role.id)];
    selectedRoleId.value = role.id;
    roleSelectionId.value = role.id;
    showRolePicker.value = false;
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建角色失败');
  }
};

const handleRoleBinding = (mode: 'voice' | 'params') => {
  const needsRole = bindVoiceToRole.value || bindParamsToRole.value;
  if (needsRole && !selectedRoleId.value) {
    openRolePicker(mode);
  }
};

const syncRoleSettings = async () => {
  if (!selectedRoleId.value) return;
  try {
    const role = await updateVoiceRole(selectedRoleId.value, {
      voice_id: selectedVoiceId.value || undefined,
      emotion: selectedEmotion.value !== '默认' ? selectedEmotion.value : undefined,
      volume: voiceVolume.value,
      speed: voiceSpeed.value,
    });
    voiceRoles.value = [role, ...voiceRoles.value.filter(item => item.id !== role.id)];
  } catch (err) {
    // Ignore to avoid blocking TTS apply.
  }
};

const loadMusicLibrary = async () => {
  const projectId = resolveProjectId();
  if (!projectId) return;
  try {
    const list = await fetchMusicLibrary(projectId);
    musicLibrary.value = list;
    musicAiResults.value = list.filter(item => item.source === 'ai');
  } catch (err) {
    musicError.value = err instanceof Error ? err.message : '加载音乐库失败';
  }
};

const formatDuration = (seconds?: number) => {
  if (!seconds || seconds <= 0) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

const musicProgressFor = (item: MusicItem) => {
  if (musicPlayingId.value !== item.id || !musicPlayingDuration.value) return 0;
  return Math.min(100, (musicPlayingTime.value / musicPlayingDuration.value) * 100);
};

const stopMusicPreview = () => {
  if (musicPreviewAudio.value) {
    musicPreviewAudio.value.pause();
    musicPreviewAudio.value.currentTime = 0;
  }
  musicPreviewAudio.value = null;
  musicPlayingId.value = '';
  musicPlayingTime.value = 0;
  musicPlayingDuration.value = 0;
};

const playMusicPreview = (item: MusicItem) => {
  if (!item.url) return;
  if (musicPlayingId.value === item.id && musicPreviewAudio.value) {
    stopMusicPreview();
    return;
  }
  stopMusicPreview();
  const audio = new Audio(item.url);
  musicPreviewAudio.value = audio;
  musicPlayingId.value = item.id;
  musicPlayingDuration.value = item.duration_sec || 0;
  audio.addEventListener('timeupdate', () => {
    musicPlayingTime.value = audio.currentTime;
    if (!musicPlayingDuration.value && audio.duration) {
      musicPlayingDuration.value = audio.duration;
    }
  });
  audio.addEventListener('ended', () => {
    stopMusicPreview();
  });
  audio.play().catch(() => {
    stopMusicPreview();
  });
};

const selectMusicItem = (item: MusicItem) => {
  selectedMusicId.value = item.id;
  playMusicPreview(item);
};

const generateMusicTrack = async () => {
  const projectId = resolveProjectId();
  if (!projectId) {
    alert('缺少项目 ID');
    return;
  }
  if (!musicPrompt.value.trim() || musicPromptOverLimit.value) {
    alert('请输入简短的音乐描述');
    return;
  }
  isGeneratingMusic.value = true;
  musicError.value = '';
  try {
    const track = await generateMusic({ project_id: projectId, prompt: musicPrompt.value.trim() });
    musicAiResults.value = [track, ...musicAiResults.value.filter(item => item.id !== track.id)];
    musicLibrary.value = [track, ...musicLibrary.value.filter(item => item.id !== track.id)];
    selectedMusicId.value = track.id;
    musicPrompt.value = '';
  } catch (err) {
    musicError.value = err instanceof Error ? err.message : '生成音乐失败';
  } finally {
    isGeneratingMusic.value = false;
  }
};

const triggerMusicUpload = () => {
  musicFileInputRef.value?.click();
};

const handleMusicUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files ? Array.from(target.files) : [];
  if (!files.length) return;
  const projectId = resolveProjectId();
  if (!projectId) return;
  isUploadingMusic.value = true;
  try {
    const track = await uploadMusic(projectId, files[0]);
    musicLibrary.value = [track, ...musicLibrary.value.filter(item => item.id !== track.id)];
    selectedMusicId.value = track.id;
  } catch (err) {
    musicError.value = err instanceof Error ? err.message : '上传音乐失败';
  } finally {
    isUploadingMusic.value = false;
    target.value = '';
  }
};

const applyMusicToShot = async () => {
  const clip = currentClip.value;
  if (!clip || !currentPackageId.value) return;
  if (!selectedMusicId.value) {
    alert('请选择音乐');
    return;
  }
  try {
    await applyStoryboardMusic(currentPackageId.value, clip.shotId, {
      music_id: selectedMusicId.value,
      volume: musicVolume.value,
    });
    await refreshPackage(currentPackageId.value, clip.shotId);
  } catch (err) {
    musicError.value = err instanceof Error ? err.message : '应用音乐失败';
  }
};

const previewNarration = async () => {
  if (!narrationText.value.trim() || narrationOverLimit.value) return;
  const projectId = resolveProjectId();
  if (!projectId) {
    alert('缺少项目 ID');
    return;
  }
  if (!selectedVoiceId.value && voiceOptions.value.length) {
    selectedVoiceId.value = voiceOptions.value[0].id;
  }
  if (!selectedVoiceId.value) {
    alert('请先选择音色');
    return;
  }
  isPreviewingTts.value = true;
  ttsError.value = '';
  try {
    const audio = await previewTts({
      project_id: projectId,
      text: narrationText.value.trim(),
      voice_id: selectedVoiceId.value,
      emotion: selectedEmotion.value !== '默认' ? selectedEmotion.value : undefined,
      speed: voiceSpeed.value,
      volume: voiceVolume.value,
    });
    previewAudioUrl.value = audio.url;
    if (previewAudio.value) {
      previewAudio.value.pause();
      previewAudio.value = null;
    }
    const audioPlayer = new Audio(audio.url);
    previewAudio.value = audioPlayer;
    await audioPlayer.play();
    audioPlayer.onended = () => {
      isPreviewingTts.value = false;
    };
  } catch (err) {
    ttsError.value = err instanceof Error ? err.message : '生成试听音频失败';
    isPreviewingTts.value = false;
  }
};

function stopNarrationPreview() {
  if (previewAudio.value) {
    previewAudio.value.pause();
    previewAudio.value.currentTime = 0;
  }
  isPreviewingTts.value = false;
}

const applyNarration = async () => {
  const clip = currentClip.value;
  if (!clip || !currentPackageId.value) return;
  if (!narrationText.value.trim() || narrationOverLimit.value) return;
  if (!selectedVoiceId.value) {
    alert('请先选择音色');
    return;
  }
  if ((bindVoiceToRole.value || bindParamsToRole.value) && !selectedRoleId.value) {
    openRolePicker('voice');
    return;
  }
  isGeneratingTts.value = true;
  ttsError.value = '';
  try {
    await generateStoryboardAudio(currentPackageId.value, clip.shotId, {
      text: narrationText.value.trim(),
      voice_id: selectedVoiceId.value,
      emotion: selectedEmotion.value !== '默认' ? selectedEmotion.value : undefined,
      speed: voiceSpeed.value,
      volume: voiceVolume.value,
      role_id: selectedRoleId.value || undefined,
    });
    if (bindVoiceToRole.value || bindParamsToRole.value) {
      await syncRoleSettings();
    }
    await refreshPackage(currentPackageId.value, clip.shotId);
  } catch (err) {
    ttsError.value = err instanceof Error ? err.message : '生成配音失败';
  } finally {
    isGeneratingTts.value = false;
  }
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
  if (isGeneratingStoryboard.value) return;
  if (!hasMissingStoryboardImages(pkg)) {
    storyboardError.value = '';
    clearStoryboardRetry();
    return;
  }
  isGeneratingStoryboard.value = true;
  storyboardError.value = '';
  try {
    const result = await generateStoryboardImages(pkg.id, false, selectedImageModelId.value || undefined);
    if (!result.generated || result.generated.length === 0) {
      scheduleStoryboardRetry(pkg.id);
    } else {
      clearStoryboardRetry();
      storyboardError.value = '';
    }
    await refreshPackage(pkg.id);
  } catch (err) {
    scheduleStoryboardRetry(pkg.id);
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
    const result = await regenerateImage(
      currentClip.value.imageId,
      prompt,
      'user_edit',
      undefined,
      selectedImageModelId.value || undefined
    );
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
    const result = await regenerateImage(
      currentClip.value.imageId,
      rewritten.rewritten_prompt,
      'user_feedback',
      undefined,
      selectedImageModelId.value || undefined
    );
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
      model_id: selectedVideoModelId.value || undefined,
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
      model_id: selectedVideoModelId.value || undefined,
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
      model_id: selectedVideoModelId.value || undefined,
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
      clearStoryboardRetry();
      stopPlayback();
      return;
    }
    currentPackageId.value = active.id;
    packageName.value = active.package_name || '素材包';
    const nextClips = buildClipsFromPackage(active);
    clips.value = nextClips;
    buildVideoStateFromPackage(active, nextClips);
    clearStoryboardRetry();
    await ensureStoryboardImages(active);
    stopPlayback();
    currentShotIndex.value = 0;
    currentTimeSec.value = 0;
  } catch (err) {
    clips.value = [];
    storyboardError.value = err instanceof Error ? err.message : '素材包加载失败';
    videoState.value = {};
    clearStoryboardRetry();
  }
};

watch(
  () => selectedImageModelId.value,
  value => {
    if (value) {
      sessionStorage.setItem('selectedImageModelId', value);
    }
  }
);

watch(
  () => selectedVideoModelId.value,
  value => {
    if (value) {
      sessionStorage.setItem('selectedVideoModelId', value);
    }
  }
);

watch(
  () => currentClip.value,
  clip => {
    syncVoicePanelFromClip(clip);
    syncMusicPanelFromClip(clip);
  },
  { immediate: true }
);

watch(
  () => narrationText.value,
  value => {
    if (value.length > narrationLimit) {
      narrationText.value = value.slice(0, narrationLimit);
    }
  }
);

watch(
  () => musicPrompt.value,
  value => {
    if (value.length > musicPromptLimit) {
      musicPrompt.value = value.slice(0, musicPromptLimit);
    }
  }
);

const goBack = () => {
  router.push('/materials');
};

onMounted(() => {
  const storedImage = sessionStorage.getItem('selectedImageModelId') || '';
  const storedVideo = sessionStorage.getItem('selectedVideoModelId') || '';
  fetchModels('image')
    .then(items => {
      imageModels.value = items;
      pickModel(items, storedImage, 'image');
    })
    .catch(() => {
      imageModels.value = [];
    });
  fetchModels('video')
    .then(items => {
      videoModels.value = items;
      pickModel(items, storedVideo, 'video');
    })
    .catch(() => {
      videoModels.value = [];
    });
  loadVoiceAssets();
  loadMusicLibrary();
  loadEditorData();
});

onUnmounted(() => {
  stopPlayback();
  stopMusicPreview();
  stopVideoPolling();
  stopExportPolling();
  clearStoryboardRetry();
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
  background: rgba(10, 16, 28, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.floating-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--md-stroke);
  border-radius: 9999px;
  padding: 8px 12px;
  box-shadow: 0 12px 24px rgba(2, 6, 23, 0.35);
}

.pill-btn {
  padding: 8px 14px;
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(var(--md-accent-rgb), 0.1);
}

.pill-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pill-btn.primary {
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.85));
  color: #031019;
  font-weight: 700;
}

.pill-btn.ghost {
  background: transparent;
  border-color: rgba(148, 163, 184, 0.2);
}

.editor-layout {
  display: grid;
  grid-template-columns: 340px 8px 1fr;
  gap: 12px;
  min-height: 420px;
  height: calc(100vh - 320px);
}

.editor-left {
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  padding: 12px;
  overflow-y: auto;
  box-shadow: var(--md-card-shadow-soft);
}

.panel-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.7);
  color: var(--md-on-surface-variant);
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.tab-btn.active {
  border-color: rgba(var(--md-accent-rgb), 0.6);
  color: var(--md-primary);
  background: rgba(var(--md-accent-rgb), 0.12);
}

.music-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.music-tab {
  flex: 1;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.7);
  color: var(--md-on-surface-variant);
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.music-tab.active {
  background: rgba(var(--md-accent-rgb), 0.12);
  color: var(--md-on-surface);
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
  background: rgba(var(--md-accent-rgb), 0.12);
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
  background: rgba(10, 16, 28, 0.75);
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.voice-card {
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  padding: 8px;
  cursor: pointer;
  background: rgba(10, 16, 28, 0.85);
  margin-bottom: 10px;
}

.voice-card .voice-name {
  font-size: 13px;
  font-weight: 600;
}

.voice-card .voice-meta {
  margin-top: 4px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
  display: flex;
  gap: 6px;
}

.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}

.count-label {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.count-label.warn {
  color: #b42318;
}

.count-hint {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.slider-row {
  display: grid;
  grid-template-columns: 48px 1fr 44px;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}

.slider-row input[type="range"] {
  width: 100%;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-top: 8px;
}

.role-note {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 4px;
}

.status-note {
  font-size: 11px;
  color: var(--md-on-surface-variant);
}

.status-error {
  margin-top: 6px;
  font-size: 11px;
  color: #b42318;
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

.field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--md-on-surface);
}

.field-row .label {
  min-width: 56px;
  color: var(--md-on-surface-variant);
}

.model-select {
  flex: 1;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  padding: 6px 8px;
  font-size: 12px;
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
  background: rgba(10, 16, 28, 0.75);
  border-radius: 10px;
  padding: 10px;
  line-height: 1.5;
  cursor: pointer;
  white-space: pre-wrap;
}

.prompt-editor,
.file-input {
  width: 100%;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  padding: 8px;
  resize: vertical;
}

.file-input {
  display: none;
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
  background: var(--md-surface-card);
  border-radius: 16px;
  border: 1px solid var(--md-stroke);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.voice-list,
.role-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow: auto;
}

.voice-option,
.role-option {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
  padding: 10px;
  text-align: left;
  cursor: pointer;
}

.voice-option.active,
.role-option.active {
  border-color: rgba(var(--md-accent-rgb), 0.6);
  box-shadow: 0 0 0 2px rgba(var(--md-accent-rgb), 0.2);
}

.voice-desc {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 4px;
}

.role-create {
  display: flex;
  gap: 8px;
  align-items: center;
}

.role-name {
  font-size: 13px;
  font-weight: 600;
}

.role-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-left: 6px;
}

.music-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.music-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 280px;
  overflow: auto;
}

.music-card {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 10px;
  align-items: center;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 10px;
  cursor: pointer;
  background: rgba(10, 16, 28, 0.85);
}

.music-card.active {
  border-color: rgba(var(--md-accent-rgb), 0.6);
  box-shadow: 0 0 0 2px rgba(var(--md-accent-rgb), 0.2);
}

.music-cover {
  width: 48px;
  height: 48px;
  border-radius: 10px;
}

.music-title {
  font-size: 13px;
  font-weight: 600;
}

.music-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: var(--md-on-surface-variant);
  margin-top: 4px;
}

.music-progress {
  height: 4px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.25);
  margin-top: 6px;
  overflow: hidden;
}

.music-progress-bar {
  height: 100%;
  background: var(--md-primary);
}

.music-upload {
  margin-bottom: 10px;
  display: flex;
  justify-content: flex-start;
}

.music-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.export-modal {
  width: min(520px, 92vw);
}

.export-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.export-section {
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(10, 16, 28, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.export-note {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.export-success {
  font-size: 12px;
  color: #22c55e;
}

.export-error {
  font-size: 12px;
  color: #f87171;
}

.export-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.export-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(10, 16, 28, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.export-file-meta {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: var(--md-on-surface);
}

.text-input {
  width: 100%;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  padding: 6px 8px;
  font-size: 12px;
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-on-surface);
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
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  box-shadow: var(--md-card-shadow);
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
  background: rgba(148, 163, 184, 0.45);
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
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(2, 6, 23, 0.95));
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(148, 163, 184, 0.25);
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
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  padding: 12px;
  box-shadow: var(--md-card-shadow-soft);
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
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface);
  cursor: pointer;
  font-size: 12px;
}

.view-btn.active {
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.8));
  color: #031019;
  border-color: rgba(var(--md-accent-rgb), 0.4);
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
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
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
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(10, 16, 28, 0.85);
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
