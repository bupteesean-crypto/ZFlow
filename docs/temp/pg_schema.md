# 一站式视频生成平台 - 数据库设计

本文档基于PRD的六个功能模块，逐步构建完整的PostgreSQL数据库设计。

---

## 模块一：项目与任务管理

### 1.1 用户与空间相关

#### 1.1.1 用户表 (users)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 用户唯一标识 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 邮箱 |
| phone | VARCHAR(20) | | 手机号 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| avatar_url | VARCHAR(500) | | 头像URL |
| user_type | VARCHAR(20) | NOT NULL | 用户类型: personal/team |
| status | VARCHAR(20) | NOT NULL | 状态: active/suspended/deleted |
| last_login_at | TIMESTAMP | | 最后登录时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('personal', 'team')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

#### 1.1.2 团队空间表 (team_spaces)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 团队空间唯一标识 |
| name | VARCHAR(100) | NOT NULL | 团队名称 |
| description | TEXT | | 团队描述 |
| invite_code | VARCHAR(20) | NOT NULL, UNIQUE | 邀请码 |
| owner_id | UUID | FK->users | 团队所有者 |
| logo_url | VARCHAR(500) | | 团队Logo |
| max_members | INTEGER | NOT NULL | 最大成员数 |
| max_daily_tasks | INTEGER | | 每日最大任务数限制 |
| status | VARCHAR(20) | NOT NULL | 状态: active/suspended |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE team_spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    invite_code VARCHAR(20) NOT NULL UNIQUE,
    owner_id UUID NOT NULL REFERENCES users(id),
    logo_url VARCHAR(500),
    max_members INTEGER NOT NULL DEFAULT 50,
    max_daily_tasks INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_spaces_invite_code ON team_spaces(invite_code);
CREATE INDEX idx_team_spaces_owner ON team_spaces(owner_id);
```

#### 1.1.3 团队成员表 (team_members)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 成员关系唯一标识 |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| user_id | UUID | FK->users | 用户ID |
| role | VARCHAR(20) | NOT NULL | 角色: admin/editor/viewer |
| permissions | JSONB | | 详细权限配置 |
| joined_at | TIMESTAMP | NOT NULL | 加入时间 |
| status | VARCHAR(20) | NOT NULL | 状态: active/removed |

```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_space_id UUID NOT NULL REFERENCES team_spaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    permissions JSONB,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'removed')),
    UNIQUE(team_space_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_space_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
```

### 1.2 创作单元（任务）相关

#### 1.2.1 创作单元表 (creative_units)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 创作单元唯一标识 |
| name | VARCHAR(200) | NOT NULL | 任务名称 |
| description | TEXT | | 任务描述/备注 |
| user_id | UUID | FK->users | 创建用户ID |
| team_space_id | UUID | FK->team_spaces | 所属团队空间(个人用户为NULL) |
| workspace_type | VARCHAR(20) | NOT NULL | 空间类型: personal/team |
| current_stage | VARCHAR(50) | NOT NULL | 当前阶段: input/generating/editing/completed/exported |
| status | VARCHAR(20) | NOT NULL | 状态: draft/in_progress/completed/exported |
| auto_name | BOOLEAN | NOT NULL | 是否自动命名 |
| progress | INTEGER | | 进度百分比 0-100 |
| priority | VARCHAR(20) | | 优先级: low/medium/high |
| tags | TEXT[] | | 标签数组 |
| metadata | JSONB | | 元数据(画幅、时长、语言等) |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| deleted_at | TIMESTAMP | | 软删除时间 |

```sql
CREATE TABLE creative_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES users(id),
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE SET NULL,
    workspace_type VARCHAR(20) NOT NULL CHECK (workspace_type IN ('personal', 'team')),
    current_stage VARCHAR(50) NOT NULL DEFAULT 'input' CHECK (current_stage IN ('input', 'generating', 'editing', 'completed', 'exported')),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'exported')),
    auto_name BOOLEAN NOT NULL DEFAULT true,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high')),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_creative_units_user ON creative_units(user_id);
CREATE INDEX idx_creative_units_team ON creative_units(team_space_id);
CREATE INDEX idx_creative_units_status ON creative_units(status);
CREATE INDEX idx_creative_units_stage ON creative_units(current_stage);
CREATE INDEX idx_creative_units_created ON creative_units(created_at DESC);
```

#### 1.2.2 任务协作者表 (task_collaborators)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 协作者关系ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| user_id | UUID | FK->users | 协作者用户ID |
| role | VARCHAR(20) | NOT NULL | 角色: owner/editor/viewer |
| permissions | JSONB | | 权限配置 |
| assigned_by | UUID | FK->users | 分配人 |
| assigned_at | TIMESTAMP | NOT NULL | 分配时间 |

```sql
CREATE TABLE task_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    permissions JSONB,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creative_unit_id, user_id)
);

CREATE INDEX idx_task_collaborators_unit ON task_collaborators(creative_unit_id);
CREATE INDEX idx_task_collaborators_user ON task_collaborators(user_id);
```

#### 1.2.3 任务阶段历史表 (task_stage_history)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 历史记录ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| from_stage | VARCHAR(50) | | 原阶段 |
| to_stage | VARCHAR(50) | NOT NULL | 目标阶段 |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| metadata | JSONB | | 阶段相关元数据 |
| created_at | TIMESTAMP | NOT NULL | 记录时间 |

```sql
CREATE TABLE task_stage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    from_stage VARCHAR(50),
    to_stage VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_stage_history_unit ON task_stage_history(creative_unit_id);
```

### 1.3 用户会话与最近使用

#### 1.3.1 用户会话表 (user_sessions)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 会话ID |
| user_id | UUID | FK->users | 用户ID |
| current_space_id | UUID | FK->team_spaces | 当前空间ID |
| current_space_type | VARCHAR(20) | NOT NULL | 当前空间类型 |
| session_token | VARCHAR(255) | NOT NULL, UNIQUE | 会话令牌 |
| refresh_token | VARCHAR(255) | | 刷新令牌 |
| expires_at | TIMESTAMP | NOT NULL | 过期时间 |
| last_activity | TIMESTAMP | NOT NULL | 最后活动时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_space_id UUID REFERENCES team_spaces(id) ON DELETE SET NULL,
    current_space_type VARCHAR(20) NOT NULL CHECK (current_space_type IN ('personal', 'team')),
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
```

#### 1.3.2 空间使用记录表 (space_usage_history)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录ID |
| user_id | UUID | FK->users | 用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| space_type | VARCHAR(20) | NOT NULL | 空间类型 |
| last_accessed | TIMESTAMP | NOT NULL | 最后访问时间 |
| access_count | INTEGER | NOT NULL | 访问次数 |

```sql
CREATE TABLE space_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    space_type VARCHAR(20) NOT NULL CHECK (space_type IN ('personal', 'team')),
    last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_space_usage_user ON space_usage_history(user_id);
CREATE INDEX idx_space_usage_last_accessed ON space_usage_history(last_accessed DESC);
```

### 1.4 配额管理

#### 1.4.1 用户配额表 (user_quotas)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配额记录ID |
| user_id | UUID | FK->users | 用户ID |
| quota_type | VARCHAR(50) | NOT NULL | 配额类型 |
| max_value | INTEGER | NOT NULL | 最大值 |
| used_value | INTEGER | NOT NULL | 已使用值 |
| reset_period | VARCHAR(20) | | 重置周期: daily/weekly/monthly/never |
| last_reset_at | TIMESTAMP | | 最后重置时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE user_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quota_type VARCHAR(50) NOT NULL,
    max_value INTEGER NOT NULL,
    used_value INTEGER NOT NULL DEFAULT 0,
    reset_period VARCHAR(20) CHECK (reset_period IN ('daily', 'weekly', 'monthly', 'never')),
    last_reset_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, quota_type)
);

CREATE INDEX idx_user_quotas_user ON user_quotas(user_id);
```

#### 1.4.2 团队配额表 (team_quotas)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配额记录ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| quota_type | VARCHAR(50) | NOT NULL | 配额类型 |
| max_value | INTEGER | NOT NULL | 最大值 |
| used_value | INTEGER | NOT NULL | 已使用值 |
| reset_period | VARCHAR(20) | | 重置周期 |
| last_reset_at | TIMESTAMP | | 最后重置时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE team_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_space_id UUID NOT NULL REFERENCES team_spaces(id) ON DELETE CASCADE,
    quota_type VARCHAR(50) NOT NULL,
    max_value INTEGER NOT NULL,
    used_value INTEGER NOT NULL DEFAULT 0,
    reset_period VARCHAR(20) CHECK (reset_period IN ('daily', 'weekly', 'monthly', 'never')),
    last_reset_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_space_id, quota_type)
);

CREATE INDEX idx_team_quotas_team ON team_quotas(team_space_id);
```

---

## 模块二：输入与素材导入

### 2.1 输入内容相关

#### 2.1.1 创作输入表 (creative_inputs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 输入记录唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| input_mode | VARCHAR(20) | NOT NULL | 输入模式: general/professional |
| input_type | VARCHAR(50) | NOT NULL | 输入类型: text/script/storyboard |
| content | TEXT | NOT NULL | 输入内容 |
| word_count | INTEGER | NOT NULL | 字数统计 |
| status | VARCHAR(20) | NOT NULL | 状态: draft/submitted/processing/completed/failed |
| submit_time | TIMESTAMP | | 提交时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE creative_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    input_mode VARCHAR(20) NOT NULL CHECK (input_mode IN ('general', 'professional')),
    input_type VARCHAR(50) NOT NULL CHECK (input_type IN ('text', 'script', 'storyboard')),
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'processing', 'completed', 'failed')),
    submit_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_creative_inputs_unit ON creative_inputs(creative_unit_id);
CREATE INDEX idx_creative_inputs_status ON creative_inputs(status);
```

#### 2.1.2 输入配置表 (input_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| config_key | VARCHAR(50) | NOT NULL | 配置键 |
| config_value | JSONB | NOT NULL | 配置值 |
| category | VARCHAR(50) | NOT NULL | 配置分类 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE input_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    config_key VARCHAR(50) NOT NULL,
    config_value JSONB NOT NULL,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creative_unit_id, config_key)
);

CREATE INDEX idx_input_configs_unit ON input_configs(creative_unit_id);
CREATE INDEX idx_input_configs_category ON input_configs(category);
```

### 2.2 附件与文件管理

#### 2.2.1 附件表 (attachments)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 附件唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| file_name | VARCHAR(255) | NOT NULL | 原始文件名 |
| file_type | VARCHAR(50) | NOT NULL | 文件类型 |
| file_category | VARCHAR(50) | NOT NULL | 文件分类: image/audio/video/document |
| mime_type | VARCHAR(100) | NOT NULL | MIME类型 |
| file_size | BIGINT | NOT NULL | 文件大小(字节) |
| storage_path | VARCHAR(500) | NOT NULL | 存储路径 |
| storage_provider | VARCHAR(50) | NOT NULL | 存储提供商 |
| file_hash | VARCHAR(64) | | 文件哈希(SHA256) |
| upload_status | VARCHAR(20) | NOT NULL | 上传状态: uploading/completed/failed |
| upload_progress | INTEGER | | 上传进度 0-100 |
| error_message | TEXT | | 错误信息 |
| uploaded_by | UUID | FK->users | 上传用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_category VARCHAR(50) NOT NULL CHECK (file_category IN ('image', 'audio', 'video', 'document')),
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    storage_provider VARCHAR(50) NOT NULL,
    file_hash VARCHAR(64),
    upload_status VARCHAR(20) NOT NULL DEFAULT 'uploading' CHECK (upload_status IN ('uploading', 'completed', 'failed')),
    upload_progress INTEGER DEFAULT 0 CHECK (upload_progress >= 0 AND upload_progress <= 100),
    error_message TEXT,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_unit ON attachments(creative_unit_id);
CREATE INDEX idx_attachments_category ON attachments(file_category);
CREATE INDEX idx_attachments_status ON attachments(upload_status);
CREATE INDEX idx_attachments_hash ON attachments(file_hash);
```

#### 2.2.2 附件标注表 (attachment_labels)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 标注唯一标识 |
| attachment_id | UUID | FK->attachments | 附件ID |
| label_type | VARCHAR(50) | NOT NULL | 标注类型 |
| label_value | VARCHAR(255) | NOT NULL | 标注内容 |
| is_auto_generated | BOOLEAN | NOT NULL | 是否自动生成 |
| created_by | UUID | FK->users | 创建用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE attachment_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attachment_id UUID NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
    label_type VARCHAR(50) NOT NULL,
    label_value VARCHAR(255) NOT NULL,
    is_auto_generated BOOLEAN NOT NULL DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachment_labels_attachment ON attachment_labels(attachment_id);
CREATE INDEX idx_attachment_labels_type ON attachment_labels(label_type);
```

### 2.3 模型与风格配置

#### 2.3.1 模型配置表 (model_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 模型配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| model_category | VARCHAR(50) | NOT NULL | 模型分类: text_to_image/image_to_image/text_to_video |
| model_id | VARCHAR(50) | NOT NULL | 模型ID |
| model_name | VARCHAR(100) | NOT NULL | 模型名称 |
| model_display_name | VARCHAR(100) | NOT NULL | 模型显示名称 |
| model_icon | VARCHAR(500) | | 模型图标URL |
| is_smart_selected | BOOLEAN | NOT NULL | 是否智能选择 |
| config_params | JSONB | | 配置参数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE model_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    model_category VARCHAR(50) NOT NULL CHECK (model_category IN ('text_to_image', 'image_to_image', 'text_to_video')),
    model_id VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_display_name VARCHAR(100) NOT NULL,
    model_icon VARCHAR(500),
    is_smart_selected BOOLEAN NOT NULL DEFAULT false,
    config_params JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_configs_unit ON model_configs(creative_unit_id);
CREATE INDEX idx_model_configs_category ON model_configs(model_category);
```

#### 2.3.2 风格配置表 (style_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 风格配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| style_id | VARCHAR(50) | NOT NULL | 风格ID |
| style_name | VARCHAR(100) | NOT NULL | 风格名称 |
| style_prompt | TEXT | NOT NULL | 风格Prompt |
| preview_image_url | VARCHAR(500) | | 预览图URL |
| is_custom | BOOLEAN | NOT NULL | 是否自定义 |
| filter_params | JSONB | | 筛选参数(主体年龄、性别等) |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE style_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    style_id VARCHAR(50) NOT NULL,
    style_name VARCHAR(100) NOT NULL,
    style_prompt TEXT NOT NULL,
    preview_image_url VARCHAR(500),
    is_custom BOOLEAN NOT NULL DEFAULT false,
    filter_params JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_style_configs_unit ON style_configs(creative_unit_id);
CREATE INDEX idx_style_configs_style_id ON style_configs(style_id);
```

#### 2.3.3 预设风格库表 (preset_styles)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | VARCHAR(50) | PK | 风格ID |
| name | VARCHAR(100) | NOT NULL | 风格名称 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| prompt_template | TEXT | NOT NULL | Prompt模板 |
| preview_image_url | VARCHAR(500) | | 预览图URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| category | VARCHAR(50) | | 分类 |
| is_active | BOOLEAN | NOT NULL | 是否启用 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE preset_styles (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,
    prompt_template TEXT NOT NULL,
    preview_image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    category VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preset_styles_order ON preset_styles(display_order);
CREATE INDEX idx_preset_styles_category ON preset_styles(category);
```

### 2.4 视频规格配置

#### 2.4.1 画幅配置表 (aspect_ratio_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| aspect_ratio | VARCHAR(20) | NOT NULL | 画幅比例: 16:9/4:3/2.35:1/19:16 |
| width | INTEGER | | 宽度(像素) |
| height | INTEGER | | 高度(像素) |
| description | TEXT | | 描述 |
| preview_url | VARCHAR(500) | | 预览图URL |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE aspect_ratio_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    aspect_ratio VARCHAR(20) NOT NULL,
    width INTEGER,
    height INTEGER,
    description TEXT,
    preview_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creative_unit_id, aspect_ratio)
);

CREATE INDEX idx_aspect_ratio_configs_unit ON aspect_ratio_configs(creative_unit_id);
```

#### 2.4.2 时长配置表 (duration_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| is_smart | BOOLEAN | NOT NULL | 是否智能时长 |
| duration_seconds | INTEGER | | 时长(秒) |
| custom_hours | INTEGER | | 自定义小时 |
| custom_minutes | INTEGER | | 自定义分钟 |
| custom_seconds | INTEGER | | 自定义秒 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE duration_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    is_smart BOOLEAN NOT NULL DEFAULT true,
    duration_seconds INTEGER,
    custom_hours INTEGER DEFAULT 0 CHECK (custom_hours >= 0),
    custom_minutes INTEGER DEFAULT 0 CHECK (custom_minutes >= 0 AND custom_minutes < 60),
    custom_seconds INTEGER DEFAULT 0 CHECK (custom_seconds >= 0 AND custom_seconds < 60),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (is_smart = true OR (duration_seconds IS NOT NULL OR (custom_hours + custom_minutes + custom_seconds) > 0))
);

CREATE INDEX idx_duration_configs_unit ON duration_configs(creative_unit_id);
```

### 2.5 主体配置

#### 2.5.1 主体配置表 (subject_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 主体配置唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| subject_type | VARCHAR(50) | NOT NULL | 主体类型 |
| subject_name | VARCHAR(100) | | 主体名称 |
| reference_image_id | UUID | FK->attachments | 参考图附件ID |
| consistency_level | VARCHAR(20) | NOT NULL | 一致性级别 |
| config_params | JSONB | | 配置参数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE subject_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    subject_type VARCHAR(50) NOT NULL,
    subject_name VARCHAR(100),
    reference_image_id UUID REFERENCES attachments(id) ON DELETE SET NULL,
    consistency_level VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (consistency_level IN ('low', 'medium', 'high')),
    config_params JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subject_configs_unit ON subject_configs(creative_unit_id);
CREATE INDEX idx_subject_configs_type ON subject_configs(subject_type);
```

### 2.6 配置模板

#### 2.6.1 用户配置模板表 (user_config_templates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 模板唯一标识 |
| user_id | UUID | FK->users | 用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID(NULL表示个人) |
| template_name | VARCHAR(100) | NOT NULL | 模板名称 |
| is_default | BOOLEAN | NOT NULL | 是否默认模板 |
| config_data | JSONB | NOT NULL | 配置数据 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE user_config_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    template_name VARCHAR(100) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,
    config_data JSONB NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_config_templates_user ON user_config_templates(user_id);
CREATE INDEX idx_user_config_templates_team ON user_config_templates(team_space_id);
```

---

## 模块三：生成素材管理

### 3.1 素材包管理

#### 3.1.1 素材包表 (material_packages)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 素材包唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| package_name | VARCHAR(200) | NOT NULL | 素材包名称 |
| package_version | INTEGER | NOT NULL | 版本号 |
| status | VARCHAR(20) | NOT NULL | 状态: generating/completed/failed/incomplete |
| is_active | BOOLEAN | NOT NULL | 是否为当前激活版本 |
| summary | TEXT | | 变更摘要 |
| generation_summary | TEXT | | 生成总结 |
| display_order | INTEGER | | 显示顺序 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE material_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    package_name VARCHAR(200) NOT NULL,
    package_version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'failed', 'incomplete')),
    is_active BOOLEAN NOT NULL DEFAULT false,
    summary TEXT,
    generation_summary TEXT,
    display_order INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_material_packages_unit ON material_packages(creative_unit_id);
CREATE INDEX idx_material_packages_version ON material_packages(creative_unit_id, package_version);
CREATE INDEX idx_material_packages_status ON material_packages(status);
CREATE INDEX idx_material_packages_active ON material_packages(is_active);
```

#### 3.1.2 素材包历史表 (material_package_history)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 历史记录ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| action_type | VARCHAR(50) | NOT NULL | 操作类型: created/renamed/activated |
| action_description | TEXT | | 操作描述 |
| previous_data | JSONB | | 变更前数据 |
| new_data | JSONB | | 变更后数据 |
| created_by | UUID | FK->users | 操作用户ID |
| created_at | TIMESTAMP | NOT NULL | 记录时间 |

```sql
CREATE TABLE material_package_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT,
    previous_data JSONB,
    new_data JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_material_package_history_package ON material_package_history(material_package_id);
```

### 3.2 生成任务与进度

#### 3.2.1 生成任务表 (generation_tasks)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 生成任务唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| task_type | VARCHAR(50) | NOT NULL | 任务类型: storyline/artstyle/characters/scenes/storyboard |
| task_name | VARCHAR(200) | NOT NULL | 任务名称 |
| display_name | VARCHAR(200) | NOT NULL | 显示名称 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| status | VARCHAR(20) | NOT NULL | 状态: pending/in_progress/completed/failed/skipped |
| progress | INTEGER | | 进度 0-100 |
| error_message | TEXT | | 错误信息 |
| retry_count | INTEGER | NOT NULL | 重试次数 |
| max_retries | INTEGER | NOT NULL | 最大重试次数 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE generation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('storyline', 'artstyle', 'characters', 'scenes', 'storyboard')),
    task_name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    display_order INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generation_tasks_unit ON generation_tasks(creative_unit_id);
CREATE INDEX idx_generation_tasks_package ON generation_tasks(material_package_id);
CREATE INDEX idx_generation_tasks_status ON generation_tasks(status);
CREATE INDEX idx_generation_tasks_type ON generation_tasks(task_type);
```

### 3.3 故事梗概素材

#### 3.3.1 故事梗概表 (storylines)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 故事梗概唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| generation_task_id | UUID | FK->generation_tasks | 生成任务ID |
| title | VARCHAR(200) | | 标题 |
| content | TEXT | NOT NULL | 故事内容 |
| summary | TEXT | | 摘要 |
| genre | VARCHAR(50) | | 类型/题材 |
| tone | VARCHAR(50) | | 基调 |
| target_duration | INTEGER | | 目标时长(秒) |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE storylines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    generation_task_id UUID REFERENCES generation_tasks(id) ON DELETE SET NULL,
    title VARCHAR(200),
    content TEXT NOT NULL,
    summary TEXT,
    genre VARCHAR(50),
    tone VARCHAR(50),
    target_duration INTEGER,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_storylines_package ON storylines(material_package_id);
```

### 3.4 美术风格素材

#### 3.4.1 美术风格表 (art_styles)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 美术风格唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| generation_task_id | UUID | FK->generation_tasks | 生成任务ID |
| style_name | VARCHAR(100) | NOT NULL | 风格名称 |
| description | TEXT | NOT NULL | 风格描述 |
| prompt_template | TEXT | | Prompt模板 |
| reference_image_url | VARCHAR(500) | | 参考图URL |
| color_palette | JSONB | | 色彩方案 |
| visual_keywords | TEXT[] | | 视觉关键词 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE art_styles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    generation_task_id UUID REFERENCES generation_tasks(id) ON DELETE SET NULL,
    style_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    prompt_template TEXT,
    reference_image_url VARCHAR(500),
    color_palette JSONB,
    visual_keywords TEXT[] DEFAULT '{}',
    is_selected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_art_styles_package ON art_styles(material_package_id);
```

### 3.5 角色素材

#### 3.5.1 角色表 (characters)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 角色唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| generation_task_id | UUID | FK->generation_tasks | 生成任务ID |
| character_name | VARCHAR(100) | NOT NULL | 角色名称 |
| character_type | VARCHAR(50) | NOT NULL | 角色类型: protagonist/supporting/extras |
| description | TEXT | | 角色描述 |
| personality | TEXT[] | | 性格特征 |
| appearance | TEXT | | 外观描述 |
| voice_style | VARCHAR(100) | | 音色风格 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| display_order | INTEGER | | 显示顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    generation_task_id UUID REFERENCES generation_tasks(id) ON DELETE SET NULL,
    character_name VARCHAR(100) NOT NULL,
    character_type VARCHAR(50) NOT NULL CHECK (character_type IN ('protagonist', 'supporting', 'extras')),
    description TEXT,
    personality TEXT[] DEFAULT '{}',
    appearance TEXT,
    voice_style VARCHAR(100),
    is_selected BOOLEAN NOT NULL DEFAULT false,
    display_order INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_characters_package ON characters(material_package_id);
CREATE INDEX idx_characters_type ON characters(character_type);
```

#### 3.5.2 角色图片候选表 (character_image_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选图片唯一标识 |
| character_id | UUID | FK->characters | 角色ID |
| image_type | VARCHAR(50) | NOT NULL | 图片类型: front_view/three_view/detail |
| image_url | VARCHAR(500) | NOT NULL | 图片URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| prompt | TEXT | | 生成提示词 |
| generation_params | JSONB | | 生成参数 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE character_image_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL CHECK (image_type IN ('front_view', 'three_view', 'detail')),
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    prompt TEXT,
    generation_params JSONB,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_character_image_candidates_character ON character_image_candidates(character_id);
CREATE INDEX idx_character_image_candidates_selected ON character_image_candidates(is_selected);
```

#### 3.5.3 角色音色候选表 (character_voice_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 音色候选唯一标识 |
| character_id | UUID | FK->characters | 角色ID |
| voice_name | VARCHAR(100) | NOT NULL | 音色名称 |
| voice_id | VARCHAR(50) | | 音色ID(关联资产库) |
| audio_sample_url | VARCHAR(500) | | 试听音频URL |
| voice_params | JSONB | | 音色参数 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE character_voice_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    voice_name VARCHAR(100) NOT NULL,
    voice_id VARCHAR(50),
    audio_sample_url VARCHAR(500),
    voice_params JSONB,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_character_voice_candidates_character ON character_voice_candidates(character_id);
CREATE INDEX idx_character_voice_candidates_selected ON character_voice_candidates(is_selected);
```

### 3.6 场景素材

#### 3.6.1 场景表 (scenes)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 场景唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| generation_task_id | UUID | FK->generation_tasks | 生成任务ID |
| scene_name | VARCHAR(100) | NOT NULL | 场景名称 |
| scene_type | VARCHAR(50) | NOT NULL | 场景类型: indoor/outdoor/abstract |
| description | TEXT | | 场景描述 |
| atmosphere | TEXT | | 氛围描述 |
| lighting | VARCHAR(100) | | 光照描述 |
| camera_angle | VARCHAR(50) | | 镜头角度 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| display_order | INTEGER | | 显示顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    generation_task_id UUID REFERENCES generation_tasks(id) ON DELETE SET NULL,
    scene_name VARCHAR(100) NOT NULL,
    scene_type VARCHAR(50) NOT NULL CHECK (scene_type IN ('indoor', 'outdoor', 'abstract')),
    description TEXT,
    atmosphere TEXT,
    lighting VARCHAR(100),
    camera_angle VARCHAR(50),
    is_selected BOOLEAN NOT NULL DEFAULT false,
    display_order INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenes_package ON scenes(material_package_id);
CREATE INDEX idx_scenes_type ON scenes(scene_type);
```

#### 3.6.2 场景图片候选表 (scene_image_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选图片唯一标识 |
| scene_id | UUID | FK->scenes | 场景ID |
| image_url | VARCHAR(500) | NOT NULL | 图片URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| prompt | TEXT | | 生成提示词 |
| generation_params | JSONB | | 生成参数 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE scene_image_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    prompt TEXT,
    generation_params JSONB,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scene_image_candidates_scene ON scene_image_candidates(scene_id);
CREATE INDEX idx_scene_image_candidates_selected ON scene_image_candidates(is_selected);
```

### 3.7 分镜剧本素材

#### 3.7.1 分镜剧本表 (storyboards)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 分镜唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| generation_task_id | UUID | FK->generation_tasks | 生成任务ID |
| shot_number | INTEGER | NOT NULL | 镜头序号 |
| shot_type | VARCHAR(50) | NOT NULL | 镜头类型 |
| scene_id | UUID | FK->scenes | 关联场景ID |
| character_id | UUID | FK->characters | 关联角色ID |
| description | TEXT | NOT NULL | 镜头描述 |
| dialogue | TEXT | | 台词/旁白 |
| action | TEXT | | 动作描述 |
| duration | DECIMAL(5,2) | | 镜头时长(秒) |
| camera_movement | VARCHAR(50) | | 镜头运动 |
| transition | VARCHAR(50) | | 转场效果 |
| reference_image_url | VARCHAR(500) | | 参考图URL |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE storyboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    generation_task_id UUID REFERENCES generation_tasks(id) ON DELETE SET NULL,
    shot_number INTEGER NOT NULL,
    shot_type VARCHAR(50) NOT NULL,
    scene_id UUID REFERENCES scenes(id) ON DELETE SET NULL,
    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    dialogue TEXT,
    action TEXT,
    duration DECIMAL(5,2),
    camera_movement VARCHAR(50),
    transition VARCHAR(50),
    reference_image_url VARCHAR(500),
    is_selected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_package_id, shot_number)
);

CREATE INDEX idx_storyboards_package ON storyboards(material_package_id);
CREATE INDEX idx_storyboards_scene ON storyboards(scene_id);
CREATE INDEX idx_storyboards_character ON storyboards(character_id);
```

### 3.8 元素级修改记录

#### 3.8.1 元素修改记录表 (element_modifications)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 修改记录唯一标识 |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| element_type | VARCHAR(50) | NOT NULL | 元素类型: storyline/artstyle/character/scene/storyboard |
| element_id | UUID | NOT NULL | 元素ID |
| element_name | VARCHAR(200) | | 元素名称 |
| modification_type | VARCHAR(50) | NOT NULL | 修改类型: text_edit/image_regenerate/voice_change |
| original_value | TEXT | | 原始值 |
| new_value | TEXT | | 新值 |
| user_prompt | TEXT | | 用户修改意见 |
| result_candidate_id | UUID | | 结果候选ID |
| auto_synced_items | JSONB | | 自动同步的项目 |
| created_by | UUID | FK->users | 修改用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE element_modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL CHECK (element_type IN ('storyline', 'artstyle', 'character', 'scene', 'storyboard')),
    element_id UUID NOT NULL,
    element_name VARCHAR(200),
    modification_type VARCHAR(50) NOT NULL,
    original_value TEXT,
    new_value TEXT,
    user_prompt TEXT,
    result_candidate_id UUID,
    auto_synced_items JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_element_modifications_package ON element_modifications(material_package_id);
CREATE INDEX idx_element_modifications_element ON element_modifications(element_type, element_id);
```

### 3.9 对话与交互记录

#### 3.9.1 系统对话记录表 (system_conversations)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 对话记录唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| message_type | VARCHAR(20) | NOT NULL | 消息类型: system/user |
| message_content | TEXT | NOT NULL | 消息内容 |
| context_data | JSONB | | 上下文数据 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE system_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    material_package_id UUID REFERENCES material_packages(id) ON DELETE SET NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('system', 'user')),
    message_content TEXT NOT NULL,
    context_data JSONB,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_conversations_unit ON system_conversations(creative_unit_id);
CREATE INDEX idx_system_conversations_package ON system_conversations(material_package_id);
```

---

## 模块四：剪辑与编排

### 4.1 时间轴与项目

#### 4.1.1 编辑项目表 (editing_projects)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 编辑项目唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| material_package_id | UUID | FK->material_packages | 素材包ID |
| project_name | VARCHAR(200) | NOT NULL | 项目名称 |
| total_duration | DECIMAL(10,2) | NOT NULL | 总时长(秒) |
| video_aspect_ratio | VARCHAR(20) | NOT NULL | 视频画幅 |
| resolution_width | INTEGER | | 分辨率宽度 |
| resolution_height | INTEGER | | 分辨率高度 |
| fps | INTEGER | NOT NULL | 帧率 |
| view_mode | VARCHAR(20) | NOT NULL | 当前视图模式: timeline/storyboard |
| auto_save_data | JSONB | | 自动保存数据 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE editing_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    material_package_id UUID NOT NULL REFERENCES material_packages(id) ON DELETE CASCADE,
    project_name VARCHAR(200) NOT NULL,
    total_duration DECIMAL(10,2) NOT NULL DEFAULT 0,
    video_aspect_ratio VARCHAR(20) NOT NULL,
    resolution_width INTEGER,
    resolution_height INTEGER,
    fps INTEGER NOT NULL DEFAULT 30,
    view_mode VARCHAR(20) NOT NULL DEFAULT 'timeline' CHECK (view_mode IN ('timeline', 'storyboard')),
    auto_save_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creative_unit_id, material_package_id)
);

CREATE INDEX idx_editing_projects_unit ON editing_projects(creative_unit_id);
CREATE INDEX idx_editing_projects_package ON editing_projects(material_package_id);
```

### 4.2 时间轴片段

#### 4.2.1 时间轴片段表 (timeline_clips)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 片段唯一标识 |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| storyboard_id | UUID | FK->storyboards | 分镜ID |
| clip_order | INTEGER | NOT NULL | 片段顺序 |
| clip_type | VARCHAR(20) | NOT NULL | 片段类型: image/video |
| duration | DECIMAL(5,2) | NOT NULL | 时长(秒) |
| start_time | DECIMAL(10,2) | NOT NULL | 开始时间(秒) |
| end_time | DECIMAL(10,2) | NOT NULL | 结束时间(秒) |
| transition_effect | VARCHAR(50) | | 转场效果 |
| transition_duration | DECIMAL(4,2) | | 转场时长 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE timeline_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    storyboard_id UUID NOT NULL REFERENCES storyboards(id) ON DELETE CASCADE,
    clip_order INTEGER NOT NULL,
    clip_type VARCHAR(20) NOT NULL CHECK (clip_type IN ('image', 'video')),
    duration DECIMAL(5,2) NOT NULL DEFAULT 5.0,
    start_time DECIMAL(10,2) NOT NULL DEFAULT 0,
    end_time DECIMAL(10,2) NOT NULL,
    transition_effect VARCHAR(50),
    transition_duration DECIMAL(4,2),
    is_selected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(editing_project_id, clip_order)
);

CREATE INDEX idx_timeline_clips_project ON timeline_clips(editing_project_id);
CREATE INDEX idx_timeline_clips_storyboard ON timeline_clips(storyboard_id);
CREATE INDEX idx_timeline_clips_order ON timeline_clips(editing_project_id, clip_order);
```

### 4.3 分镜画面与视频候选

#### 4.3.1 分镜画面候选表 (clip_image_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选图片唯一标识 |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| image_url | VARCHAR(500) | NOT NULL | 图片URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| prompt | TEXT | | 生成提示词 |
| generation_params | JSONB | | 生成参数 |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| is_applied | BOOLEAN | NOT NULL | 是否已应用 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE clip_image_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    prompt TEXT,
    generation_params JSONB,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    is_applied BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clip_image_candidates_clip ON clip_image_candidates(timeline_clip_id);
CREATE INDEX idx_clip_image_candidates_selected ON clip_image_candidates(is_selected);
```

#### 4.3.2 分镜视频候选表 (clip_video_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选视频唯一标识 |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| video_url | VARCHAR(500) | NOT NULL | 视频URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| video_duration | DECIMAL(5,2) | | 视频时长(秒) |
| model_id | VARCHAR(50) | | 使用的模型ID |
| model_name | VARCHAR(100) | | 模型名称 |
| prompt | TEXT | | 生成提示词 |
| generation_params | JSONB | | 生成参数 |
| quota_consumed | INTEGER | | 消耗的额度 |
| generation_status | VARCHAR(20) | NOT NULL | 生成状态: pending/processing/completed/failed |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| is_applied | BOOLEAN | NOT NULL | 是否已应用 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE clip_video_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    video_duration DECIMAL(5,2),
    model_id VARCHAR(50),
    model_name VARCHAR(100),
    prompt TEXT,
    generation_params JSONB,
    quota_consumed INTEGER,
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (generation_status IN ('pending', 'processing', 'completed', 'failed')),
    is_selected BOOLEAN NOT NULL DEFAULT false,
    is_applied BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clip_video_candidates_clip ON clip_video_candidates(timeline_clip_id);
CREATE INDEX idx_clip_video_candidates_status ON clip_video_candidates(generation_status);
CREATE INDEX idx_clip_video_candidates_selected ON clip_video_candidates(is_selected);
```

#### 4.3.3 视频生成任务表 (video_generation_tasks)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 任务唯一标识 |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| task_type | VARCHAR(20) | NOT NULL | 任务类型: single/batch |
| model_id | VARCHAR(50) | NOT NULL | 模型ID |
| model_name | VARCHAR(100) | NOT NULL | 模型名称 |
| total_clips | INTEGER | NOT NULL | 总片段数 |
| completed_clips | INTEGER | NOT NULL | 已完成片段数 |
| total_quota | INTEGER | NOT NULL | 总额度消耗 |
| status | VARCHAR(20) | NOT NULL | 状态: pending/processing/completed/failed/cancelled |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE video_generation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    task_type VARCHAR(20) NOT NULL CHECK (task_type IN ('single', 'batch')),
    model_id VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    total_clips INTEGER NOT NULL DEFAULT 0,
    completed_clips INTEGER NOT NULL DEFAULT 0,
    total_quota INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_video_generation_tasks_project ON video_generation_tasks(editing_project_id);
CREATE INDEX idx_video_generation_tasks_status ON video_generation_tasks(status);
```

### 4.4 音频配置

#### 4.4.1 片段旁白表 (clip_narrations)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 旁白唯一标识 |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| narration_text | TEXT | NOT NULL | 旁白文本 |
| voice_id | VARCHAR(50) | | 音色ID |
| voice_name | VARCHAR(100) | | 音色名称 |
| audio_url | VARCHAR(500) | | 生成音频URL |
| estimated_duration | DECIMAL(5,2) | | 预估时长(秒) |
| actual_duration | DECIMAL(5,2) | | 实际时长(秒) |
| speech_speed | DECIMAL(3,2) | NOT NULL | 语速(0.5-2.0) |
| volume | INTEGER | NOT NULL | 音量(0-100) |
| emotion | VARCHAR(50) | | 情绪: calm/happy/serious等 |
| generation_status | VARCHAR(20) | NOT NULL | 生成状态 |
| is_custom_audio | BOOLEAN | NOT NULL | 是否自定义音频 |
| custom_audio_url | VARCHAR(500) | | 自定义音频URL |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE clip_narrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    narration_text TEXT NOT NULL,
    voice_id VARCHAR(50),
    voice_name VARCHAR(100),
    audio_url VARCHAR(500),
    estimated_duration DECIMAL(5,2),
    actual_duration DECIMAL(5,2),
    speech_speed DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (speech_speed >= 0.5 AND speech_speed <= 2.0),
    volume INTEGER NOT NULL DEFAULT 80 CHECK (volume >= 0 AND volume <= 100),
    emotion VARCHAR(50) CHECK (emotion IN ('calm', 'happy', 'serious', 'sad', 'excited', 'angry')),
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (generation_status IN ('pending', 'processing', 'completed', 'failed')),
    is_custom_audio BOOLEAN NOT NULL DEFAULT false,
    custom_audio_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timeline_clip_id)
);

CREATE INDEX idx_clip_narrations_clip ON clip_narrations(timeline_clip_id);
CREATE INDEX idx_clip_narrations_status ON clip_narrations(generation_status);
```

#### 4.4.2 片段对话表 (clip_dialogues)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 对话唯一标识 |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| character_id | UUID | FK->characters | 角色ID |
| dialogue_text | TEXT | NOT NULL | 对话文本 |
| voice_id | VARCHAR(50) | | 音色ID |
| voice_name | VARCHAR(100) | | 音色名称 |
| audio_url | VARCHAR(500) | | 生成音频URL |
| estimated_duration | DECIMAL(5,2) | | 预估时长(秒) |
| actual_duration | DECIMAL(5,2) | | 实际时长(秒) |
| speech_speed | DECIMAL(3,2) | NOT NULL | 语速 |
| volume | INTEGER | NOT NULL | 音量 |
| emotion | VARCHAR(50) | | 情绪 |
| generation_status | VARCHAR(20) | NOT NULL | 生成状态 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE clip_dialogues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
    dialogue_text TEXT NOT NULL,
    voice_id VARCHAR(50),
    voice_name VARCHAR(100),
    audio_url VARCHAR(500),
    estimated_duration DECIMAL(5,2),
    actual_duration DECIMAL(5,2),
    speech_speed DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (speech_speed >= 0.5 AND speech_speed <= 2.0),
    volume INTEGER NOT NULL DEFAULT 80 CHECK (volume >= 0 AND volume <= 100),
    emotion VARCHAR(50) CHECK (emotion IN ('calm', 'happy', 'serious', 'sad', 'excited', 'angry')),
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (generation_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clip_dialogues_clip ON clip_dialogues(timeline_clip_id);
CREATE INDEX idx_clip_dialogues_character ON clip_dialogues(character_id);
```

#### 4.4.3 背景音乐表 (background_music)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | BGM唯一标识 |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| music_source | VARCHAR(20) | NOT NULL | 音乐来源: ai_generated/library/uploaded |
| audio_url | VARCHAR(500) | NOT NULL | 音频URL |
| music_name | VARCHAR(200) | | 音乐名称 |
| prompt | TEXT | | AI生成提示词 |
| volume | INTEGER | NOT NULL | 音量(0-100) |
| is_loop | BOOLEAN | NOT NULL | 是否循环 |
| fade_in_duration | DECIMAL(4,2) | | 淡入时长(秒) |
| fade_out_duration | DECIMAL(4,2) | | 淡出时长(秒) |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE background_music (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    music_source VARCHAR(20) NOT NULL CHECK (music_source IN ('ai_generated', 'library', 'uploaded')),
    audio_url VARCHAR(500) NOT NULL,
    music_name VARCHAR(200),
    prompt TEXT,
    volume INTEGER NOT NULL DEFAULT 50 CHECK (volume >= 0 AND volume <= 100),
    is_loop BOOLEAN NOT NULL DEFAULT true,
    fade_in_duration DECIMAL(4,2) DEFAULT 1.0,
    fade_out_duration DECIMAL(4,2) DEFAULT 1.0,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_background_music_project ON background_music(editing_project_id);
```

#### 4.4.4 BGM候选表 (bgm_candidates)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 候选BGM唯一标识 |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| music_source | VARCHAR(20) | NOT NULL | 音乐来源 |
| audio_url | VARCHAR(500) | NOT NULL | 音频URL |
| music_name | VARCHAR(200) | | 音乐名称 |
| prompt | TEXT | | AI生成提示词 |
| duration | DECIMAL(5,2) | | 时长(秒) |
| library_asset_id | UUID | | 资产库ID |
| is_selected | BOOLEAN | NOT NULL | 是否被选中 |
| generation_order | INTEGER | NOT NULL | 生成顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE bgm_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    music_source VARCHAR(20) NOT NULL CHECK (music_source IN ('ai_generated', 'library', 'uploaded')),
    audio_url VARCHAR(500) NOT NULL,
    music_name VARCHAR(200),
    prompt TEXT,
    duration DECIMAL(5,2),
    library_asset_id UUID,
    is_selected BOOLEAN NOT NULL DEFAULT false,
    generation_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bgm_candidates_project ON bgm_candidates(editing_project_id);
CREATE INDEX idx_bgm_candidates_selected ON bgm_candidates(is_selected);
```

### 4.5 画面编辑

#### 4.5.1 画面编辑配置表 (clip_edit_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| crop_x | INTEGER | | 裁剪X坐标 |
| crop_y | INTEGER | | 裁剪Y坐标 |
| crop_width | INTEGER | | 裁剪宽度 |
| crop_height | INTEGER | | 裁剪高度 |
| zoom_level | DECIMAL(3,2) | NOT NULL | 缩放级别 |
| pan_x | DECIMAL(8,2) | NOT NULL | 平移X |
| pan_y | DECIMAL(8,2) | NOT NULL | 平移Y |
| rotation | DECIMAL(5,2) | | 旋转角度 |
| filter_type | VARCHAR(50) | | 滤镜类型 |
| filter_intensity | DECIMAL(3,2) | | 滤镜强度 |
| transform_params | JSONB | | 其他变换参数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE clip_edit_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    crop_x INTEGER,
    crop_y INTEGER,
    crop_width INTEGER,
    crop_height INTEGER,
    zoom_level DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    pan_x DECIMAL(8,2) NOT NULL DEFAULT 0,
    pan_y DECIMAL(8,2) NOT NULL DEFAULT 0,
    rotation DECIMAL(5,2),
    filter_type VARCHAR(50),
    filter_intensity DECIMAL(3,2),
    transform_params JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timeline_clip_id)
);

CREATE INDEX idx_clip_edit_configs_clip ON clip_edit_configs(timeline_clip_id);
```

### 4.6 编辑历史记录

#### 4.6.1 编辑操作记录表 (editing_history)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| operation_type | VARCHAR(50) | NOT NULL | 操作类型 |
| target_type | VARCHAR(50) | NOT NULL | 目标类型: clip/audio/transition等 |
| target_id | UUID | | 目标ID |
| operation_description | TEXT | | 操作描述 |
| before_state | JSONB | | 操作前状态 |
| after_state | JSONB | | 操作后状态 |
| created_by | UUID | FK->users | 操作用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE editing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID,
    operation_description TEXT,
    before_state JSONB,
    after_state JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_editing_history_project ON editing_history(editing_project_id);
CREATE INDEX idx_editing_history_target ON editing_history(target_type, target_id);
```

---

## 模块五：导出与交付

### 5.1 导出任务

#### 5.1.1 导出任务表 (export_tasks)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 导出任务唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| editing_project_id | UUID | FK->editing_projects | 编辑项目ID |
| task_name | VARCHAR(200) | NOT NULL | 任务名称 |
| export_type | VARCHAR(50) | NOT NULL | 导出类型: video/audio/image/subtitle |
| status | VARCHAR(20) | NOT NULL | 状态: pending/processing/completed/failed/cancelled |
| progress | INTEGER | | 进度 0-100 |
| estimated_duration | INTEGER | | 预计耗时(秒) |
| actual_duration | INTEGER | | 实际耗时(秒) |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE export_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    editing_project_id UUID NOT NULL REFERENCES editing_projects(id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    export_type VARCHAR(50) NOT NULL CHECK (export_type IN ('video', 'audio', 'image', 'subtitle')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    estimated_duration INTEGER,
    actual_duration INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_tasks_unit ON export_tasks(creative_unit_id);
CREATE INDEX idx_export_tasks_project ON export_tasks(editing_project_id);
CREATE INDEX idx_export_tasks_status ON export_tasks(status);
CREATE INDEX idx_export_tasks_created ON export_tasks(created_at DESC);
```

### 5.2 导出配置

#### 5.2.1 导出配置表 (export_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| resolution | VARCHAR(20) | NOT NULL | 分辨率: 720p/1080p/4K |
| width | INTEGER | NOT NULL | 视频宽度 |
| height | INTEGER | NOT NULL | 视频高度 |
| format | VARCHAR(20) | NOT NULL | 输出格式: MP4/MOV/AVI |
| aspect_ratio | VARCHAR(20) | NOT NULL | 画幅比例 |
| video_codec | VARCHAR(50) | | 视频编码 |
| audio_codec | VARCHAR(50) | | 音频编码 |
| bitrate | INTEGER | | 比特率(kbps) |
| fps | INTEGER | | 帧率 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE export_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    resolution VARCHAR(20) NOT NULL CHECK (resolution IN ('720p', '1080p', '4K')),
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    format VARCHAR(20) NOT NULL CHECK (format IN ('MP4', 'MOV', 'AVI')),
    aspect_ratio VARCHAR(20) NOT NULL,
    video_codec VARCHAR(50),
    audio_codec VARCHAR(50),
    bitrate INTEGER,
    fps INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_configs_task ON export_configs(export_task_id);
```

### 5.3 字幕导出

#### 5.3.1 字幕导出配置表 (subtitle_export_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| enabled | BOOLEAN | NOT NULL | 是否启用字幕 |
| burn_in | BOOLEAN | NOT NULL | 是否烧录字幕 |
| subtitle_format | VARCHAR(20) | | 字幕格式: SRT/VTT/ASS |
| font_name | VARCHAR(100) | | 字体名称 |
| font_size | INTEGER | | 字体大小 |
| font_color | VARCHAR(20) | | 字体颜色 |
| font_style | VARCHAR(50) | | 字体样式 |
| position | VARCHAR(20) | | 位置: top/bottom/center |
| background_color | VARCHAR(20) | | 背景颜色 |
| background_opacity | DECIMAL(3,2) | | 背景透明度 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE subtitle_export_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT false,
    burn_in BOOLEAN NOT NULL DEFAULT false,
    subtitle_format VARCHAR(20) CHECK (subtitle_format IN ('SRT', 'VTT', 'ASS')),
    font_name VARCHAR(100),
    font_size INTEGER,
    font_color VARCHAR(20),
    font_style VARCHAR(50),
    position VARCHAR(20) CHECK (position IN ('top', 'bottom', 'center')),
    background_color VARCHAR(20),
    background_opacity DECIMAL(3,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subtitle_export_configs_task ON subtitle_export_configs(export_task_id);
```

#### 5.3.2 字幕内容表 (subtitle_contents)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 字幕条目唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| timeline_clip_id | UUID | FK->timeline_clips | 时间轴片段ID |
| sequence_number | INTEGER | NOT NULL | 序号 |
| start_time | DECIMAL(10,2) | NOT NULL | 开始时间(秒) |
| end_time | DECIMAL(10,2) | NOT NULL | 结束时间(秒) |
| text_content | TEXT | NOT NULL | 字幕文本 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE subtitle_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    timeline_clip_id UUID NOT NULL REFERENCES timeline_clips(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    start_time DECIMAL(10,2) NOT NULL,
    end_time DECIMAL(10,2) NOT NULL,
    text_content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subtitle_contents_task ON subtitle_contents(export_task_id);
CREATE INDEX idx_subtitle_contents_clip ON subtitle_contents(timeline_clip_id);
```

### 5.4 封面导出

#### 5.4.1 封面配置表 (cover_configs)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 配置唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| enabled | BOOLEAN | NOT NULL | 是否生成封面 |
| cover_type | VARCHAR(50) | NOT NULL | 封面类型: auto_generate/custom/from_clip |
| source_clip_id | UUID | FK->timeline_clips | 来源片段ID |
| custom_image_url | VARCHAR(500) | | 自定义图片URL |
| title_text | VARCHAR(200) | | 标题文字 |
| subtitle_text | VARCHAR(200) | | 副标题文字 |
| template_id | VARCHAR(50) | | 模板ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE cover_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT false,
    cover_type VARCHAR(50) NOT NULL CHECK (cover_type IN ('auto_generate', 'custom', 'from_clip')),
    source_clip_id UUID REFERENCES timeline_clips(id) ON DELETE SET NULL,
    custom_image_url VARCHAR(500),
    title_text VARCHAR(200),
    subtitle_text VARCHAR(200),
    template_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cover_configs_task ON cover_configs(export_task_id);
```

### 5.5 导出结果

#### 5.5.1 导出文件表 (export_files)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 文件唯一标识 |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| file_type | VARCHAR(50) | NOT NULL | 文件类型: video/audio/subtitle/cover |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_path | VARCHAR(500) | NOT NULL | 文件路径 |
| file_url | VARCHAR(500) | NOT NULL | 文件URL |
| file_size | BIGINT | NOT NULL | 文件大小(字节) |
| duration | DECIMAL(10,2) | | 时长(秒) |
| resolution | VARCHAR(20) | | 分辨率 |
| format | VARCHAR(20) | | 格式 |
| storage_provider | VARCHAR(50) | NOT NULL | 存储提供商 |
| storage_path | VARCHAR(500) | | 存储路径 |
| is_downloadable | BOOLEAN | NOT NULL | 是否可下载 |
| download_count | INTEGER | NOT NULL | 下载次数 |
| expires_at | TIMESTAMP | | 过期时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE export_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('video', 'audio', 'subtitle', 'cover')),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    duration DECIMAL(10,2),
    resolution VARCHAR(20),
    format VARCHAR(20),
    storage_provider VARCHAR(50) NOT NULL,
    storage_path VARCHAR(500),
    is_downloadable BOOLEAN NOT NULL DEFAULT true,
    download_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_files_task ON export_files(export_task_id);
CREATE INDEX idx_export_files_type ON export_files(file_type);
```

### 5.6 导出记录

#### 5.6.1 导出历史表 (export_history)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| export_task_id | UUID | FK->export_tasks | 导出任务ID |
| export_config | JSONB | | 导出配置快照 |
| file_summary | JSONB | | 文件摘要 |
| status | VARCHAR(20) | NOT NULL | 状态 |
| exported_by | UUID | FK->users | 导出用户ID |
| exported_at | TIMESTAMP | NOT NULL | 导出时间 |

```sql
CREATE TABLE export_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    export_task_id UUID NOT NULL REFERENCES export_tasks(id) ON DELETE CASCADE,
    export_config JSONB,
    file_summary JSONB,
    status VARCHAR(20) NOT NULL,
    exported_by UUID REFERENCES users(id),
    exported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_history_unit ON export_history(creative_unit_id);
CREATE INDEX idx_export_history_exported ON export_history(exported_at DESC);
```

#### 5.6.2 下载记录表 (download_records)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| export_file_id | UUID | FK->export_files | 导出文件ID |
| user_id | UUID | FK->users | 下载用户ID |
| ip_address | VARCHAR(50) | | IP地址 |
| user_agent | TEXT | | 用户代理 |
| downloaded_at | TIMESTAMP | NOT NULL | 下载时间 |

```sql
CREATE TABLE download_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_file_id UUID NOT NULL REFERENCES export_files(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    downloaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_download_records_file ON download_records(export_file_id);
CREATE INDEX idx_download_records_user ON download_records(user_id);
```

---

## 模块六：资产库

### 6.1 资产库基础

#### 6.1.1 资产分类表 (asset_categories)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 分类唯一标识 |
| category_type | VARCHAR(20) | NOT NULL | 分类类型: character/style/voice |
| name | VARCHAR(100) | NOT NULL | 分类名称 |
| display_order | INTEGER | NOT NULL | 显示顺序 |
| parent_id | UUID | FK->asset_categories | 父分类ID |
| icon_url | VARCHAR(500) | | 图标URL |
| description | TEXT | | 描述 |
| is_active | BOOLEAN | NOT NULL | 是否启用 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE asset_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_type VARCHAR(20) NOT NULL CHECK (category_type IN ('character', 'style', 'voice')),
    name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    parent_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL,
    icon_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_asset_categories_type ON asset_categories(category_type);
CREATE INDEX idx_asset_categories_parent ON asset_categories(parent_id);
```

### 6.2 角色库

#### 6.2.1 角色资产表 (character_assets)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 角色资产唯一标识 |
| user_id | UUID | FK->users | 所有者用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID(NULL表示个人) |
| category_id | UUID | FK->asset_categories | 分类ID |
| character_name | VARCHAR(100) | NOT NULL | 角色名称 |
| character_type | VARCHAR(50) | NOT NULL | 角色类型 |
| description | TEXT | | 角色描述 |
| personality | TEXT[] | | 性格特征 |
| appearance | TEXT | | 外观描述 |
| image_url | VARCHAR(500) | | 主图URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| images | JSONB | | 多图数据(三视图等) |
| is_public | BOOLEAN | NOT NULL | 是否公开 |
| is_preset | BOOLEAN | NOT NULL | 是否预设 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE character_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    category_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL,
    character_name VARCHAR(100) NOT NULL,
    character_type VARCHAR(50) NOT NULL CHECK (character_type IN ('male', 'female', 'other')),
    description TEXT,
    personality TEXT[] DEFAULT '{}',
    appearance TEXT,
    image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    images JSONB,
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_preset BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_character_assets_user ON character_assets(user_id);
CREATE INDEX idx_character_assets_team ON character_assets(team_space_id);
CREATE INDEX idx_character_assets_category ON character_assets(category_id);
CREATE INDEX idx_character_assets_type ON character_assets(character_type);
CREATE INDEX idx_character_assets_public ON character_assets(is_public);
CREATE INDEX idx_character_assets_usage ON character_assets(usage_count DESC);
```

#### 6.2.2 角色资产版本表 (character_asset_versions)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 版本唯一标识 |
| character_asset_id | UUID | FK->character_assets | 角色资产ID |
| version_number | INTEGER | NOT NULL | 版本号 |
| snapshot_data | JSONB | NOT NULL | 快照数据 |
| change_description | TEXT | | 变更描述 |
| created_by | UUID | FK->users | 创建用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE character_asset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_asset_id UUID NOT NULL REFERENCES character_assets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    change_description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_asset_id, version_number)
);

CREATE INDEX idx_character_asset_versions_asset ON character_asset_versions(character_asset_id);
```

#### 6.2.3 角色使用记录表 (character_usage_records)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| character_asset_id | UUID | FK->character_assets | 角色资产ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| usage_context | JSONB | | 使用上下文 |
| used_at | TIMESTAMP | NOT NULL | 使用时间 |

```sql
CREATE TABLE character_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_asset_id UUID NOT NULL REFERENCES character_assets(id) ON DELETE CASCADE,
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    usage_context JSONB,
    used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_character_usage_records_asset ON character_usage_records(character_asset_id);
CREATE INDEX idx_character_usage_records_unit ON character_usage_records(creative_unit_id);
```

### 6.3 风格库

#### 6.3.1 风格资产表 (style_assets)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 风格资产唯一标识 |
| user_id | UUID | FK->users | 所有者用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| category_id | UUID | FK->asset_categories | 分类ID |
| style_name | VARCHAR(100) | NOT NULL | 风格名称 |
| description | TEXT | | 风格描述 |
| prompt_template | TEXT | NOT NULL | Prompt模板 |
| preview_image_url | VARCHAR(500) | | 预览图URL |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| color_palette | JSONB | | 色彩方案 |
| visual_keywords | TEXT[] | | 视觉关键词 |
| is_public | BOOLEAN | NOT NULL | 是否公开 |
| is_preset | BOOLEAN | NOT NULL | 是否预设 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE style_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    category_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL,
    style_name VARCHAR(100) NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    preview_image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    color_palette JSONB,
    visual_keywords TEXT[] DEFAULT '{}',
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_preset BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_style_assets_user ON style_assets(user_id);
CREATE INDEX idx_style_assets_team ON style_assets(team_space_id);
CREATE INDEX idx_style_assets_category ON style_assets(category_id);
CREATE INDEX idx_style_assets_public ON style_assets(is_public);
CREATE INDEX idx_style_assets_usage ON style_assets(usage_count DESC);
```

#### 6.3.2 风格资产版本表 (style_asset_versions)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 版本唯一标识 |
| style_asset_id | UUID | FK->style_assets | 风格资产ID |
| version_number | INTEGER | NOT NULL | 版本号 |
| snapshot_data | JSONB | NOT NULL | 快照数据 |
| change_description | TEXT | | 变更描述 |
| created_by | UUID | FK->users | 创建用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE style_asset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    style_asset_id UUID NOT NULL REFERENCES style_assets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    change_description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(style_asset_id, version_number)
);

CREATE INDEX idx_style_asset_versions_asset ON style_asset_versions(style_asset_id);
```

#### 6.3.3 风格使用记录表 (style_usage_records)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| style_asset_id | UUID | FK->style_assets | 风格资产ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| usage_context | JSONB | | 使用上下文 |
| used_at | TIMESTAMP | NOT NULL | 使用时间 |

```sql
CREATE TABLE style_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    style_asset_id UUID NOT NULL REFERENCES style_assets(id) ON DELETE CASCADE,
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    usage_context JSONB,
    used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_style_usage_records_asset ON style_usage_records(style_asset_id);
CREATE INDEX idx_style_usage_records_unit ON style_usage_records(creative_unit_id);
```

### 6.4 音色库

#### 6.4.1 音色资产表 (voice_assets)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 音色资产唯一标识 |
| user_id | UUID | FK->users | 所有者用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| category_id | UUID | FK->asset_categories | 分类ID |
| voice_name | VARCHAR(100) | NOT NULL | 音色名称 |
| voice_type | VARCHAR(50) | NOT NULL | 音色类型: narration/dialogue |
| voice_id | VARCHAR(50) | | 系统音色ID |
| description | TEXT | | 音色描述 |
| audio_sample_url | VARCHAR(500) | | 试听音频URL |
| gender | VARCHAR(20) | | 性别 |
| age_range | VARCHAR(20) | | 年龄段 |
| tone | VARCHAR(50) | | 音调 |
| language | VARCHAR(20) | | 语言 |
| is_public | BOOLEAN | NOT NULL | 是否公开 |
| is_preset | BOOLEAN | NOT NULL | 是否预设 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE voice_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    category_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL,
    voice_name VARCHAR(100) NOT NULL,
    voice_type VARCHAR(50) NOT NULL CHECK (voice_type IN ('narration', 'dialogue')),
    voice_id VARCHAR(50),
    description TEXT,
    audio_sample_url VARCHAR(500),
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'neutral')),
    age_range VARCHAR(20),
    tone VARCHAR(50),
    language VARCHAR(20),
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_preset BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_voice_assets_user ON voice_assets(user_id);
CREATE INDEX idx_voice_assets_team ON voice_assets(team_space_id);
CREATE INDEX idx_voice_assets_category ON voice_assets(category_id);
CREATE INDEX idx_voice_assets_type ON voice_assets(voice_type);
CREATE INDEX idx_voice_assets_public ON voice_assets(is_public);
CREATE INDEX idx_voice_assets_usage ON voice_assets(usage_count DESC);
```

#### 6.4.2 音色资产版本表 (voice_asset_versions)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 版本唯一标识 |
| voice_asset_id | UUID | FK->voice_assets | 音色资产ID |
| version_number | INTEGER | NOT NULL | 版本号 |
| snapshot_data | JSONB | NOT NULL | 快照数据 |
| change_description | TEXT | | 变更描述 |
| created_by | UUID | FK->users | 创建用户ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE voice_asset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voice_asset_id UUID NOT NULL REFERENCES voice_assets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    change_description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(voice_asset_id, version_number)
);

CREATE INDEX idx_voice_asset_versions_asset ON voice_asset_versions(voice_asset_id);
```

#### 6.4.3 音色使用记录表 (voice_usage_records)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| voice_asset_id | UUID | FK->voice_assets | 音色资产ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| usage_context | JSONB | | 使用上下文 |
| used_at | TIMESTAMP | NOT NULL | 使用时间 |

```sql
CREATE TABLE voice_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voice_asset_id UUID NOT NULL REFERENCES voice_assets(id) ON DELETE CASCADE,
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    usage_context JSONB,
    used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_voice_usage_records_asset ON voice_usage_records(voice_asset_id);
CREATE INDEX idx_voice_usage_records_unit ON voice_usage_records(creative_unit_id);
```

### 6.5 音乐库

#### 6.5.1 音乐资产表 (music_assets)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 音乐资产唯一标识 |
| user_id | UUID | FK->users | 所有者用户ID |
| team_space_id | UUID | FK->team_spaces | 团队空间ID |
| category_id | UUID | FK->asset_categories | 分类ID |
| music_name | VARCHAR(200) | NOT NULL | 音乐名称 |
| description | TEXT | | 音乐描述 |
| audio_url | VARCHAR(500) | NOT NULL | 音频URL |
| duration | DECIMAL(5,2) | NOT NULL | 时长(秒) |
| genre | VARCHAR(50) | | 流派 |
| mood | VARCHAR(50) | | 情绪 |
| tempo | VARCHAR(50) | | 节奏 |
| instruments | TEXT[] | | 乐器 |
| thumbnail_url | VARCHAR(500) | | 缩略图URL |
| is_public | BOOLEAN | NOT NULL | 是否公开 |
| is_preset | BOOLEAN | NOT NULL | 是否预设 |
| usage_count | INTEGER | NOT NULL | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

```sql
CREATE TABLE music_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_space_id UUID REFERENCES team_spaces(id) ON DELETE CASCADE,
    category_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL,
    music_name VARCHAR(200) NOT NULL,
    description TEXT,
    audio_url VARCHAR(500) NOT NULL,
    duration DECIMAL(5,2) NOT NULL,
    genre VARCHAR(50),
    mood VARCHAR(50),
    tempo VARCHAR(50),
    instruments TEXT[] DEFAULT '{}',
    thumbnail_url VARCHAR(500),
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_preset BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_music_assets_user ON music_assets(user_id);
CREATE INDEX idx_music_assets_team ON music_assets(team_space_id);
CREATE INDEX idx_music_assets_category ON music_assets(category_id);
CREATE INDEX idx_music_assets_genre ON music_assets(genre);
CREATE INDEX idx_music_assets_mood ON music_assets(mood);
CREATE INDEX idx_music_assets_public ON music_assets(is_public);
CREATE INDEX idx_music_assets_usage ON music_assets(usage_count DESC);
```

#### 6.5.2 音乐使用记录表 (music_usage_records)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| music_asset_id | UUID | FK->music_assets | 音乐资产ID |
| creative_unit_id | UUID | FK->creative_units | 创作单元ID |
| usage_context | JSONB | | 使用上下文 |
| used_at | TIMESTAMP | NOT NULL | 使用时间 |

```sql
CREATE TABLE music_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    music_asset_id UUID NOT NULL REFERENCES music_assets(id) ON DELETE CASCADE,
    creative_unit_id UUID NOT NULL REFERENCES creative_units(id) ON DELETE CASCADE,
    usage_context JSONB,
    used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_music_usage_records_asset ON music_usage_records(music_asset_id);
CREATE INDEX idx_music_usage_records_unit ON music_usage_records(creative_unit_id);
```

### 6.6 资产收藏与标签

#### 6.6.1 资产收藏表 (asset_favorites)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 收藏唯一标识 |
| user_id | UUID | FK->users | 用户ID |
| asset_type | VARCHAR(20) | NOT NULL | 资产类型 |
| asset_id | UUID | NOT NULL | 资产ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE asset_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('character', 'style', 'voice', 'music')),
    asset_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, asset_type, asset_id)
);

CREATE INDEX idx_asset_favorites_user ON asset_favorites(user_id);
CREATE INDEX idx_asset_favorites_asset ON asset_favorites(asset_type, asset_id);
```

#### 6.6.2 资产标签表 (asset_tags)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 标签唯一标识 |
| tag_name | VARCHAR(50) | NOT NULL | 标签名称 |
| tag_type | VARCHAR(20) | NOT NULL | 标签类型 |
| color | VARCHAR(20) | | 标签颜色 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE asset_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(50) NOT NULL,
    tag_type VARCHAR(20) NOT NULL CHECK (tag_type IN ('character', 'style', 'voice', 'music')),
    color VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tag_name, tag_type)
);

CREATE INDEX idx_asset_tags_type ON asset_tags(tag_type);
```

#### 6.6.3 资产标签关联表 (asset_tag_relations)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 关联唯一标识 |
| asset_type | VARCHAR(20) | NOT NULL | 资产类型 |
| asset_id | UUID | NOT NULL | 资产ID |
| tag_id | UUID | FK->asset_tags | 标签ID |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

```sql
CREATE TABLE asset_tag_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('character', 'style', 'voice', 'music')),
    asset_id UUID NOT NULL,
    tag_id UUID NOT NULL REFERENCES asset_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_type, asset_id, tag_id)
);

CREATE INDEX idx_asset_tag_relations_asset ON asset_tag_relations(asset_type, asset_id);
CREATE INDEX idx_asset_tag_relations_tag ON asset_tag_relations(tag_id);
```

---

*当前已完成: 模块一 - 项目与任务管理，模块二 - 输入与素材导入，模块三 - 生成素材管理，模块四 - 剪辑与编排，模块五 - 导出与交付，模块六 - 资产库*

---

## 总体数据库设计概览

### ER关系图（文字描述）

```
用户与权限层
├── users (用户表)
│   ├── user_sessions (会话)
│   ├── space_usage_history (空间使用记录)
│   └── user_quotas (配额)
├── team_spaces (团队空间)
│   ├── team_members (成员)
│   └── team_quotas (配额)

创作核心层
├── creative_units (创作单元/任务)
│   ├── task_collaborators (协作者)
│   ├── task_stage_history (阶段历史)
│   └── task_collaborators (协作者)

输入层
├── creative_inputs (创作输入)
├── input_configs (输入配置)
├── attachments (附件文件)
│   └── attachment_labels (附件标注)
├── model_configs (模型配置)
├── style_configs (风格配置)
├── preset_styles (预设风格)
├── aspect_ratio_configs (画幅配置)
├── duration_configs (时长配置)
├── subject_configs (主体配置)
└── user_config_templates (配置模板)

素材生成层
├── material_packages (素材包)
│   └── material_package_history (包历史)
├── generation_tasks (生成任务)
├── storylines (故事梗概)
├── art_styles (美术风格)
├── characters (角色)
│   ├── character_image_candidates (角色图片候选)
│   └── character_voice_candidates (角色音色候选)
├── scenes (场景)
│   └── scene_image_candidates (场景图片候选)
├── storyboards (分镜剧本)
├── element_modifications (元素修改记录)
└── system_conversations (系统对话)

剪辑编排层
├── editing_projects (编辑项目)
├── timeline_clips (时间轴片段)
│   ├── clip_image_candidates (画面候选)
│   ├── clip_video_candidates (视频候选)
│   ├── clip_narrations (旁白)
│   ├── clip_dialogues (对话)
│   └── clip_edit_configs (编辑配置)
├── video_generation_tasks (视频生成任务)
├── background_music (背景音乐)
├── bgm_candidates (BGM候选)
└── editing_history (编辑历史)

导出交付层
├── export_tasks (导出任务)
│   ├── export_configs (导出配置)
│   ├── subtitle_export_configs (字幕配置)
│   ├── cover_configs (封面配置)
│   ├── export_files (导出文件)
│   └── export_history (导出历史)
├── subtitle_contents (字幕内容)
└── download_records (下载记录)

资产库层
├── asset_categories (资产分类)
├── character_assets (角色资产)
│   ├── character_asset_versions (版本)
│   └── character_usage_records (使用记录)
├── style_assets (风格资产)
│   ├── style_asset_versions (版本)
│   └── style_usage_records (使用记录)
├── voice_assets (音色资产)
│   ├── voice_asset_versions (版本)
│   └── voice_usage_records (使用记录)
├── music_assets (音乐资产)
│   └── music_usage_records (使用记录)
├── asset_favorites (收藏)
├── asset_tags (标签)
└── asset_tag_relations (标签关联)
```

### 数据流向图

```
用户输入 → creative_inputs → attachments/input_configs
                ↓
        material_packages ← generation_tasks
                ↓
    storylines/art_styles/characters/scenes/storyboards
                ↓
        editing_projects ← timeline_clips
                ↓
        export_tasks → export_files
                ↓
            用户下载
```

### 核心表关系

1. **creative_units** 是核心创作单元，关联所有其他表
2. **material_packages** 存储素材包版本，包含所有生成素材
3. **editing_projects** 基于素材包创建剪辑项目
4. **export_tasks** 基于剪辑项目导出最终文件
5. **资产库表** 被多个模块引用复用
