# 一站式视频生成平台 - 前后端接口文档

> 本文档基于PRD的6个功能模块，整理出前后端对齐的数据接口定义。

---

## 接口规范说明

### 通用说明

| 项目 | 说明 |
|-----|------|
| Base URL | `/api/v1` |
| 请求格式 | `application/json` |
| 响应格式 | `application/json` |
| 字符编码 | `UTF-8` |

### 统一响应格式

```typescript
// 成功响应
{
  "code": 0,           // 0表示成功
  "message": "success",
  "data": { ... }      // 业务数据
}

// 失败响应
{
  "code": 1001,        // 非0表示失败
  "message": "错误信息",
  "data": null
}
```

### 通用错误码

| 错误码 | 说明 |
|-------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 未登录 |
| 1003 | 无权限 |
| 1004 | 资源不存在 |
| 1005 | 资源已存在 |
| 1006 | 余额/配额不足 |
| 1007 | 文件上传失败 |
| 1008 | 生成任务失败 |
| 1009 | 导出任务失败 |
| 1010 | 邀请码无效 |

### 分页参数

```typescript
interface PageParams {
  page: number;      // 页码，从1开始
  page_size: number; // 每页数量
}
```

### 分页响应

```typescript
interface PageResponse<T> {
  list: T[];
  total: number;     // 总数
  page: number;      // 当前页
  page_size: number; // 每页数量
}
```

---

## 模块一：项目与任务管理

### 1.1 用户相关

#### 1.1.1 用户登录

```typescript
// POST /api/v1/auth/login
interface Request {
  username: string;  // 用户名
  password: string;  // 密码
}

interface Response {
  user: {
    id: string;
    username: string;
    email: string;
    avatar_url: string;
    user_type: 'personal' | 'team';
  };
  session_token: string;
  refresh_token: string;
  current_space: {
    type: 'personal' | 'team';
    space_id?: string;  // 团队空间ID
    space_name?: string;
  };
}
```

#### 1.1.2 获取当前用户信息

```typescript
// GET /api/v1/user/me
interface Response {
  id: string;
  username: string;
  email: string;
  avatar_url: string;
  user_type: 'personal' | 'team';
  quota_info: {
    daily_limit: number;
    used: number;
    reset_at: string;  // ISO 8601
  };
  settings: {
    language: string;
    theme: string;
  };
}
```

#### 1.1.3 更新用户信息

```typescript
// PUT /api/v1/user/me
interface Request {
  username?: string;
  avatar_url?: string;
  settings?: {
    language?: string;
    theme?: string;
  };
}
```

#### 1.1.4 刷新令牌

```typescript
// POST /api/v1/auth/refresh
interface Request {
  refresh_token: string;
}

interface Response {
  session_token: string;
  refresh_token: string;
}
```

### 1.2 团队空间相关

#### 1.2.1 加入团队空间

```typescript
// POST /api/v1/team/join
interface Request {
  invite_code: string;
}

interface Response {
  team_space: {
    id: string;
    name: string;
    role: 'admin' | 'editor' | 'viewer';
  };
}
```

#### 1.2.2 获取用户的团队空间列表

```typescript
// GET /api/v1/team/spaces
interface Response {
  list: Array<{
    id: string;
    name: string;
    logo_url: string;
    role: 'admin' | 'editor' | 'viewer';
    last_accessed: string;  // ISO 8601
  }>;
  recent_space_id?: string;  // 最近使用空间
}
```

#### 1.2.3 切换当前空间

```typescript
// POST /api/v1/team/switch
interface Request {
  space_type: 'personal' | 'team';
  space_id?: string;  // team时必填
}

interface Response {
  current_space: {
    type: 'personal' | 'team';
    space_id?: string;
    space_name?: string;
  };
}
```

### 1.3 项目/创作单元相关

#### 1.3.1 获取项目列表

```typescript
// GET /api/v1/projects
interface Query {
  space_type?: 'personal' | 'team';
  team_space_id?: string;  // team时必填
  status?: 'draft' | 'generating' | 'editing' | 'completed' | 'exported';
  keyword?: string;       // 搜索关键词
  page: number;
  page_size: number;
}

interface Response extends PageResponse<{
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'generating' | 'editing' | 'completed' | 'exported';
  stage: 'input' | 'generating' | 'editing' | 'completed';
  progress: number;
  tags: string[];
  input_config: {
    aspect_ratio: string;
    duration: number;
    language: string;
  };
  thumbnail_url?: string;
  updated_at: string;  // ISO 8601
  created_at: string;  // ISO 8601
}> {}
```

#### 1.3.2 创建项目

```typescript
// POST /api/v1/projects
interface Request {
  name?: string;  // 可选，系统可自动命名
  space_type?: 'personal' | 'team';
  team_space_id?: string;
}
```

> **说明**：实际上用户点击"提交生成"时才真正创建项目，此接口供团队空间显式创建使用。

#### 1.3.3 获取项目详情

```typescript
// GET /api/v1/projects/:project_id
interface Response {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'generating' | 'editing' | 'completed' | 'exported';
  stage: 'input' | 'generating' | 'editing' | 'completed';
  progress: number;
  tags: string[];
  input_config: {
    aspect_ratio: string;
    duration: number;
    language: string;
    subtitle_enabled: boolean;
  };
  metadata: {
    total_duration?: number;
    video_count?: number;
    export_count?: number;
  };
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}
```

#### 1.3.4 更新项目信息

```typescript
// PUT /api/v1/projects/:project_id
interface Request {
  name?: string;
  description?: string;
  tags?: string[];
}
```

#### 1.3.5 删除项目

```typescript
// DELETE /api/v1/projects/:project_id
// Response: { code: 0, message: "success" }
```

---

## 模块二：输入与素材导入

### 2.1 输入模式相关

#### 2.1.1 获取输入配置选项

```typescript
// GET /api/v1/input/options
interface Response {
  models: {
    text_to_image: Array<{
      id: string;
      name: string;
      display_name: string;
      icon_url: string;
      is_default: boolean;
    }>;
    image_to_image: Array<{
      id: string;
      name: string;
      display_name: string;
      icon_url: string;
    }>;
  };
  styles: Array<{
    id: string;
    name: string;
    preview_image_url: string;
    category: string;
  }>;
  aspect_ratios: Array<{
    ratio: string;     // "16:9", "9:16", "4:3", "2.35:1", "19:16"
    width: number;
    height: number;
    description: string;
    preview_url: string;
  }>;
  durations: Array<{
    label: string;     // "智能", "5秒", "10秒", ...
    value: number;     // 秒数，智能为-1
  }>;
  subjects: Array<{
    id: string;
    name: string;
    type: string;
  }>;
}
```

#### 2.1.2 提交创作输入

```typescript
// POST /api/v1/input/submit
interface Request {
  input_mode: 'general' | 'professional';
  input_type: 'text' | 'script' | 'storyboard';
  content: string;  // 文本内容
  attachments?: Array<{
    id: string;     // 已上传附件ID
    label?: string; // 用户标注
  }>;
  config: {
    text_to_image_model?: string;
    image_to_image_model?: string;
    style_id?: string;
    aspect_ratio: string;  // "16:9", "9:16", etc.
    duration_type: 'smart' | 'custom';
    duration_seconds?: number;
    subject_id?: string;
  };
}

interface Response {
  project_id: string;  // 创建或关联的项目ID
  status: 'submitted' | 'processing';
}
```

### 2.2 附件管理

#### 2.2.1 获取上传签名/配置

```typescript
// GET /api/v1/attachments/upload-config
interface Response {
  upload_url: string;     // 预签名URL（直传OSS）
  file_max_size: number;  // 字节
  allowed_types: string[]; // ["image/jpeg", "image/png", ...]
}
```

#### 2.2.2 上传附件

```typescript
// POST /api/v1/attachments
interface Request {
  file_name: string;
  file_type: string;
  file_category: 'image' | 'audio' | 'video' | 'document';
  file_size: number;
  file_url: string;  // 上传后返回的访问URL
  file_hash?: string;
}

interface Response {
  id: string;
  file_name: string;
  file_url: string;
  file_size: number;
  upload_status: 'uploading' | 'completed';
  created_at: string;
}
```

#### 2.2.3 更新附件标注

```typescript
// PUT /api/v1/attachments/:attachment_id
interface Request {
  label?: string;  // 如 "角色设计图"、"背景音乐" 等
  metadata?: Record<string, any>;
}
```

#### 2.2.4 删除附件

```typescript
// DELETE /api/v1/attachments/:attachment_id
```

#### 2.2.5 获取项目附件列表

```typescript
// GET /api/v1/projects/:project_id/attachments
interface Query {
  category?: 'image' | 'audio' | 'video' | 'document';
}

interface Response {
  list: Array<{
    id: string;
    file_name: string;
    file_type: string;
    file_category: string;
    file_url: string;
    file_size: number;
    label?: string;
    metadata: Record<string, any>;
    created_at: string;
  }>;
}
```

### 2.3 配置模板

#### 2.3.1 保存配置为模板

```typescript
// POST /api/v1/config-templates
interface Request {
  template_name: string;
  config_data: {
    model_id?: string;
    style_id?: string;
    aspect_ratio?: string;
    duration?: number;
    language?: string;
    subtitle_enabled?: boolean;
  };
  is_default?: boolean;
}
```

#### 2.3.2 获取配置模板列表

```typescript
// GET /api/v1/config-templates
interface Response {
  list: Array<{
    id: string;
    template_name: string;
    is_default: boolean;
    config_data: Record<string, any>;
    usage_count: number;
    created_at: string;
  }>;
}
```

---

## 模块三：生成素材管理

### 3.1 生成任务相关

#### 3.1.1 开始生成素材

```typescript
// POST /api/v1/generation/start
interface Request {
  project_id: string;
}

interface Response {
  material_package_id: string;
  status: 'generating';
}
```

#### 3.1.2 获取生成进度

```typescript
// GET /api/v1/generation/progress/:project_id
interface Response {
  material_package_id: string;
  status: 'generating' | 'completed' | 'failed';
  progress: number;  // 0-100
  current_step: string;  // 当前步骤描述
  tasks: Array<{
    task_type: 'storyline' | 'artstyle' | 'characters' | 'scenes' | 'storyboard';
    task_name: string;
    display_name: string;
    display_order: number;
    status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
    progress: number;
    error_message?: string;
  }>;
}
```

#### 3.1.3 重试生成任务

```typescript
// POST /api/v1/generation/retry/:task_id
interface Response {
  status: 'pending';
}
```

#### 3.1.4 跳过某个生成步骤

```typescript
// POST /api/v1/generation/skip/:task_id
```

### 3.2 素材包相关

#### 3.2.1 获取素材包列表

```typescript
// GET /api/v1/projects/:project_id/material-packages
interface Response {
  list: Array<{
    id: string;
    version: number;
    package_name: string;
    status: 'generating' | 'completed' | 'failed';
    is_active: boolean;
    summary?: string;
    generated_at?: string;
    created_at: string;
  }>;
}
```

#### 3.2.2 切换素材包

```typescript
// POST /api/v1/material-packages/:package_id/switch
// Response: { code: 0, message: "success" }
```

#### 3.2.3 重命名素材包

```typescript
// PUT /api/v1/material-packages/:package_id
interface Request {
  package_name: string;
}
```

#### 3.2.4 保存为新版本

```typescript
// POST /api/v1/material-packages/:package_id/save-new
interface Request {
  package_name?: string;  // 可选，系统自动命名
}

interface Response {
  new_package_id: string;
  version: number;
}
```

### 3.3 素材内容相关

#### 3.3.1 获取素材包详情

```typescript
// GET /api/v1/material-packages/:package_id
interface Response {
  id: string;
  version: string;
  package_name: string;
  status: string;
  materials: {
    storyline?: {
      id: string;
      title: string;
      content: string;
      summary: string;
      genre: string;
      tone: string;
      is_selected: boolean;
    };
    art_style?: {
      id: string;
      style_name: string;
      description: string;
      prompt_template: string;
      reference_image_url: string;
      is_selected: boolean;
    };
    characters?: Array<{
      id: string;
      character_name: string;
      character_type: 'protagonist' | 'supporting' | 'extras';
      description: string;
      personality: string[];
      appearance: string;
      voice_style?: string;
      images: Array<{
        id: string;
        image_type: 'front_view' | 'three_view' | 'detail';
        image_url: string;
        thumbnail_url: string;
        is_selected: boolean;
      }>;
      voices?: Array<{
        id: string;
        voice_name: string;
        voice_id: string;
        audio_sample_url: string;
        is_selected: boolean;
      }>;
      is_selected: boolean;
    }>;
    scenes?: Array<{
      id: string;
      scene_name: string;
      scene_type: 'indoor' | 'outdoor' | 'abstract';
      description: string;
      atmosphere: string;
      lighting: string;
      camera_angle: string;
      images: Array<{
        id: string;
        image_url: string;
        thumbnail_url: string;
        is_selected: boolean;
      }>;
      is_selected: boolean;
    }>;
    storyboards?: Array<{
      id: string;
      shot_number: number;
      shot_type: string;
      scene_id?: string;
      character_id?: string;
      description: string;
      dialogue?: string;
      action?: string;
      duration: number;
      camera_movement?: string;
      transition?: string;
      reference_image_url?: string;
      is_selected: boolean;
    }>;
  };
  summary?: string;
  created_at: string;
}
```

### 3.4 元素修改与候选

#### 3.4.1 修改文本元素

```typescript
// POST /api/v1/material-packages/:package_id/modify/text
interface Request {
  element_type: 'storyline' | 'artstyle' | 'character' | 'scene' | 'storyboard';
  element_id: string;
  modification_type: 'text_edit' | 'regenerate';
  user_prompt?: string;  // 用户修改意见
  new_content?: string;  // 直接编辑的新内容
}

interface Response {
  candidate_id: string;
  content: string;
  status: 'completed' | 'processing';
}
```

#### 3.4.2 重新生成图片

```typescript
// POST /api/v1/material-packages/:package_id/regenerate/image
interface Request {
  element_type: 'character' | 'scene';
  element_id: string;
  user_prompt: string;  // 修改意见
  prompt?: string;      // 新的生图提示词
}

interface Response {
  candidate_id: string;
  image_url: string;
  thumbnail_url: string;
  status: 'processing';
}
```

#### 3.4.3 切换音色

```typescript
// POST /api/v1/material-packages/:package_id/switch-voice
interface Request {
  element_type: 'character' | 'narration';
  element_id: string;
  voice_id: string;
}
```

#### 3.4.4 选择候选

```typescript
// POST /api/v1/material-packages/:package_id/select-candidate
interface Request {
  element_type: 'character' | 'scene';
  element_id: string;
  candidate_type: 'image' | 'voice';
  candidate_id: string;
}
```

#### 3.4.5 从资产库替换

```typescript
// POST /api/v1/material-packages/:package_id/replace-from-asset
interface Request {
  asset_type: 'character' | 'style' | 'voice';
  element_id: string;
  asset_id: string;
}
```

### 3.5 对话记录

#### 3.5.1 获取对话记录

```typescript
// GET /api/v1/projects/:project_id/conversations
interface Response {
  list: Array<{
    id: string;
    message_type: 'system' | 'user';
    message_content: string;
    context_data?: Record<string, any>;
    display_order: number;
    created_at: string;
  }>;
}
```

---

## 模块四：剪辑与编排

### 4.1 时间轴与片段

#### 4.1.1 获取时间轴数据

```typescript
// GET /api/v1/projects/:project_id/timeline
interface Response {
  project_id: string;
  total_duration: number;
  video_aspect_ratio: string;
  fps: number;
  clips: Array<{
    id: string;
    shot_number: number;
    clip_type: 'image' | 'video';
    duration: number;
    start_time: number;
    end_time: number;
    description: string;
    dialogue?: string;
    transition?: string;
    transition_duration?: number;
    selected_image_id?: string;
    selected_video_id?: string;
    thumbnail_url?: string;
    config: {
      crop_x?: number;
      crop_y?: number;
      crop_width?: number;
      crop_height?: number;
      zoom_level?: number;
      filter_type?: string;
    };
  }>;
}
```

#### 4.1.2 更新片段时长

```typescript
// PUT /api/v1/timeline-clips/:clip_id/duration
interface Request {
  duration: number;
}
```

#### 4.1.3 调整片段顺序

```typescript
// POST /api/v1/projects/:project_id/timeline/reorder
interface Request {
  clip_ids: string[];  // 按新顺序排列的片段ID
}
```

#### 4.1.4 删除片段

```typescript
// DELETE /api/v1/timeline-clips/:clip_id
```

### 4.2 分镜画面与视频生成

#### 4.2.1 获取分镜候选列表

```typescript
// GET /api/v1/timeline-clips/:clip_id/candidates
interface Query {
  candidate_type?: 'image' | 'video';
}

interface Response {
  images?: Array<{
    id: string;
    image_url: string;
    thumbnail_url: string;
    prompt: string;
    is_selected: boolean;
    created_at: string;
  }>;
  videos?: Array<{
    id: string;
    video_url: string;
    thumbnail_url: string;
    video_duration: number;
    model_id: string;
    model_name: string;
    prompt: string;
    quota_consumed: number;
    is_selected: boolean;
    generation_status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at: string;
  }>;
}
```

#### 4.2.2 重新生成分镜图片

```typescript
// POST /api/v1/timeline-clips/:clip_id/regenerate-image
interface Request {
  user_prompt: string;
  prompt?: string;
}

interface Response {
  candidate_id: string;
  status: 'processing';
  quota_consumed?: number;
}
```

#### 4.2.3 生成分镜视频

```typescript
// POST /api/v1/timeline-clips/:clip_id/generate-video
interface Request {
  model_id: string;
  prompt?: string;
}

interface Response {
  generation_id: string;
  estimated_duration: number;
  quota_consumed: number;
  status: 'pending';
}
```

#### 4.2.4 批量生成视频

```typescript
// POST /api/v1/projects/:project_id/generate-batch-videos
interface Request {
  model_id: string;
  clip_ids?: string[];  // 可选，不传则生成所有未生成视频的片段
}

interface Response {
  task_id: string;
  total_clips: number;
  total_quota: number;
  status: 'pending';
}
```

#### 4.2.5 获取批量生成进度

```typescript
// GET /api/v1/video-generation-tasks/:task_id
interface Response {
  task_id: string;
  model_id: string;
  model_name: string;
  total_clips: number;
  completed_clips: number;
  total_quota: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
}
```

#### 4.2.6 应用候选

```typescript
// POST /api/v1/timeline-clips/:clip_id/apply-candidate
interface Request {
  candidate_type: 'image' | 'video';
  candidate_id: string;
}
```

### 4.3 音频配置

#### 4.3.1 获取片段音频配置

```typescript
// GET /api/v1/timeline-clips/:clip_id/audio
interface Response {
  narration?: {
    id: string;
    text_content: string;
    voice_id?: string;
    voice_name?: string;
    audio_url?: string;
    speech_speed: number;
    volume: number;
    emotion?: string;
    generation_status: 'pending' | 'processing' | 'completed';
    is_custom_audio: boolean;
    custom_audio_url?: string;
  };
  dialogue?: Array<{
    id: string;
    character_id?: string;
    character_name?: string;
    text_content: string;
    voice_id?: string;
    voice_name?: string;
    audio_url?: string;
    generation_status: 'pending' | 'processing' | 'completed';
  }>;
}
```

#### 4.3.2 更新旁白

```typescript
// PUT /api/v1/timeline-clips/:clip_id/narration
interface Request {
  text_content: string;
  voice_id?: string;
  speech_speed?: number;
  volume?: number;
  emotion?: string;
}

interface Response {
  estimated_duration: number;
  generation_status: 'pending';
}
```

#### 4.3.3 旁白使用自定义音频

```typescript
// POST /api/v1/timeline-clips/:clip_id/narration/custom-audio
interface Request {
  audio_url: string;
}
```

#### 4.3.4 更新对话

```typescript
// PUT /api/v1/timeline-clips/:clip_id/dialogue/:dialogue_id
interface Request {
  text_content: string;
  voice_id?: string;
  speech_speed?: number;
  volume?: number;
  emotion?: string;
}
```

#### 4.3.5 获取项目BGM

```typescript
// GET /api/v1/projects/:project_id/bgm
interface Response {
  id?: string;
  audio_url?: string;
  music_name?: string;
  source?: 'ai_generated' | 'library' | 'uploaded';
  volume: number;
  is_loop: boolean;
  fade_in_duration: number;
  fade_out_duration: number;
  is_selected: boolean;
}
```

#### 4.3.6 更新项目BGM

```typescript
// PUT /api/v1/projects/:project_id/bgm
interface Request {
  audio_url?: string;
  music_name?: string;
  source?: 'ai_generated' | 'library' | 'uploaded';
  volume?: number;
  is_loop?: boolean;
  fade_in_duration?: number;
  fade_out_duration?: number;
}
```

#### 4.3.7 生成BGM候选

```typescript
// POST /api/v1/projects/:project_id/generate-bgm
interface Request {
  prompt?: string;
}

interface Response {
  candidate_id: string;
  audio_url: string;
  quota_consumed: number;
  status: 'processing';
}
```

### 4.4 画面编辑

#### 4.4.1 更新画面编辑配置

```typescript
// PUT /api/v1/timeline-clips/:clip_id/edit-config
interface Request {
  crop_x?: number;
  crop_y?: number;
  crop_width?: number;
  crop_height?: number;
  zoom_level?: number;
  pan_x?: number;
  pan_y?: number;
  rotation?: number;
  filter_type?: string;
  filter_intensity?: number;
  transform_params?: Record<string, any>;
}
```

---

## 模块五：导出与交付

### 5.1 导出任务

#### 5.1.1 创建导出任务

```typescript
// POST /api/v1/projects/:project_id/export
interface Request {
  task_name?: string;
  config: {
    resolution: '720p' | '1080p' | '4K';
    width: number;
    height: number;
    format: 'MP4' | 'MOV';
    aspect_ratio: string;
    fps?: number;
    subtitle?: {
      enabled: boolean;
      burn_in: boolean;
      format?: 'SRT' | 'VTT' | 'ASS';
      font_name?: string;
      font_size?: number;
      font_color?: string;
      position?: 'top' | 'bottom' | 'center';
      background_color?: string;
      background_opacity?: number;
    };
    cover?: {
      enabled: boolean;
      cover_type?: 'auto_generate' | 'custom' | 'from_clip';
      source_clip_id?: string;
      custom_image_url?: string;
      title_text?: string;
      subtitle_text?: string;
    };
  };
}

interface Response {
  export_task_id: string;
  estimated_duration?: number;  // 预计秒数
  status: 'pending';
}
```

#### 5.1.2 获取导出任务状态

```typescript
// GET /api/v1/export-tasks/:task_id
interface Response {
  id: string;
  project_id: string;
  task_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}
```

#### 5.1.3 取消导出任务

```typescript
// POST /api/v1/export-tasks/:task_id/cancel
```

### 5.2 导出文件

#### 5.2.1 获取导出文件列表

```typescript
// GET /api/v1/projects/:project_id/export-files
interface Response {
  list: Array<{
    id: string;
    file_type: 'video' | 'audio' | 'subtitle' | 'cover';
    file_name: string;
    file_url: string;
    file_size: number;
    duration?: number;
    resolution?: string;
    format?: string;
    download_count: number;
    expires_at?: string;
    created_at: string;
  }>;
}
```

#### 5.2.2 下载文件（获取临时下载链接）

```typescript
// GET /api/v1/export-files/:file_id/download-url
interface Response {
  download_url: string;  // 带签名的临时下载链接
  expires_at: string;
}
```

### 5.3 导出历史

#### 5.3.1 获取导出历史

```typescript
// GET /api/v1/projects/:project_id/export-history
interface Query extends PageParams {}

interface Response extends PageResponse<{
  export_task_id: string;
  export_config: Record<string, any>;
  file_summary: {
    video_count: number;
    total_size: number;
  };
  status: string;
  exported_at: string;
}> {}
```

---

## 模块六：资产库

### 6.1 角色库

#### 6.1.1 获取角色资产列表

```typescript
// GET /api/v1/assets/characters
interface Query {
  category_id?: string;
  character_type?: 'male' | 'female' | 'other';
  keyword?: string;
  is_preset?: boolean;
  page?: number;
  page_size?: number;
}

interface Response extends PageResponse<{
  id: string;
  character_name: string;
  character_type: string;
  description: string;
  personality: string[];
  appearance: string;
  image_url: string;
  thumbnail_url: string;
  images: Record<string, any>;
  is_preset: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}> {}
```

#### 6.1.2 创建角色资产

```typescript
// POST /api/v1/assets/characters
interface Request {
  character_name: string;
  character_type: 'male' | 'female' | 'other';
  description?: string;
  personality?: string[];
  appearance?: string;
  image_url: string;
  prompt_template?: string;
}
```

#### 6.1.3 更新角色资产

```typescript
// PUT /api/v1/assets/characters/:asset_id
interface Request {
  character_name?: string;
  description?: string;
  personality?: string[];
  appearance?: string;
  image_url?: string;
}
```

#### 6.1.4 删除角色资产

```typescript
// DELETE /api/v1/assets/characters/:asset_id
```

### 6.2 风格库

#### 6.2.1 获取风格资产列表

```typescript
// GET /api/v1/assets/styles
interface Query {
  category_id?: string;
  keyword?: string;
  is_preset?: boolean;
  page?: number;
  page_size?: number;
}

interface Response extends PageResponse<{
  id: string;
  style_name: string;
  description?: string;
  prompt_template: string;
  preview_image_url: string;
  thumbnail_url: string;
  color_palette: Record<string, any>;
  visual_keywords: string[];
  is_preset: boolean;
  usage_count: number;
  created_at: string;
}> {}
```

#### 6.2.2 创建风格资产

```typescript
// POST /api/v1/assets/styles
interface Request {
  style_name: string;
  description?: string;
  prompt_template: string;
  preview_image_url?: string;
  visual_keywords?: string[];
  color_palette?: Record<string, any>;
}
```

#### 6.2.3 更新/删除风格资产

```typescript
// PUT /api/v1/assets/styles/:asset_id
// DELETE /api/v1/assets/styles/:asset_id
// 同角色资产结构
```

### 6.3 音色库

#### 6.3.1 获取音色资产列表

```typescript
// GET /api/v1/assets/voices
interface Query {
  voice_type?: 'narration' | 'dialogue';
  gender?: 'male' | 'female' | 'neutral';
  language?: string;
  keyword?: string;
  is_preset?: boolean;
  page?: number;
  page_size?: number;
}

interface Response extends PageResponse<{
  id: string;
  voice_name: string;
  voice_type: 'narration' | 'dialogue';
  voice_id?: string;
  description?: string;
  audio_sample_url: string;
  gender?: string;
  age_range?: string;
  tone?: string;
  language?: string;
  is_preset: boolean;
  usage_count: number;
  created_at: string;
}> {}
```

#### 6.3.2 创建音色资产

```typescript
// POST /api/v1/assets/voices
interface Request {
  voice_name: string;
  voice_type: 'narration' | 'dialogue';
  voice_id?: string;
  description?: string;
  audio_sample_url: string;
  gender?: string;
  age_range?: string;
  tone?: string;
  language?: string;
}
```

### 6.4 音乐库

#### 6.4.1 获取音乐资产列表

```typescript
// GET /api/v1/assets/music
interface Query {
  genre?: string;
  mood?: string;
  keyword?: string;
  is_preset?: boolean;
  page?: number;
  page_size?: number;
}

interface Response extends PageResponse<{
  id: string;
  music_name: string;
  description?: string;
  audio_url: string;
  duration: number;
  genre?: string;
  mood?: string;
  tempo?: string;
  instruments?: string[];
  thumbnail_url?: string;
  is_preset: boolean;
  usage_count: number;
  created_at: string;
}> {}
```

#### 6.4.2 创建音乐资产

```typescript
// POST /api/v1/assets/music
interface Request {
  music_name: string;
  description?: string;
  audio_url: string;
  duration: number;
  genre?: string;
  mood?: string;
  tempo?: string;
  instruments?: string[];
}
```

### 6.5 资产通用操作

#### 6.5.1 搜索资产（跨类型）

```typescript
// GET /api/v1/assets/search
interface Query {
  keyword: string;
  asset_types?: ('character' | 'style' | 'voice' | 'music')[];
  page?: number;
  page_size?: number;
}

interface Response {
  results: {
    characters?: PageResponse<any>;
    styles?: PageResponse<any>;
    voices?: PageResponse<any>;
    music?: PageResponse<any>;
  };
}
```

#### 6.5.2 批量删除资产

```typescript
// POST /api/v1/assets/batch-delete
interface Request {
  asset_type: 'character' | 'style' | 'voice' | 'music';
  asset_ids: string[];
}
```

#### 6.5.3 获取资产分类

```typescript
// GET /api/v1/assets/categories
interface Query {
  category_type: 'character' | 'style' | 'voice';
}

interface Response {
  list: Array<{
    id: string;
    name: string;
    display_order: number;
    parent_id?: string;
    icon_url?: string;
  }>;
}
```

---

## WebSocket 事件订阅（实时通知）

### 连接

```typescript
// WS连接地址：wss://api.example.com/ws
// 连接时携带认证token
const ws = new WebSocket('wss://api.example.com/ws?token=xxx');
```

### 订阅项目事件

```typescript
// 客户端发送
{
  "action": "subscribe",
  "channel": "project",  // 订阅项目事件
  "project_id": "xxx"
}
```

### 服务端推送事件

#### 生成进度更新

```typescript
{
  "event": "generation.progress",
  "project_id": "xxx",
  "data": {
    "material_package_id": "xxx",
    "status": "generating",
    "progress": 60,
    "current_step": "正在生成角色形象..."
  }
}
```

#### 生成任务完成

```typescript
{
  "event": "generation.completed",
  "project_id": "xxx",
  "data": {
    "material_package_id": "xxx",
    "package_name": "海滨故事 v1",
    "materials": { ... }
  }
}
```

#### 视频生成进度

```typescript
{
  "event": "video.progress",
  "project_id": "xxx",
  "data": {
    "clip_id": "xxx",
    "shot_number": 3,
    "status": "processing",
    "progress": 80
  }
}
```

#### 导出任务完成

```typescript
{
  "event": "export.completed",
  "project_id": "xxx",
  "data": {
    "export_task_id": "xxx",
    "files": [
      {
        "file_type": "video",
        "file_name": "海滨故事.mp4",
        "file_url": "https://...",
        "file_size": 12345678
      }
    ]
  }
}
```

#### 配额不足提醒

```typescript
{
  "event": "quota.insufficient",
  "project_id": "xxx",
  "data": {
    "required": 10,
    "remaining": 3
  }
}
```

---

## 数据模型索引

### User 用户

```typescript
interface User {
  id: string;
  username: string;
  email: string;
  avatar_url?: string;
  user_type: 'personal' | 'team';
  quota_info: {
    daily_limit: number;
    used: number;
    reset_at: string;
  };
  created_at: string;
  updated_at: string;
}
```

### Project 项目/创作单元

```typescript
interface Project {
  id: string;
  user_id: string;
  team_space_id?: string;
  name: string;
  description?: string;
  status: 'draft' | 'generating' | 'editing' | 'completed' | 'exported';
  stage: 'input' | 'generating' | 'editing' | 'completed';
  progress: number;
  tags: string[];
  input_config: InputConfig;
  metadata: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

interface InputConfig {
  text_to_image_model?: string;
  image_to_image_model?: string;
  style_id?: string;
  aspect_ratio: string;
  duration_type: 'smart' | 'custom';
  duration_seconds?: number;
  subject_id?: string;
  language?: string;
  subtitle_enabled?: boolean;
}
```

### MaterialPackage 素材包

```typescript
interface MaterialPackage {
  id: string;
  project_id: string;
  version: number;
  package_name: string;
  status: 'generating' | 'completed' | 'failed';
  is_active: boolean;
  summary?: string;
  materials: Materials;
  generated_at?: string;
  created_at: string;
}

interface Materials {
  storyline?: Storyline;
  art_style?: ArtStyle;
  characters?: Character[];
  scenes?: Scene[];
  storyboards?: Storyboard[];
}
```

### TimelineClip 时间轴片段

```typescript
interface TimelineClip {
  id: string;
  project_id: string;
  shot_number: number;
  clip_type: 'image' | 'video';
  duration: number;
  start_time: number;
  end_time: number;
  description: string;
  dialogue?: string;
  transition?: string;
  transition_duration?: number;
  selected_image_id?: string;
  selected_video_id?: string;
  config: EditConfig;
}

interface EditConfig {
  crop_x?: number;
  crop_y?: number;
  crop_width?: number;
  crop_height?: number;
  zoom_level?: number;
  pan_x?: number;
  pan_y?: number;
  rotation?: number;
  filter_type?: string;
  filter_intensity?: number;
}
```

### Asset 资产

```typescript
interface Asset {
  id: string;
  user_id: string;
  asset_type: 'character' | 'style' | 'voice' | 'music';
  asset_name: string;
  description?: string;
  content_url?: string;
  thumbnail_url?: string;
  prompt_template?: string;
  attributes: Record<string, any>;
  is_preset: boolean;
  is_public: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}
```

---

## 接口使用流程示例

### 完整创作流程

```typescript
// 1. 用户登录
POST /api/v1/auth/login
→ { session_token, user, current_space }

// 2. 获取输入配置选项
GET /api/v1/input/options
→ { models, styles, aspect_ratios, durations }

// 3. 上传参考图
POST /api/v1/attachments
→ { id, file_url }

// 4. 提交创作输入
POST /api/v1/input/submit
→ { project_id, status }

// 5. 开始生成素材
POST /api/v1/generation/start
→ { material_package_id, status }

// 6. 轮询获取生成进度（或订阅WebSocket）
GET /api/v1/generation/progress/:project_id
→ { progress, tasks }

// 7. 获取素材包详情
GET /api/v1/material-packages/:package_id
→ { materials }

// 8. 修改某个角色图片
POST /api/v1/material-packages/:package_id/regenerate/image
→ { candidate_id, status }

// 9. 保存为新版本
POST /api/v1/material-packages/:package_id/save-new
→ { new_package_id, version }

// 10. 进入剪辑，获取时间轴
GET /api/v1/projects/:project_id/timeline
→ { total_duration, clips }

// 11. 选中片段，生成分镜视频
POST /api/v1/timeline-clips/:clip_id/generate-video
→ { generation_id, quota_consumed }

// 12. 配置旁白
PUT /api/v1/timeline-clips/:clip_id/narration
→ { estimated_duration }

// 13. 配置BGM
PUT /api/v1/projects/:project_id/bgm
→ { success }

// 14. 创建导出任务
POST /api/v1/projects/:project_id/export
→ { export_task_id, estimated_duration }

// 15. 轮询导出进度
GET /api/v1/export-tasks/:task_id
→ { status, progress }

// 16. 导出完成，获取下载链接
GET /api/v1/export-files/:file_id/download-url
→ { download_url }
```

### 资产复用流程

```typescript
// 1. 搜索角色
GET /api/v1/assets/characters?keyword=少女
→ { list: [...] }

// 2. 在生成素材时引用
POST /api/v1/input/submit
{
  config: {
    subject_id: 'character-asset-id'  // 引用资产库角色
  }
}

// 3. 在素材管理中替换
POST /api/v1/material-packages/:package_id/replace-from-asset
{
  asset_type: 'character',
  element_id: 'xxx',
  asset_id: 'character-asset-id'
}

// 4. 在剪辑中切换音色
PUT /api/v1/timeline-clips/:clip_id/narration
{
  voice_id: 'voice-asset-id'  // 引用音色库
}
```

---

## 附录：枚举值定义

### 状态枚举

```typescript
enum ProjectStatus {
  DRAFT = 'draft',
  GENERATING = 'generating',
  EDITING = 'editing',
  COMPLETED = 'completed',
  EXPORTED = 'exported'
}

enum ProjectStage {
  INPUT = 'input',
  GENERATING = 'generating',
  EDITING = 'editing',
  COMPLETED = 'completed'
}

enum GenerationTaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

enum MaterialPackageStatus {
  GENERATING = 'generating',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

enum ExportStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}
```

### 类型枚举

```typescript
enum ClipType {
  IMAGE = 'image',
  VIDEO = 'video'
}

enum AssetType {
  CHARACTER = 'character',
  STYLE = 'style',
  VOICE = 'voice',
  MUSIC = 'music'
}

enum FileCategory {
  IMAGE = 'image',
  AUDIO = 'audio',
  VIDEO = 'video',
  DOCUMENT = 'document'
}
```

### 配置枚举

```typescript
enum AspectRatio {
  R16_9 = '16:9',
  R4_3 = '4:3',
  R235_1 = '2.35:1',
  R19_16 = '19:16'
}

enum Resolution {
  P720 = '720p',
  P1080 = '1080p',
  P4K = '4K'
}

enum VideoFormat {
  MP4 = 'MP4',
  MOV = 'MOV'
}

enum SubtitleFormat {
  SRT = 'SRT',
  VTT = 'VTT',
  ASS = 'ASS'
}
```

---

> 文档版本：v1.0
> 更新时间：2024年
> 维护者：产品技术团队
