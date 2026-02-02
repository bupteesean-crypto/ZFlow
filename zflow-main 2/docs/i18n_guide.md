# 国际化配置指南 (i18n Guide)

本项目使用 `vue-i18n` 实现多语言支持。目前支持中文 (zh) 和英文 (en)。

## 1. 安装和配置

项目已经预装了 `vue-i18n`。

配置文件位置：
- 入口配置：`src/i18n/index.js`
- 语言包：`src/i18n/locales/*.js`

## 2. 添加新语言

1. 在 `src/i18n/locales/` 下创建新的语言文件，例如 `jp.js` (日语)。
2. 在 `src/i18n/index.js` 中引入并注册：

```javascript
import jp from './locales/jp'

const i18n = createI18n({
  // ...
  messages: {
    zh,
    en,
    jp // 添加新语言
  }
})
```

## 3. 使用方法

### 在模板中

使用 `$t` 函数：

```html
<button :title="$t('common.settings')">
  Settings
</button>
```

### 在脚本中 (setup script)

使用 `useI18n` hook：

```javascript
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

console.log(t('common.success'))

// 切换语言
const toggleLanguage = () => {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
}
```

## 4. 语言包结构

建议按模块组织语言包结构：

```javascript
// src/i18n/locales/zh.js
export default {
  common: {
    confirm: '确认',
    cancel: '取消'
  },
  menu: {
    home: '首页'
  },
  // ...
}
```
