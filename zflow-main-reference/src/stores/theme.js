/**
 * Theme store | 主题状态管理
 * Handles theme state (always dark)
 */
import { ref } from 'vue'

// Always dark | 始终深色
export const isDark = ref(true)

// Ensure dark class is on html element | 确保 html 元素上有 dark 类
if (typeof window !== 'undefined') {
  document.documentElement.classList.add('dark')
  localStorage.setItem('theme', 'dark')
}

// Toggle theme (disabled/noop) | 切换主题（禁用/无效）
export const toggleTheme = () => {
  // Do nothing or force true
  isDark.value = true
  document.documentElement.classList.add('dark')
}
