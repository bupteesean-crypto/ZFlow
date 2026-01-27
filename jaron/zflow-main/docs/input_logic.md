# 输入框输入后执行逻辑说明

本文档说明了在应用中输入文本后系统的执行逻辑。主要涉及首页 (`Home.vue`) 的新建项目输入框和画布页 (`Canvas.vue`) 的对话输入框。

## 1. 首页输入逻辑 (`src/views/Home.vue`)

当用户在首页输入框输入文本并提交（回车或点击发送）时，执行 `handleCreateWithInput` 方法：

1.  **检查 API 配置**：首先检查是否已配置 API Key。
2.  **创建项目**：使用输入文本作为项目名称（如果为空则默认为"未命名项目"）创建一个新项目。
3.  **存储提示词**：将用户输入的文本存储到 `sessionStorage` 中，Key 为 `ai-canvas-initial-prompt`。
4.  **页面跳转**：跳转到新创建项目的画布页面 (`/canvas/{projectId}`)。

```javascript
// src/views/Home.vue
const handleCreateWithInput = () => {
  checkApiKeyAndNavigate(() => {
    // ...
    // 存储提示词
    sessionStorage.setItem('ai-canvas-initial-prompt', inputText.value.trim())
    // 跳转
    router.push(`/canvas/${id}`)
  })
}
```

## 2. 画布页初始化逻辑 (`src/views/Canvas.vue`)

当画布页面加载完成 (`onMounted`) 时：

1.  **检查初始提示词**：检查 `sessionStorage` 中是否存在 `ai-canvas-initial-prompt`。
2.  **自动执行**：如果存在，读取该文本作为输入内容，并在 `nextTick` 后自动调用 `sendMessage()` 方法执行后续逻辑。

```javascript
// src/views/Canvas.vue
onMounted(() => {
  // ...
  const initialPrompt = sessionStorage.getItem('ai-canvas-initial-prompt')
  if (initialPrompt) {
    sessionStorage.removeItem('ai-canvas-initial-prompt')
    chatInput.value = initialPrompt
    // 自动触发发送
    nextTick(() => {
      sendMessage()
    })
  }
})
```

## 3. 核心执行逻辑 (`sendMessage` 方法)

无论是来自首页的自动执行，还是用户在画布页底部输入框直接输入，最终都由 `sendMessage` 方法处理。

### 3.1 前置检查
*   检查输入内容是否为空。
*   检查 API Key 是否配置。

### 3.2 执行模式
系统根据 `autoExecute`（自动执行）开关的状态决定执行路径。

#### A. 自动执行模式 (默认)
1.  **意图分析**：调用 `useWorkflowOrchestrator` hook 中的 `analyzeIntent(content)` 方法。
    *   该方法使用 LLM 分析用户的文本，确定工作流类型（如文生图、视频生成、分镜等）并提取相关参数。
    *   **工作流类型**：
        *   `text_to_image`: 单张图片生成（默认）
        *   `text_to_image_to_video`: 图片转视频
        *   `storyboard`: 分镜/多场景
        *   `multi_angle_storyboard`: 多角度分镜
2.  **执行工作流**：
    *   如果分析成功，调用 `executeWorkflow` 根据分析结果执行相应的工作流。
    *   如果分析失败，捕获错误并回退到默认的"文生图"工作流 (`createTextToImageWorkflow`)。

#### B. 手动模式
如果不启用自动执行，系统仅会在画布上创建基础节点：
1.  创建一个包含用户输入内容的 **文本节点**。
2.  创建一个 **文生图配置节点**。
3.  自动连接这两个节点。

## 4. 数据存储结构

项目数据持久化存储在浏览器 `localStorage` 中，Key 为 `ai-canvas-projects`。存储格式为 JSON 数组，每个项目对象包含以下字段：

### 4.1 项目对象结构 (Project Object)

| 字段 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `id` | `string` | 项目唯一标识符 | `"project_1740123456789_a1b2c3d4"` |
| `name` | `string` | 项目名称 | `"未命名项目"` |
| `thumbnail` | `string` | 项目缩略图 (URL 或 Base64) | `"http://..."` |
| `createdAt` | `string` | 创建时间 (ISO 格式) | `"2025-02-21T08:00:00.000Z"` |
| `updatedAt` | `string` | 最后更新时间 (ISO 格式) | `"2025-02-21T09:30:00.000Z"` |
| `canvasData` | `object` | 画布数据，包含节点和连线 | (见下文) |

### 4.2 画布数据结构 (canvasData)

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `nodes` | `Array` | 节点列表 |
| `edges` | `Array` | 连线列表 |
| `viewport` | `object` | 视口状态 `{ x, y, zoom }` |

**节点对象示例 (Node):**
```json
{
  "id": "node_0",
  "type": "text",
  "position": { "x": 150, "y": 150 },
  "data": {
    "content": "用户输入的提示词内容",
    "label": "文本输入"
  }
}
```

**连线对象示例 (Edge):**
```json
{
  "id": "edge_node_0_node_1",
  "source": "node_0",
  "target": "node_1",
  "sourceHandle": "right",
  "targetHandle": "left"
}
```

### 4.3 存储位置
*   **文件**: `src/stores/projects.js`
*   **Key**: `ai-canvas-projects`
*   **机制**: 每次项目更新（新建、重命名、画布变动）都会触发 `saveProjects()` 将整个项目列表序列化为 JSON 字符串并写入 `localStorage`。

## 5. 相关代码位置

*   **首页处理**: [Home.vue](../src/views/Home.vue) - `handleCreateWithInput`
*   **画布初始化**: [Canvas.vue](../src/views/Canvas.vue) - `onMounted`
*   **消息发送**: [Canvas.vue](../src/views/Canvas.vue) - `sendMessage`
*   **工作流编排**: [useWorkflowOrchestrator.js](../src/hooks/useWorkflowOrchestrator.js)
*   **项目存储管理**: [projects.js](../src/stores/projects.js)
