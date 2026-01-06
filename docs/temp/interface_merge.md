# 一站式视频生成平台 - 合并接口文档（HTML + PRD）

> 目的：将前端 HTML 字段清单与 PRD 接口定义合并，形成可执行的接口设计基线。
> 本文以 PRD 为主干，补充前端页面已使用字段，并通过映射表统一命名。

---

## 0. 合并说明

- **来源**：`interface_from_html.md` + `interface_from_prd.md`
- **合并原则**：
  - PRD 接口为主，HTML 字段为必需补充
  - 已出现命名冲突时，以 PRD 为标准命名，前端自行映射，不在接口返回别名字段
  - 所有时间字段默认 **ISO 8601** 字符串
- **注释标记说明**：
  - `[PRD]` 来自 PRD 的接口/字段
  - `[HTML]` 来自前端页面字段清单
  - `[MERGE]` 合并/衍生后的字段或约定

---

## 1. 页面数据依赖速览（来自 HTML）

- **登录页**：`phone` / `code` / `invite`；支持个人/团队模式切换；`sessionStorage` 维护 `authenticated` / `userType` / `currentSpace`
- **落地页**：用户信息 + 积分/配额 + 创建项目（`prompt`, `mode`, `model`）
- **素材页**：`Conversation[]` + `AssetPackage[]` + 角色/场景/分镜候选编辑
- **编辑器**：`Project` + `Shot[]` + `TimelineClip[]` + `AudioTrack[]` + 导出任务
- **资产库**：查询/筛选/批量操作；分类包含 `role/style/scene/template/voice`
- **空间页**：`User` + `Space` + `Journey[]`

---

## 2. 术语对齐与实体映射

| 术语 | 说明 | 映射/别名 |
|---|---|---|
| Project | 项目/创作单元 | HTML 中 `Journey` 卡片数据 [HTML] |
| MaterialPackage | 素材包 | HTML 中 `AssetPackage` [HTML] |
| Role | 角色 | PRD `Character` 的 UI 简化版本 [MERGE] |
| Storyboard | 分镜文本 | HTML `AssetPackage.storyboard[]` [HTML] |
| TimelineClip | 时间轴片段 | 编辑器底部 clips [HTML][PRD] |
| Candidate | 候选 | 角色/场景/分镜的候选图/音/文 [HTML] |
| Asset | 资产 | 统一资产库（role/style/scene/template/voice）[MERGE] |

**命名约定（建议）**：API 使用 `snake_case`，前端可映射为 `camelCase`。

**前端字段映射（参考）**：

| 前端字段 | API 字段 | 说明 |
|---|---|---|
| `User.avatar` | `User.avatar_url` | 头像地址统一为 `avatar_url` |
| `User.userType` | `User.user_type` | 类型命名统一为 `snake_case` |
| `Session.currentSpace` | `current_space` | 结构保持一致 |
| `Journey.title` | `Project.name` | 项目标题 |
| `Journey.desc` | `Project.description` | 若为空可由状态生成文案 |
| `Journey.lastPkgId` | `Project.last_material_package_id` | 素材包关联 |
| `AssetPackage.title` | `MaterialPackage.package_name` | 素材包名称 |
| `AssetPackage.roles` | `materials.characters` | 结构需前端适配 |
| `AssetPackage.scenes` | `materials.scenes` | 结构需前端适配 |
| `AssetPackage.storyboard` | `materials.storyboards` | 结构需前端适配 |
| `Candidate.text` | `TextCandidate.content` | 文本候选统一为 `content` |
| `TimelineClip.img` | `thumbnail_url` | 统一缩略图字段 |
| `TimelineClip.videoGenerated` | `selected_video_id != null` | 状态可推导 |
| `Asset.name` | `Asset.name` | 接口统一使用 `name` |
| `Asset.desc` | `description` | 统一资产描述字段 |
| `Asset.preview` | `content_url` / `thumbnail_url` | 视资源类型选择 |
| `Asset.type` | `type` | roles/styles/scenes/voices/templates -> role/style/scene/voice/template |

---

## 3. 通用规范（合并）

### 3.1 Base URL

```
/api/v1
```

### 3.2 统一响应

```typescript
// 成功响应
{
  code: 0,
  message: 'success',
  data: { ... }
}

// 失败响应
{
  code: 1001,
  message: '错误信息',
  data: null
}
```

### 3.3 通用错误码（沿用 PRD）

- 0 成功
- 1001 参数错误
- 1002 未登录
- 1003 无权限
- 1004 资源不存在
- 1005 资源已存在
- 1006 余额/配额不足
- 1007 文件上传失败
- 1008 生成任务失败
- 1009 导出任务失败
- 1010 邀请码无效

### 3.4 分页

```typescript
interface PageParams {
  page: number;      // 页码，从1开始
  page_size: number; // 每页数量
}

interface PageResponse<T> {
  list: T[];
  total: number;
  page: number;
  page_size: number;
}
```

### 3.5 媒体 URL 约定

- 所有 `image_url` / `audio_url` / `video_url` / `file_url` 字段均为**短期签名链接**
- 服务端可在同级对象返回 `url_expires_at`（ISO 8601）提示前端刷新时机

### 3.6 配额扣减规则（v0）

- 仅在**任务成功完成**时扣减配额
- 失败或中断的任务不扣减配额

### 3.7 v0 已实现接口示例（Mock）

> 说明：以下为 v0 已落地子集示例，均使用统一响应壳 `{code,message,data}`。

#### 登录

```typescript
// POST /api/v1/auth/login
Request:
{
  "phone": "13800000000",
  "code": "123456",
  "invite_code": "TEAM123" // 可选
}

Response:
{
  "code": 0,
  "message": "success",
  "data": {
    "user": { "id": "uuid", "username": "user_0000", "user_type": "team" },
    "session_token": "token",
    "refresh_token": "refresh",
    "current_space": { "type": "team", "space_id": null, "space_name": "Team Space" },
    "authenticated": true
  }
}
```

#### 项目列表 / 创建 / 详情

```typescript
// GET /api/v1/projects?page=1&page_size=20
Response:
{
  "code": 0,
  "message": "success",
  "data": { "list": [], "total": 0, "page": 1, "page_size": 20 }
}

// POST /api/v1/projects
Request:
{ "name": "Untitled Project", "space_type": "personal" }

Response:
{ "code": 0, "message": "success", "data": { "id": "uuid", "status": "draft" } }

// GET /api/v1/projects/:project_id
Response:
{ "code": 0, "message": "success", "data": { "id": "uuid", "status": "draft" } }
```

#### 素材包

```typescript
// GET /api/v1/projects/:project_id/material-packages
Response:
{ "code": 0, "message": "success", "data": { "list": [], "total": 0 } }

// GET /api/v1/material-packages/:package_id
Response:
{ "code": 0, "message": "success", "data": { "id": "uuid", "status": "generating" } }
```

#### 生成（Mock）

```typescript
// POST /api/v1/generation/start
Request:
{ "project_id": "uuid" }

Response:
{ "code": 0, "message": "success", "data": { "id": "task_id", "status": "pending" } }

// GET /api/v1/generation/progress/:project_id
Response:
{ "code": 0, "message": "success", "data": { "list": [] } }

// POST /api/v1/generation/retry/:task_id
// POST /api/v1/generation/skip/:task_id
```

---

## 4. 核心数据模型（合并注释版）

### 4.1 User / Session

```typescript
interface User {
  id: string;                // [PRD] 主键
  uid?: string;              // [HTML] 前端展示用，可与 id 相同
  username: string;          // [PRD][HTML]
  phone?: string;            // [HTML] 登录用
  email?: string;            // [PRD]
  avatar_url?: string;       // [PRD]
  membership?: string;       // [HTML] 会员文案
  user_type: 'personal' | 'team'; // [PRD][HTML]
  points?: {                 // [HTML] 积分显示
    current: number;
    paid: number;
    bonus: number;
  };
  quota_info?: {             // [PRD] 配额
    daily_limit: number;
    used: number;
    reset_at: string;
    remaining?: number;      // [MERGE] 便于前端直接显示
  };
  created_at?: string;
  updated_at?: string;
}

interface Session {
  authenticated: boolean;     // [HTML] sessionStorage
  session_token: string;      // [PRD]
  refresh_token?: string;     // [PRD]
  user_type: 'personal' | 'team'; // [HTML]
  current_space: CurrentSpace; // [PRD][HTML]
}

interface CurrentSpace {
  type: 'personal' | 'team';  // [PRD]
  space_id?: string;          // [PRD] team 时必填
  space_name?: string;        // [PRD]
}
```

### 4.2 TeamSpace / Space

```typescript
interface TeamSpace {
  id: string;                 // [PRD]
  name: string;               // [PRD]
  logo_url?: string;          // [PRD]
  role?: 'admin' | 'editor' | 'viewer'; // [PRD]
  members?: number;           // [HTML] 成员数
  recent?: boolean;           // [HTML] 是否最近使用
  last_accessed?: string;     // [PRD]
}
```

### 4.3 Project（= Journey）

```typescript
interface Project {
  id: string;                 // [PRD]
  user_id?: string;           // [PRD]
  team_space_id?: string;     // [PRD]
  name: string;               // [PRD]
  description?: string;       // [PRD]
  status: 'draft' | 'generating' | 'editing' | 'completed' | 'exported'; // [PRD]
  stage: 'input' | 'generating' | 'editing' | 'completed';              // [PRD]
  progress: number;           // [PRD]
  tags: string[];             // [PRD]
  input_config: InputConfig;  // [PRD]
  thumbnail_url?: string;     // [PRD]
  last_material_package_id?: string; // [HTML] Journey 卡片关联素材包
  updated_at: string;         // [PRD]
  created_at: string;         // [PRD]
}

interface InputConfig {
  text_to_image_model?: string;   // [PRD]
  image_to_image_model?: string;  // [PRD]
  style_id?: string;              // [PRD]
  aspect_ratio: string;           // [PRD]
  duration_type: 'smart' | 'custom'; // [PRD]
  duration_seconds?: number;      // [PRD]
  subject_id?: string;            // [PRD] 引用资产库角色
  language?: string;              // [PRD]
  subtitle_enabled?: boolean;     // [PRD]
}
```

### 4.4 MaterialPackage（前端历史称 AssetPackage）

```typescript
interface MaterialPackage {
  id: string;                 // [PRD]
  project_id: string;         // [PRD]
  parent_id?: string;         // [MERGE] 版本关联（可选）
  package_name: string;       // [PRD]
  status: 'generating' | 'completed' | 'failed'; // [PRD]
  is_active: boolean;         // [PRD]
  summary?: string;           // [PRD][HTML]
  materials: Materials;       // [PRD]
  generated_at?: string;      // [PRD]
  created_at: string;         // [PRD]
}

interface Materials {
  storyline?: Storyline;      // [PRD]
  art_style?: ArtStyle;        // [PRD]
  characters?: Character[];    // [PRD]
  scenes?: Scene[];            // [PRD]
  storyboards?: Storyboard[];  // [PRD]
}

interface Storyline {
  id: string;                 // [PRD]
  title: string;              // [PRD]
  content: string;            // [PRD]
  summary: string;            // [PRD]
  genre: string;              // [PRD]
  tone: string;               // [PRD]
  is_selected: boolean;       // [PRD]
}

interface ArtStyle {
  id: string;                 // [PRD]
  style_name: string;         // [PRD]
  description: string;        // [PRD]
  prompt_template: string;    // [PRD]
  reference_image_url: string;// [PRD]
  is_selected: boolean;       // [PRD]
}

interface Character {
  id: string;                 // [PRD]
  character_name: string;     // [PRD]
  character_type: 'protagonist' | 'supporting' | 'extras'; // [PRD]
  description: string;        // [PRD]
  personality: string[];      // [PRD]
  appearance: string;         // [PRD]
  voice_style?: string;       // [PRD]
  images: ImageCandidate[];   // [PRD]
  voices?: VoiceCandidate[];  // [PRD]
  is_selected: boolean;       // [PRD]
}

interface Role {              // [HTML] 前端本地结构，不作为接口返回
  name: string;
  visuals: ImageCandidate[];
  voices: VoiceCandidate[];
}

interface Scene {
  id: string;                 // [PRD]
  scene_name: string;         // [PRD]
  scene_type: 'indoor' | 'outdoor' | 'abstract'; // [PRD]
  description?: string;       // [PRD]
  atmosphere?: string;        // [PRD]
  lighting?: string;          // [PRD]
  camera_angle?: string;      // [PRD]
  images: ImageCandidate[];   // [PRD]
  is_selected: boolean;       // [PRD]
}

interface Storyboard {
  id: string;                 // [PRD]
  shot_number: number;        // [PRD]
  description?: string;       // [PRD]
  dialogue?: string;          // [PRD]
  action?: string;            // [PRD]
  duration?: number;          // [PRD]
  camera_movement?: string;   // [PRD]
  transition?: string;        // [PRD]
  reference_image_url?: string; // [PRD]
  candidates?: TextCandidate[];  // [MERGE] 当前候选集（有限数量）
  is_selected: boolean;       // [PRD]
}
```

### 4.5 Candidate（候选）

```typescript
// [MERGE] 候选集仅保留当前有限数量（服务端配置上限）
interface CandidateBase {
  id?: string;                // [MERGE]
  tag?: string;               // [HTML] 如“原图/微调/新/当前”
  prompt?: string;            // [HTML] 生成提示词
  is_selected?: boolean;      // [PRD]
  created_at?: string;        // [PRD]
}

interface ImageCandidate extends CandidateBase {
  image_url?: string;         // [PRD]
  thumbnail_url?: string;     // [PRD]
}

interface VoiceCandidate extends CandidateBase {
  voice_id?: string;          // [PRD]
  voice_name?: string;        // [PRD]
  audio_sample_url?: string;  // [PRD]
}

interface TextCandidate extends CandidateBase {
  content?: string;           // [PRD] 文本内容
}
```

### 4.6 Conversation / Todo

```typescript
interface Conversation {
  id: string;                 // [HTML]
  display_index?: number;     // [HTML]
  user_prompt: string;        // [HTML]
  sys_text: string;           // [HTML]
  status: 'pending' | 'loading' | 'done' | 'fail'; // [HTML]
  asset_package_id?: string;  // [HTML] 关联素材包
  todo_list?: Array<{
    title: string;            // [HTML]
    status: 'pending' | 'loading' | 'done';
  }>; // [HTML]
}
```

### 4.7 TimelineClip / Shot / Audio

```typescript
interface TimelineClip {
  id: string;                 // [PRD]
  project_id?: string;        // [PRD]
  shot_number: number;        // [PRD]
  clip_type: 'image' | 'video'; // [PRD]
  duration: number;           // [PRD]
  start_time: number;         // [PRD]
  end_time: number;           // [PRD]
  description: string;        // [PRD]
  dialogue?: string;          // [PRD]
  transition?: string;        // [PRD]
  transition_duration?: number; // [PRD]
  selected_image_id?: string; // [PRD]
  selected_video_id?: string; // [PRD]
  thumbnail_url?: string;     // [PRD]
  config: EditConfig;         // [PRD]
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

interface Shot {              // [HTML] 前端聚合结构，不作为接口返回
  index: number;
  img?: string;
  video_path?: string;
  video?: string;
  video_generated?: boolean;
  title?: string;
  prompt?: string;
  narration?: string;
  voice_settings?: {
    name?: string;
    tags?: string[];
    volume?: number;
    speed?: number;
    emotion?: string;
  };
  music?: {
    mode?: 'ai' | 'library' | 'uploaded';
    prompt?: string;
    audio_src?: string;
    volume?: number;
  };
}

interface AudioTrack {        // [HTML] 前端聚合结构，不作为接口返回
  type: 'bgm' | 'tts';
  src: string;
  volume: number;             // 0-100
  duration?: number;
}
```

### 4.8 Asset（资产库）

```typescript
interface Asset {
  id: string;                 // [PRD]
  user_id?: string;           // [PRD]
  type: 'role' | 'style' | 'scene' | 'template' | 'voice'; // [MERGE] 统一资产类型
  name: string;               // [MERGE]
  description?: string;       // [PRD]
  category_id?: string;       // [MERGE] 分类ID（可选）
  content_url?: string;       // [PRD]
  thumbnail_url?: string;     // [PRD]
  prompt_template?: string;   // [PRD]
  tags?: string[];            // [HTML]
  is_preset?: boolean;        // [PRD]
  is_public?: boolean;        // [PRD]
  usage_count?: number;       // [PRD][HTML]
  created_at?: string;        // [PRD]
  updated_at?: string;        // [PRD]
  attributes?: Record<string, any>; // [PRD]
}
```

---

## 5. 接口定义（合并版）

> 说明：保持 PRD 路由结构；若 HTML 有额外字段/流程，则在接口中补充说明。

### 5.1 用户与空间

#### 5.1.1 登录

```typescript
// POST /api/v1/auth/login
interface Request {
  phone: string;       // [HTML] 手机号
  code: string;        // [HTML] 短信验证码
  invite_code?: string;// [HTML] 团队邀请码（可选）
}

interface Response {
  user: User;                         // [MERGE]
  session_token: string;              // [PRD]
  refresh_token: string;              // [PRD]
  current_space: CurrentSpace;        // [PRD]
  authenticated: boolean;             // [HTML]
}
```

> 注释：v0 阶段仅支持手机验证码登录，不支持账号密码登录。

#### 5.1.2 获取当前用户

```typescript
// GET /api/v1/user/me
interface Response extends User {}
```

> 注释：此接口需包含 `points`、`membership`、`uid` 等前端显示字段 [HTML]。

#### 5.1.3 更新用户信息

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

#### 5.1.4 刷新令牌

```typescript
// POST /api/v1/auth/refresh
interface Request {
  refresh_token: string;
}
```

#### 5.1.5 团队空间相关

```typescript
// POST /api/v1/team/join
interface Request {
  invite_code: string; // [PRD][HTML]
}

// GET /api/v1/team/spaces
// Response.list[] 需包含 members / recent 字段 [HTML]

// POST /api/v1/team/switch
interface Request {
  space_type: 'personal' | 'team';
  space_id?: string;
}
```

---

### 5.2 项目（Project / Journey）

#### 5.2.1 获取项目列表

```typescript
// GET /api/v1/projects
interface Query extends PageParams {
  space_type?: 'personal' | 'team';
  team_space_id?: string;
  status?: 'draft' | 'generating' | 'editing' | 'completed' | 'exported';
  keyword?: string;
}

interface Response extends PageResponse<Project> {}
```

> 注释：HTML 的 `Journey` 列表可直接用此接口映射，需包含 `last_material_package_id`/`desc` 等字段 [HTML]。

#### 5.2.2 创建项目

```typescript
// POST /api/v1/projects
interface Request {
  name?: string;
  space_type?: 'personal' | 'team';
  team_space_id?: string;
}
```

#### 5.2.3 获取项目详情

```typescript
// GET /api/v1/projects/:project_id
interface Response extends Project {
  metadata?: {
    total_duration?: number;
    video_count?: number;
    export_count?: number;
  };
  started_at?: string;
  completed_at?: string;
}
```

#### 5.2.4 更新/删除项目

```typescript
// PUT /api/v1/projects/:project_id
interface Request {
  name?: string;
  description?: string;
  tags?: string[];
}

// DELETE /api/v1/projects/:project_id
```

---

### 5.3 输入与素材导入

#### 5.3.1 获取输入配置选项

```typescript
// GET /api/v1/input/options
// 按 PRD 返回 models / styles / aspect_ratios / durations / subjects
```

#### 5.3.2 提交创作输入

```typescript
// POST /api/v1/input/submit
interface Request {
  input_mode: 'general' | 'professional'; // [HTML] mode
  input_type: 'text' | 'script' | 'storyboard';
  content: string; // [PRD] 前端 prompt 可映射到此
  attachments?: Array<{
    id: string;
    label?: string;
  }>;
  config: InputConfig;
}
```

> 注释：HTML 落地页用 `prompt` + `mode` + `model`；建议前端将 `prompt` 映射到 `content`，`model` 映射到 `config.text_to_image_model`。

#### 5.3.3 附件管理

```typescript
// GET /api/v1/attachments/upload-config
// POST /api/v1/attachments
// PUT /api/v1/attachments/:attachment_id
// DELETE /api/v1/attachments/:attachment_id
// GET /api/v1/projects/:project_id/attachments
```

---

### 5.4 生成任务与素材包（MaterialPackage，前端历史称 AssetPackage）

#### 5.4.1 生成任务

```typescript
// POST /api/v1/generation/start
// GET  /api/v1/generation/progress/:project_id
// POST /api/v1/generation/retry/:task_id
// POST /api/v1/generation/skip/:task_id
```

#### 5.4.2 素材包列表/切换/派生

```typescript
// GET  /api/v1/projects/:project_id/material-packages
// POST /api/v1/material-packages/:package_id/switch
// PUT  /api/v1/material-packages/:package_id
interface Request {
  package_name?: string; // [PRD]
  summary?: string;      // [HTML]
}

// POST /api/v1/material-packages/:package_id/save-new
interface Response {
  new_package_id: string;
  parent_id?: string;    // [MERGE] 关联上一版本
}
```

#### 5.4.3 素材包详情

```typescript
// GET /api/v1/material-packages/:package_id
interface Response extends MaterialPackage {}
```

> 注释：接口仅返回 `materials` 标准结构，前端通过映射适配 `roles/scenes/storyboard` 等旧字段。

#### 5.4.4 文本/图片/音色修改与候选

```typescript
// POST /api/v1/material-packages/:package_id/modify/text
// POST /api/v1/material-packages/:package_id/regenerate/image
// POST /api/v1/material-packages/:package_id/switch-voice
// POST /api/v1/material-packages/:package_id/select-candidate
// POST /api/v1/material-packages/:package_id/replace-from-asset
```

#### 5.4.5 对话记录

```typescript
// GET /api/v1/projects/:project_id/conversations
```

> 注释：HTML `Conversation` 有 `todo_list`，可扩展 `context_data` 或单独字段承载。

---

### 5.5 剪辑与编排（Timeline）

#### 5.5.1 时间轴

```typescript
// GET /api/v1/projects/:project_id/timeline
// PUT /api/v1/timeline-clips/:clip_id/duration
// POST /api/v1/projects/:project_id/timeline/reorder
// DELETE /api/v1/timeline-clips/:clip_id
```

#### 5.5.2 分镜候选与视频生成

```typescript
// GET  /api/v1/timeline-clips/:clip_id/candidates
// POST /api/v1/timeline-clips/:clip_id/regenerate-image
// POST /api/v1/timeline-clips/:clip_id/generate-video
// POST /api/v1/projects/:project_id/generate-batch-videos
// GET  /api/v1/video-generation-tasks/:task_id
// POST /api/v1/timeline-clips/:clip_id/apply-candidate
```

#### 5.5.3 音频配置

```typescript
// GET /api/v1/timeline-clips/:clip_id/audio
// PUT /api/v1/timeline-clips/:clip_id/narration
// POST /api/v1/timeline-clips/:clip_id/narration/custom-audio
// PUT /api/v1/timeline-clips/:clip_id/dialogue/:dialogue_id
// GET /api/v1/projects/:project_id/bgm
// PUT /api/v1/projects/:project_id/bgm
// POST /api/v1/projects/:project_id/generate-bgm
```

> 注释：HTML 中 `AudioTrack` 可由 `bgm` + `narration/dialogue` 聚合生成；优先级为镜头级覆盖 > 角色级默认 > 全局默认。

#### 5.5.4 画面编辑

```typescript
// PUT /api/v1/timeline-clips/:clip_id/edit-config
```

---

### 5.6 导出与交付

```typescript
// POST /api/v1/projects/:project_id/export
// GET  /api/v1/export-tasks/:task_id
// POST /api/v1/export-tasks/:task_id/cancel
// GET  /api/v1/projects/:project_id/export-files
// GET  /api/v1/export-files/:file_id/download-url
// GET  /api/v1/projects/:project_id/export-history
```

---

### 5.7 资产库

```typescript
// GET /api/v1/assets
interface AssetQuery extends PageParams {
  type?: 'role' | 'style' | 'scene' | 'template' | 'voice';
  keyword?: string;
  category_id?: string;
  tags?: string[];
  is_preset?: boolean;
  is_public?: boolean;
}

// POST /api/v1/assets
interface CreateAssetRequest {
  type: 'role' | 'style' | 'scene' | 'template' | 'voice';
  name: string;
  description?: string;
  category_id?: string;
  content_url?: string;
  thumbnail_url?: string;
  prompt_template?: string;
  tags?: string[];
  is_preset?: boolean;
  is_public?: boolean;
  attributes?: Record<string, any>;
}

// PUT /api/v1/assets/:asset_id
// DELETE /api/v1/assets/:asset_id

// POST /api/v1/assets/batch-delete
interface BatchDeleteRequest {
  type: 'role' | 'style' | 'scene' | 'template' | 'voice';
  asset_ids: string[];
}

// GET /api/v1/assets/categories
interface AssetCategoriesQuery {
  type: 'role' | 'style' | 'scene' | 'template' | 'voice';
}
```

> 注释：不再按角色/风格/音色拆分端点，统一由 `type` 区分。

---

## 6. WebSocket 实时事件（沿用 PRD）

- 连接：`wss://api.example.com/ws?token=xxx`
- 订阅：`{"action":"subscribe","channel":"project","project_id":"xxx"}`
- 事件：`generation.progress` / `generation.completed` / `video.progress` / `export.completed` / `quota.insufficient`

---

## 7. 已确认口径（v0）

1. **登录方式**：仅手机验证码登录；邀请码为可选附加字段，不支持账号密码。
2. **命名规范**：后端统一使用 `Project` / `MaterialPackage`；前端历史字段仅做映射，不返回别名字段。
3. **版本策略**：不引入显式 `version` 字段；重要修改生成新素材包，可用 `parent_id` 关联。
4. **候选历史**：仅保留当前候选集（有限数量），不持久化完整历史。
5. **媒体存储**：统一使用短期签名 URL，不提供永久直链。
6. **配额扣减**：任务成功完成时扣减；失败或中断不扣减。
7. **音频配置**：优先级为镜头级覆盖 > 角色级默认 > 全局默认。
8. **资产库类型**：统一资产库模型，通过 `type` 字段扩展（role / style / scene / template / voice）。

---

> 文档版本：v1.0-final
> 更新时间：2026年
