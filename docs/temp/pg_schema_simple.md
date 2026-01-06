# 一站式视频生成平台 - MVP数据库设计（精简版）

本文档是MVP（最小可行产品）版本的数据库设计，从完整版的60+张表精简至**15张核心表**，保留全部功能且可扩展。

---

## 设计原则

1. **JSONB优先**：将配置类、非核心查询字段合并为JSONB类型
2. **合并同类表**：将多个候选表合并为统一的candidates表
3. **延迟非核心功能**：配额、详细历史、版本管理等在JSONB中简化存储
4. **保留扩展性**：表结构设计便于后续拆分

---

## 数据库表设计（15张核心表）

### 1. users - 用户表

用户和团队空间统一管理，MVP阶段简化团队管理。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 用户唯一标识 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| avatar_url | VARCHAR(500) | | 头像URL |
| settings | JSONB | | 用户设置(语言、主题等) |
| quota_info | JSONB | | 配额信息 {daily_limit, used, reset_at} |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    settings JSONB DEFAULT '{}',
    quota_info JSONB DEFAULT '{"daily_limit": 10, "used": 0, "reset_at": null}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

> **扩展说明**：后续需团队功能时，可增加 `team_spaces` 表和 `team_members` 表。

---

### 2. projects - 项目/创作单元表

核心表，贯穿整个创作流程。替代完整版的 `creative_units` + `editing_projects`。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 项目唯一标识 |
| user_id | UUID | FK->users | 创建用户ID |
| name | VARCHAR(200) | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| status | VARCHAR(20) | NOT NULL | 状态: draft/generating/editing/completed/exported |
| stage | VARCHAR(20) | NOT NULL | 当前阶段 |
| progress | INTEGER | | 进度 0-100 |
| tags | TEXT[] | | 标签 |
| input_config | JSONB | | 输入配置(画幅、时长、风格等) |
| metadata | JSONB | | 扩展元数据 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'editing', 'completed', 'exported')),
    stage VARCHAR(20) NOT NULL DEFAULT 'input' CHECK (stage IN ('input', 'generating', 'editing', 'completed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    tags TEXT[] DEFAULT '{}',
    input_config JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created ON projects(created_at DESC);
```

> **扩展说明**：`input_config` 存储输入配置（风格、模型、画幅、时长等），后续可拆分为独立表。

---

### 3. attachments - 附件/文件表

统一管理所有上传文件（图片、视频、音频、文档）。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 附件唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_type | VARCHAR(50) | NOT NULL | 文件类型 |
| file_category | VARCHAR(20) | NOT NULL | 分类: image/audio/video/document |
| file_url | VARCHAR(500) | NOT NULL | 文件URL |
| file_size | BIGINT | NOT NULL | 文件大小(字节) |
| metadata | JSONB | | 元数据(标注、用途等) |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_category VARCHAR(20) NOT NULL CHECK (file_category IN ('image', 'audio', 'video', 'document')),
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_project ON attachments(project_id);
CREATE INDEX idx_attachments_category ON attachments(file_category);
```

> **扩展说明**：`metadata` 字段存储附件标注、用途等信息，替代 `attachment_labels` 表。

---

### 4. material_packages - 素材包表

存储每次生成的素材版本，包含故事、角色、场景、分镜等全部生成内容。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 素材包唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| version | INTEGER | NOT NULL | 版本号 |
| status | VARCHAR(20) | NOT NULL | 状态: generating/completed/failed |
| is_active | BOOLEAN | NOT NULL | 是否当前激活版本 |
| summary | TEXT | | 生成摘要 |
| materials | JSONB | NOT NULL | 素材数据(核心) |
| generated_at | TIMESTAMP | | 生成完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE material_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'failed')),
    is_active BOOLEAN NOT NULL DEFAULT false,
    summary TEXT,
    materials JSONB NOT NULL DEFAULT '{}',
    generated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, version)
);

CREATE INDEX idx_material_packages_project ON material_packages(project_id);
CREATE INDEX idx_material_packages_active ON material_packages(is_active);
```

**materials 字段结构**：
```json
{
  "storyline": { "title": "", "content": "", "genre": "", "tone": "" },
  "art_style": { "name": "", "prompt": "", "preview_url": "" },
  "characters": [
    { "id": "uuid", "name": "", "type": "", "description": "", "images": [], "voice": {} }
  ],
  "scenes": [
    { "id": "uuid", "name": "", "type": "", "description": "", "images": [] }
  ],
  "storyboards": [
    { "id": "uuid", "shot_number": 1, "description": "", "dialogue": "", "duration": 5.0 }
  ],
  "generation_tasks": [...]  // 生成任务进度
}
```

> **扩展说明**：`materials` JSONB字段存储所有生成素材，后续可根据需要拆分为独立表。

---

### 5. generation_tasks - 生成任务表

追踪素材生成过程中的各个任务步骤。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 任务唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| task_type | VARCHAR(50) | NOT NULL | 任务类型 |
| task_name | VARCHAR(100) | NOT NULL | 任务名称 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| status | VARCHAR(20) | NOT NULL | 状态: pending/in_progress/completed/failed |
| progress | INTEGER | | 进度 0-100 |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE generation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('storyline', 'artstyle', 'characters', 'scenes', 'storyboard')),
    task_name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generation_tasks_package ON generation_tasks(material_package_id);
CREATE INDEX idx_generation_tasks_status ON generation_tasks(status);
```

---

### 6. candidates - 素材候选表

统一存储所有素材的候选版本（图片、视频、音色等），替代多个候选表。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| target_type | VARCHAR(20) | NOT NULL | 目标类型: character/scene/clip |
| target_id | VARCHAR(50) | NOT NULL | 目标元素ID |
| candidate_type | VARCHAR(20) | NOT NULL | 候选类型: image/video/voice |
| content_url | VARCHAR(500) | NOT NULL | 内容URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| prompt | TEXT | | 生成提示词 |
| metadata | JSONB | | 扩展数据(时长、音色参数等) |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    material_package_id UUID REFERENCES material_packages(id) ON DELETE SET NULL,
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('character', 'scene', 'clip', 'bgm')),
    target_id VARCHAR(50) NOT NULL,
    candidate_type VARCHAR(20) NOT NULL CHECK (candidate_type IN ('image', 'video', 'voice')),
    content_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    prompt TEXT,
    metadata JSONB DEFAULT '{}',
    is_selected BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidates_project ON candidates(project_id);
CREATE INDEX idx_candidates_target ON candidates(target_type, target_id);
CREATE INDEX idx_candidates_selected ON candidates(is_selected);
```

> **扩展说明**：合并了 `character_image_candidates`、`scene_image_candidates`、`clip_video_candidates`、`clip_image_candidates`、`bgm_candidates` 等表。

---

### 7. timeline_clips - 时间轴片段表

剪辑阶段的时间轴片段数据。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 片段唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| shot_number | INTEGER | NOT NULL | 镜头序号 |
| clip_type | VARCHAR(20) | NOT NULL | 类型: image/video |
| duration | DECIMAL(5,2) | NOT NULL | 时长(秒) |
| start_time | DECIMAL(10,2) | NOT NULL | 开始时间(秒) |
| end_time | DECIMAL(10,2) | NOT NULL | 结束时间(秒) |
| description | TEXT | NOT NULL | 镜头描述 |
| dialogue | TEXT | | 台词/旁白 |
| transition | VARCHAR(50) | | 转场效果 |
| selected_image_id | UUID | FK->candidates | 选中的图片候选ID |
| selected_video_id | UUID | FK->candidates | 选中的视频候选ID |
| config | JSONB | | 扩展配置 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE timeline_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE SET NULL,
    shot_number INTEGER NOT NULL,
    clip_type VARCHAR(20) NOT NULL CHECK (clip_type IN ('image', 'video')),
    duration DECIMAL(5,2) NOT NULL DEFAULT 5.0,
    start_time DECIMAL(10,2) NOT NULL DEFAULT 0,
    end_time DECIMAL(10,2) NOT NULL,
    description TEXT NOT NULL,
    dialogue TEXT,
    transition VARCHAR(50),
    selected_image_id UUID REFERENCES candidates(id) ON DELETE SET NULL,
    selected_video_id UUID REFERENCES candidates(id) ON DELETE SET NULL,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, shot_number)
);

CREATE INDEX idx_timeline_clips_project ON timeline_clips(project_id);
CREATE INDEX idx_timeline_clips_shot ON timeline_clips(project_id, shot_number);
```

> **扩展说明**：合并了完整版的 `timeline_clips` + `clip_edit_configs`，`config` 字段存储裁剪、缩放等编辑参数。

---

### 8. audio_configs - 音频配置表

统一管理旁白、对话、背景音乐配置。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| clip_id | UUID | FK->timeline_clips | 片段ID(NULL表示BGM) |
| audio_type | VARCHAR(20) | NOT NULL | 类型: narration/dialogue/bgm |
| text_content | TEXT | | 文本内容(旁白/对话) |
| voice_id | VARCHAR(50) | | 音色ID |
| voice_name | VARCHAR(100) | | 音色名称 |
| audio_url | VARCHAR(500) | | 生成音频URL |
| source | VARCHAR(20) | | 来源: generated/library/uploaded |
| volume | INTEGER | NOT NULL | 音量 0-100 |
| speech_speed | DECIMAL(3,2) | | 语速 |
| emotion | VARCHAR(50) | | 情绪 |
| metadata | JSONB | | 扩展配置 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE audio_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    clip_id UUID REFERENCES timeline_clips(id) ON DELETE CASCADE,
    audio_type VARCHAR(20) NOT NULL CHECK (audio_type IN ('narration', 'dialogue', 'bgm')),
    text_content TEXT,
    voice_id VARCHAR(50),
    voice_name VARCHAR(100),
    audio_url VARCHAR(500),
    source VARCHAR(20) CHECK (source IN ('generated', 'library', 'uploaded')),
    volume INTEGER NOT NULL DEFAULT 80 CHECK (volume >= 0 AND volume <= 100),
    speech_speed DECIMAL(3,2) DEFAULT 1.0,
    emotion VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audio_configs_project ON audio_configs(project_id);
CREATE INDEX idx_audio_configs_clip ON audio_configs(clip_id);
CREATE INDEX idx_audio_configs_type ON audio_configs(audio_type);
```

> **扩展说明**：合并了 `clip_narrations`、`clip_dialogues`、`background_music` 三张表。

---

### 9. export_tasks - 导出任务表

管理视频导出任务。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 导出任务唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| task_name | VARCHAR(200) | NOT NULL | 任务名称 |
| status | VARCHAR(20) | NOT NULL | 状态: pending/processing/completed/failed |
| progress | INTEGER | | 进度 0-100 |
| export_config | JSONB | NOT NULL | 导出配置 |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE export_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    export_config JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_tasks_project ON export_tasks(project_id);
CREATE INDEX idx_export_tasks_status ON export_tasks(status);
CREATE INDEX idx_export_tasks_created ON export_tasks(created_at DESC);
```

**export_config 字段结构**：
```json
{
  "resolution": "1080p",
  "width": 1920,
  "height": 1080,
  "format": "MP4",
  "aspect_ratio": "16:9",
  "fps": 30,
  "subtitle": {
    "enabled": true,
    "burn_in": false,
    "format": "SRT"
  },
  "cover": {
    "enabled": false,
    "type": "auto_generate"
  }
}
```

> **扩展说明**：`export_config` 合并了 `export_configs`、`subtitle_export_configs`、`cover_configs` 三张表。

---

### 10. export_files - 导出文件表

存储导出产生的文件信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 文件唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| file_type | VARCHAR(20) | NOT NULL | 类型: video/audio/subtitle/cover |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_url | VARCHAR(500) | NOT NULL | 文件URL |
| file_size | BIGINT | NOT NULL | 文件大小(字节) |
| duration | DECIMAL(10,2) | | 时长(秒) |
| metadata | JSONB | | 扩展信息 |
| download_count | INTEGER | NOT NULL | 下载次数 |
| expires_at | TIMESTAMP | | 过期时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE export_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('video', 'audio', 'subtitle', 'cover')),
    file_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    duration DECIMAL(10,2),
    metadata JSONB DEFAULT '{}',
    download_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_files_task ON export_files(export_task_id);
```

---

### 11. assets - 资产库表

统一管理角色、风格、音色、音乐资产。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 资产唯一标识 |
| user_id | UUID | FK->users | 所有者用户ID |
| asset_type | VARCHAR(20) | NOT NULL | 类型: character/style/voice/music |
| asset_name | VARCHAR(200) | NOT NULL | 资产名称 |
| description | TEXT | | 描述 |
| content_url | VARCHAR(500) | | 内容URL(图片/音频) |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| prompt_template | TEXT | | Prompt模板(风格/角色) |
| attributes | JSONB | NOT NULL | 类型特定属性 |
| is_preset | BOOLEAN | NOT NULL | 是否预设 |
| is_public | BOOLEAN | NOT NULL | 是否公开 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('character', 'style', 'voice', 'music')),
    asset_name VARCHAR(200) NOT NULL,
    description TEXT,
    content_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    prompt_template TEXT,
    attributes JSONB NOT NULL DEFAULT '{}',
    is_preset BOOLEAN NOT NULL DEFAULT false,
    is_public BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assets_user ON assets(user_id);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_preset ON assets(is_preset);
CREATE INDEX idx_assets_usage ON assets(usage_count DESC);
```

**attributes 字段按类型存储不同数据**：
- **character**: `{ "gender": "male", "personality": [], "images": [] }`
- **style**: `{ "preview_url": "", "keywords": [], "color_palette": [] }`
- **voice**: `{ "voice_id": "", "gender": "male", "age_range": "young", "language": "zh" }`
- **music**: `{ "duration": 120, "genre": "", "mood": "", "tempo": "" }`

> **扩展说明**：合并了 `character_assets`、`style_assets`、`voice_assets`、`music_assets` 四张表。

---

### 12. conversations - 对话/消息记录表

记录系统与用户的对话历史。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 消息唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| message_type | VARCHAR(20) | NOT NULL | 类型: system/user |
| message_content | TEXT | NOT NULL | 消息内容 |
| context_data | JSONB | | 上下文数据 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    material_package_id UUID REFERENCES material_packages(id) ON DELETE SET NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('system', 'user')),
    message_content TEXT NOT NULL,
    context_data JSONB,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_project ON conversations(project_id);
```

---

### 13. modifications - 元素修改记录表

记录素材的修改历史。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| project_id | UUID | FK->projects | 项目ID |
| element_type | VARCHAR(50) | NOT NULL | 元素类型 |
| element_id | VARCHAR(50) | NOT NULL | 元素ID |
| element_name | VARCHAR(200) | | 元素名称 |
| modification_type | VARCHAR(50) | NOT NULL | 修改类型 |
| user_prompt | TEXT | | 用户修改意见 |
| result_data | JSONB | | 修改结果数据 |
| created_by | UUID | FK->users | 修改用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    element_name VARCHAR(200),
    modification_type VARCHAR(50) NOT NULL,
    user_prompt TEXT,
    result_data JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_modifications_project ON modifications(project_id);
CREATE INDEX idx_modifications_element ON modifications(element_type, element_id);
```

---

### 14. sessions - 用户会话表

管理用户登录会话。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 会话ID |
| user_id | UUID | FK->users | 用户ID |
| session_token | VARCHAR(255) | NOT NULL, UNIQUE | 会话令牌 |
| refresh_token | VARCHAR(255) | | 刷新令牌 |
| expires_at | TIMESTAMP | NOT NULL | 过期时间 |
| last_activity | TIMESTAMP | NOT NULL | 最后活动时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
```

---

### 15. operations - 操作日志表（可选）

记录所有关键操作，用于审计和调试。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 日志唯一标识 |
| user_id | UUID | FK->users | 操作用户ID |
| operation_type | VARCHAR(50) | NOT NULL | 操作类型 |
| target_type | VARCHAR(50) | NOT NULL | 目标类型 |
| target_id | UUID | | 目标ID |
| description | TEXT | | 操作描述 |
| request_data | JSONB | | 请求参数 |
| response_data | JSONB | | 响应数据 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    operation_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID,
    description TEXT,
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operations_user ON operations(user_id);
CREATE INDEX idx_operations_target ON operations(target_type, target_id);
CREATE INDEX idx_operations_created ON operations(created_at DESC);
```

---

## 表关系图

```
users ─────┬──── sessions
          │
          ├──── projects ───┬──── attachments
          │                 ├──── material_packages ───── generation_tasks
          │                 ├──── candidates
          │                 ├──── timeline_clips ───── audio_configs
          │                 ├──── export_tasks ───── export_files
          │                 ├──── conversations
          │                 └──── modifications
          │
          └──── assets (资产库)
```

---

## MVP vs 完整版对照表

| 完整版表数量 | MVP版表数量 | 合并说明 |
|------------|------------|---------|
| 60+ | 15 | 精简约75% |
| user_sessions, space_usage_history | sessions | 会话管理简化 |
| user_quotas, team_quotas | users.quota_info | 配额存JSONB |
| team_spaces, team_members | - | MVP不支持团队 |
| creative_units, editing_projects | projects | 合并项目表 |
| task_collaborators, task_stage_history | - | 暂不支持协作 |
| creative_inputs, input_configs, model_configs, style_configs, aspect_ratio_configs, duration_configs, subject_configs, user_config_templates | projects.input_config | 配置统一存JSONB |
| attachments, attachment_labels | attachments | 标签存metadata |
| material_packages, material_package_history | material_packages | 历史暂不追踪 |
| generation_tasks | generation_tasks | 保持 |
| storylines, art_styles, characters, scenes, storyboards | material_packages.materials | 素材存JSONB |
| character_image_candidates, character_voice_candidates, scene_image_candidates, clip_image_candidates, clip_video_candidates, bgm_candidates | candidates | 统一候选表 |
| clip_narrations, clip_dialogues, background_music | audio_configs | 统一音频配置 |
| clip_edit_configs | timeline_clips.config | 编辑配置存JSONB |
| editing_projects | projects | 已合并 |
| editing_history | operations | 统一日志表 |
| export_configs, subtitle_export_configs, cover_configs | export_tasks.export_config | 导出配置存JSONB |
| subtitle_contents | export_files.metadata | 字幕内容存JSONB |
| export_history, download_records | export_files + operations | 简化追踪 |
| character_assets, style_assets, voice_assets, music_assets | assets | 统一资产表 |
| character_asset_versions, style_asset_versions, voice_asset_versions | - | 暂不支持版本 |
| character_usage_records, style_usage_records, voice_usage_records, music_usage_records | assets.usage_count | 计数字段 |
| asset_favorites, asset_tags, asset_tag_relations | - | MVP暂不支持 |
| system_conversations | conversations | 重命名简化 |
| element_modifications | modifications | 重命名简化 |
| preset_styles | assets(is_preset=true) | 预设资产 |

---

## 数据流向（MVP）

```
用户创建项目
    ↓
projects.input_config ← 用户输入配置
    ↓
attachments ← 用户上传文件
    ↓
material_packages.materials ← 生成素材存储
    ↓
candidates ← 素材候选生成
    ↓
timeline_clips ← 基于素材包创建时间轴
    ↓
audio_configs ← 配置旁白/对话/BGM
    ↓
export_tasks ← 提交导出任务
    ↓
export_files ← 生成导出文件
```

---

## 后续扩展路径

### 第一阶段扩展（用户量增长后）
1. **团队功能**：增加 `team_spaces`、`team_members` 表，`projects` 增加团队关联
2. **配额系统**：`users.quota_info` 拆分为独立的 `quotas` 表
3. **协作功能**：增加 `project_collaborators` 表

### 第二阶段扩展（功能完善后）
1. **素材拆分**：`material_packages.materials` 拆分为独立表（characters, scenes等）
2. **候选拆分**：`candidates` 按类型拆分
3. **音频拆分**：`audio_configs` 拆分为旁白/对话/BGM表
4. **版本管理**：增加 `*_versions` 表

### 第三阶段扩展（精细化运营）
1. **资产分类标签**：增加 `asset_categories`、`asset_tags` 表
2. **收藏功能**：增加 `asset_favorites` 表
3. **详细历史**：增加各模块的 `*_history` 表
4. **操作审计**：完善 `operations` 表的审计能力

---

## 索引策略建议

### MVP阶段必要索引
- 所有外键字段建立索引
- `projects` 的 `user_id + status` 复合索引
- `material_packages` 的 `project_id + is_active` 复合索引
- `candidates` 的 `project_id + target_type + target_id` 复合索引
- `timeline_clips` 的 `project_id + shot_number` 唯一索引

### 查询优化建议
- 使用JSONB字段的 GIN索引支持复杂查询
```sql
CREATE INDEX idx_projects_input_config_gin ON projects USING GIN (input_config);
CREATE INDEX idx_material_packages_materials_gin ON material_packages USING GIN (materials);
CREATE INDEX idx_assets_attributes_gin ON assets USING GIN (attributes);
```

---

## 总结

**MVP版数据库统计**：
- 核心表：**15张**
- 关键索引：约**30个**
- 支持功能：项目全流程（输入→生成→剪辑→导出）+ 资产库

**相比完整版**：
- 表数量减少 **75%**（60+ → 15）
- 保持全部核心功能
- JSONB字段提供良好扩展性
- 清晰的扩展路径设计
