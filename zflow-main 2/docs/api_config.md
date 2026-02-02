# 模型接入指南

本文档介绍了如何在 Z Flow 中接入新的视频生成和图像生成模型。由于 API Endpoint 保持一致，只需在配置文件中添加模型 ID 及相关参数配置即可。

## 1. 配置文件位置

所有模型配置均位于：
`src/config/models.js`

## 2. 接入图像生成模型 (Image Models)

在 `IMAGE_MODELS` 数组中添加新的模型配置对象。

### 配置结构说明

```javascript
{
    label: '显示名称',          // 在 UI 上显示的名称
    key: 'model-id',           // 实际调用的模型 ID
    sizes: [],                 // 支持的尺寸列表（引用已有的尺寸常量或自定义）
    qualities: [],             // (可选) 支持的画质选项
    defaultParams: {           // (可选) 默认参数，会自动合并到 API 请求中
        quality: 'standard',
        style: 'vivid',
        // 其他模型特定参数
    }
}
```

### 示例

假设要接入一个新的图像模型 `new-image-model-v1`：

```javascript
// src/config/models.js

export const IMAGE_MODELS = [
    // ... 原有模型
    {
        label: 'New Image Model',
        key: 'new-image-model-v1',
        sizes: NANO_SIZE_OPTIONS, // 使用现有的尺寸配置
        defaultParams: {
            quality: 'hd',
            steps: 30 // 如果 API 支持自定义步数
        }
    }
]
```

## 3. 接入视频生成模型 (Video Models)

在 `VIDEO_MODELS` 数组中添加新的模型配置对象。

### 配置结构说明

```javascript
{
    label: '显示名称',          // UI 显示名称
    key: 'model-id',           // 模型 ID
    ratios: [],                // 支持的比例列表（如 ['16:9', '9:16']）
    durs: [],                  // 支持的时长选项（如 [{ label: '5s', key: 5 }]）
    defaultParams: {           // 默认参数
        ratio: '16:9',
        duration: 5
    }
}
```

### 示例

假设要接入一个新的视频模型 `new-video-model-pro`：

```javascript
// src/config/models.js

export const VIDEO_MODELS = [
    // ... 原有模型
    {
        label: 'New Video Pro',
        key: 'new-video-model-pro',
        ratios: ['16:9', '9:16', '1:1'], // 自定义支持的比例
        durs: [
            { label: '5 秒', key: 5 },
            { label: '10 秒', key: 10 }
        ],
        defaultParams: {
            ratio: '16:9',
            duration: 5,
            fps: 30 // 模型特定的额外参数
        }
    }
]
```

## 4. 参数传递说明

由于 API Endpoint 一致（默认为 `/images/generations` 和 `/videos/generations`），系统会自动处理基础请求。

- **通用参数**：如 `prompt` (提示词), `model` (模型ID) 会自动处理。
- **自定义参数**：在 `defaultParams` 中定义的参数，或者在 UI 组件中新增的参数，会合并到请求体 (Body) 中发送给后端。
- **特殊处理**：如果新模型需要非常特殊的参数处理逻辑（例如参数名映射不同），可能需要修改 `src/hooks/useApi.js` 中的 `useImageGeneration` 或 `useVideoGeneration` 函数。
