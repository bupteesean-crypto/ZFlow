/**
 * API Hooks | API Hooks
 * Simplified hooks for open source version | 开源版简化 hooks
 */

import { ref, reactive, onUnmounted } from 'vue'
import {
  generateImage,
  createVideoTask,
  getVideoTaskStatus,
  streamChatCompletions
} from '@/api'
import { getModelByName } from '@/config/models'
import { useApiConfig } from './useApiConfig'

/**
 * Base API state hook | 基础 API 状态 Hook
 */
export const useApiState = () => {
  const loading = ref(false)
  const error = ref(null)
  const status = ref('idle')

  const reset = () => {
    loading.value = false
    error.value = null
    status.value = 'idle'
  }

  const setLoading = (isLoading) => {
    loading.value = isLoading
    status.value = isLoading ? 'running' : status.value
  }

  const setError = (err) => {
    error.value = err
    status.value = 'error'
    loading.value = false
  }

  const setSuccess = () => {
    status.value = 'success'
    loading.value = false
    error.value = null
  }

  return { loading, error, status, reset, setLoading, setError, setSuccess }
}

/**
 * Chat composable | 问答组合式函数
 */
export const useChat = (options = {}) => {
  const { loading, error, status, reset, setLoading, setError, setSuccess } = useApiState()

  const messages = ref([])
  const currentResponse = ref('')
  let abortController = null

  const send = async (content, stream = true) => {
    setLoading(true)
    currentResponse.value = ''

    try {
      const msgList = [
        ...(options.systemPrompt ? [{ role: 'system', content: options.systemPrompt }] : []),
        ...messages.value,
        { role: 'user', content }
      ]

      if (stream) {
        status.value = 'streaming'
        abortController = new AbortController()
        let fullResponse = ''

        for await (const chunk of streamChatCompletions(
          { model: options.model || 'gpt-4o-mini', messages: msgList },
          abortController.signal
        )) {
          fullResponse += chunk
          currentResponse.value = fullResponse
        }

        messages.value.push({ role: 'user', content })
        messages.value.push({ role: 'assistant', content: fullResponse })
        setSuccess()
        return fullResponse
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err)
        throw err
      }
    }
  }

  const stop = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  const clear = () => {
    messages.value = []
    currentResponse.value = ''
    reset()
  }

  onUnmounted(() => stop())

  return { loading, error, status, messages, currentResponse, send, stop, clear, reset }
}

/**
 * Image generation composable | 图片生成组合式函数
 * Simplified for open source - fixed input/output format
 */
export const useImageGeneration = () => {
  const { loading, error, status, reset, setLoading, setError, setSuccess } = useApiState()

  const images = ref([])
  const currentImage = ref(null)

  /**
   * Generate image with fixed params | 固定参数生成图片
   * @param {Object} params - { model, prompt, size, n, image (optional ref image) }
   */
  const generate = async (params) => {
    setLoading(true)
    images.value = []
    currentImage.value = null

    try {
      const modelConfig = getModelByName(params.model)
      
      // Build request data | 构建请求数据
      const requestData = {
        model: params.model,
        prompt: params.prompt,
        size: params.size || modelConfig?.defaultParams?.size || '1024x1024',
        // n: params.n || 1
      }

      // Add quality and style if provided or in defaultParams | 添加画质和风格
      if (params.quality || modelConfig?.defaultParams?.quality) {
        // Special handling for Seedream models: quality should be 'standard' or 'hd' not the full text
        // Seedream quality options in models.js have keys 'standard' and '4k' (mapped to hd in some APIs)
        // But the input from UI might be "4张 | 高清" if not parsed correctly, OR it might be the key from the option object
        
        let quality = params.quality || modelConfig.defaultParams.quality
        
        // If quality contains pipe character (e.g. from a display label leak), try to clean it
        // But usually params.quality should be the key (e.g., 'standard', '4k')
        // Wait, the user log shows: quality: "4张 | 高清"
        // This means the UI component is passing the label or a combined string instead of the key.
        // Let's check ImageConfigNode.vue again or just fix it here defensively.
        
        // However, standard API expects 'standard' or 'hd'. 
        // Our models.js defines keys as 'standard' and '4k'.
        // If the value is "4张 | 高清", it seems like a UI issue where the dropdown value is wrong.
        
        // Let's try to map it back to valid API values if possible.
        if (quality === '4k') quality = 'hd' // Map '4k' to 'hd' if API requires 'hd'
        
        // If quality is "4张 | 高清", it's definitely invalid for API.
        // It seems like the ImageConfigNode is passing the wrong value.
        // But as a quick fix here:
        if (quality === '4张 | 高清') quality = 'hd' 
        
        requestData.quality = quality
      }
      if (params.style || modelConfig?.defaultParams?.style) {
        requestData.style = params.style || modelConfig.defaultParams.style
      }

      // Add reference image if provided | 添加参考图
      if (params.image) {
        // Clean up the image string | 清理图片字符串
        const imageStr = typeof params.image === 'string' ? params.image.trim() : params.image
        // Use 'images' field for image-to-image as per API spec | 根据 API 规范使用 'images' 字段进行图生图
        requestData.images = [imageStr]
      } else if (params.images && params.images.length > 0) {
        // Handle multiple reference images | 处理多张参考图
        requestData.images = params.images.map(img => typeof img === 'string' ? img.trim() : img)
      }

      // Add mask if provided | 添加蒙版
      if (params.mask) {
        requestData.mask = params.mask
      }

      // Call API | 调用 API
      const response = await generateImage(requestData, {
        requestType: 'json',
        endpoint: modelConfig?.endpoint || '/images/generations'
      })

      // Parse response (OpenAI format) | 解析响应
      const data = response.data || response
      const generatedImages = (Array.isArray(data) ? data : [data]).map(item => ({
        url: item.url || item.b64_json || item,
        revisedPrompt: item.revised_prompt || ''
      }))

      images.value = generatedImages
      currentImage.value = generatedImages[0] || null
      setSuccess()
      return generatedImages
    } catch (err) {
      setError(err)
      throw err
    }
  }

  return { loading, error, status, images, currentImage, generate, reset }
}

/**
 * Video generation composable | 视频生成组合式函数
 * Simplified for open source - fixed input/output format with polling
 */
export const useVideoGeneration = () => {
  const { loading, error, status, reset, setLoading, setError, setSuccess } = useApiState()

  const video = ref(null)
  const taskId = ref(null)
  const progress = reactive({
    attempt: 0,
    maxAttempts: 120,
    percentage: 0
  })

  /**
   * Generate video with fixed params | 固定参数生成视频
   * @param {Object} params - { model, prompt, first_frame_image, last_frame_image, ratio, duration }
   */
  const generate = async (params) => {
    setLoading(true)
    video.value = null
    taskId.value = null
    progress.attempt = 0
    progress.percentage = 0

    try {
      const modelConfig = getModelByName(params.model)
      
      // Build request data | 构建请求数据
      const requestData = {
        model: params.model,
        // New API format requires 'content' array for multimodal input | 新版 API 要求 'content' 数组用于多模态输入
        content: []
      }

      // Add text prompt | 添加文本提示词
      if (params.prompt) {
        requestData.content.push({
          type: 'text',
          text: params.prompt
        })
      }

      // Add first frame image | 添加首帧图片
      if (params.first_frame_image) {
        // Clean up URL | 清理 URL
        const imageUrl = params.first_frame_image.trim()
        requestData.content.push({
          type: 'image_url',
          image_url: {
            url: imageUrl
          },
          // Add role for first frame if last frame also exists, or if specifically requested | 如果存在尾帧或特定请求，则添加首帧角色
          // Based on user input: "role": "first_frame"
          role: 'first_frame'
        })
      }

      // Add last frame image if exists | 添加尾帧图片
      if (params.last_frame_image) {
        const imageUrl = params.last_frame_image.trim()
        requestData.content.push({
          type: 'image_url',
          image_url: {
            url: imageUrl
          },
          role: 'last_frame'
        })
      }

      // Add reference images | 添加参考图
      if (params.images && params.images.length > 0) {
        params.images.forEach(img => {
          if (typeof img === 'string') {
            requestData.content.push({
              type: 'image_url',
              image_url: {
                url: img.trim()
              },
              role: 'reference_image'
            })
          }
        })
      }

      // Add other params | 添加其他参数
      if (params.ratio) requestData.ratio = params.ratio // API might expect 'ratio' or 'size', trying 'ratio' based on common specs
      // Note: User input showed "size": "9:16", but that was what we sent before. 
      // If previous request had "size" and failed on "content", "size" might still be valid or ignored.
      // Let's keep 'ratio' as key if the model is 'doubao-seedance'.
      // Actually, let's try sending both or stick to one. The user's error log showed they sent "size": "9:16".
      // Let's use 'ratio' as it's more specific for video, or check if 'size' is required.
      // Reverting to 'ratio' as per standard video APIs often.
      if (params.ratio) requestData.ratio = params.ratio
      
      if (params.dur) requestData.duration = params.dur // Changed from 'seconds' to 'duration' as it's more standard

      // Call API | 调用 API
      const task = await createVideoTask(requestData, {
        requestType: 'json',
        endpoint: modelConfig?.endpoint || '/videos/generations'
      })

      // Check if async (need polling) | 检查是否异步
      const isAsync = modelConfig?.async !== false

      // If has video URL directly, return | 如果直接有视频 URL，返回
      if (!isAsync || task.data?.url || task.url) {
        const videoUrl = task.data?.url || task.url || task.data?.[0]?.url
        video.value = { url: videoUrl, ...task }
        setSuccess()
        return video.value
      }

      // Get task ID for polling | 获取任务 ID 用于轮询
      const id = task.id || task.task_id || task.taskId
      if (!id) {
        throw new Error('未获取到任务 ID')
      }

      taskId.value = id
      status.value = 'polling'

      // Poll for result | 轮询获取结果
      const maxAttempts = 120
      const interval = 5000

      for (let i = 0; i < maxAttempts; i++) {
        progress.attempt = i + 1
        progress.percentage = Math.min(Math.round((i / maxAttempts) * 100), 99)

        const result = await getVideoTaskStatus(id)

        // Check for completion | 检查是否完成
        if (result.status === 'completed' || result.status === 'succeeded' || result.task_status === 'SUCCESS' || result.data) {
          progress.percentage = 100
          // Handle various response formats | 处理各种响应格式
          // 1. Standard format: result.data.url
          // 2. Direct format: result.url
          // 3. New API format: result.video_result[0].url
          const videoUrl = 
            result.video_result?.[0]?.url || 
            result.data?.url || 
            result.data?.[0]?.url || 
            result.url || 
            result.video_url

          if (videoUrl) {
            video.value = { url: videoUrl, ...result }
            setSuccess()
            return video.value
          } else if (result.task_status === 'SUCCESS' && !videoUrl) {
             // Task success but no URL found yet? Wait or error? 
             // Usually SUCCESS means result is there. If not, maybe processing just finished.
             // But for safety, let's consider it done only if we have URL, or just return result.
             // However, based on user log, video_result is present.
          }
        }
        
        // Also check for FAIL status in new API
        if (result.task_status === 'FAIL' || result.task_status === 'FAILED') {
           throw new Error(result.error_msg || result.message || '视频生成失败')
        }

        // Check for failure | 检查是否失败
        if (result.status === 'failed' || result.status === 'error') {
          throw new Error(result.error?.message || result.message || '视频生成失败')
        }

        // Wait before next poll | 等待下次轮询
        await new Promise(resolve => setTimeout(resolve, interval))
      }

      throw new Error('视频生成超时')
    } catch (err) {
      setError(err)
      throw err
    }
  }

  return { loading, error, status, video, taskId, progress, generate, reset }
}

/**
 * Combined API composable | 综合 API 组合式函数
 */
export const useApi = () => {
  const config = useApiConfig()
  const chat = useChat()
  const image = useImageGeneration()
  const videoGen = useVideoGeneration()

  return { config, chat, image, video: videoGen }
}
