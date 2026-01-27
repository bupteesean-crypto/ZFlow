<template>
  <div class="login-page">
    <nav class="glass-nav">
      <div class="top-nav">
        <div class="top-nav__left">
          <div class="logo-badge">ZF</div>
          <div>
            <div class="brand-name">ZFlow</div>
            <div class="brand-subtitle">登录 / 注册</div>
          </div>
        </div>
        <div class="top-nav__right">
          <RouterLink to="/" class="nav-link">返回首页</RouterLink>
        </div>
      </div>
    </nav>

    <main class="login-main">
      <div class="login-wrap">
        <div class="visual">
          <div class="visual-content">这里是视频，暂时占位用。</div>
          <button class="close-btn" @click="goBack">×</button>
        </div>
        <div class="panel">
          <div class="logo">
            <div class="logo-mark">ZF</div>
            <div>
              <div class="logo-subtitle">ZFlow</div>
              <div class="logo-title">欢迎回来</div>
            </div>
          </div>

          <form class="login-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="label">账号</label>
              <input
                v-model="username"
                type="text"
                placeholder="请输入账号"
                autocomplete="username"
              />
            </div>

            <div class="form-group">
              <label class="label">密码</label>
              <input
                v-model="password"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
              />
            </div>

            <button type="submit" class="btn-submit" :disabled="loading">
              {{ loading ? '登录中...' : '账号登录' }}
            </button>

            <div class="agreement">
              登录即代表同意
              <a href="javascript:void(0)" @click="showServiceModal = true">《服务协议》</a>
              <a href="javascript:void(0)" @click="showPrivacyModal = true">《隐私政策》</a>
            </div>

            <div class="admin-link">
              <RouterLink to="/admin/users">账号管理入口</RouterLink>
            </div>
          </form>
        </div>
      </div>
    </main>

    <!-- Service Modal -->
    <div v-if="showServiceModal" class="modal active" @click.self="showServiceModal = false">
      <div class="modal-content">
        <span class="modal-close" @click="showServiceModal = false">✕</span>
        <h3>服务协议（示例占位）</h3>
        <p>1. 本平台提供视频创作相关的在线服务，当前为演示环境，不产生真实输出。</p>
        <p>2. 用户需遵守法律法规，不得上传违法违规内容。</p>
        <p>3. 演示登录为模拟，不收集真实数据。</p>
      </div>
    </div>

    <!-- Privacy Modal -->
    <div v-if="showPrivacyModal" class="modal active" @click.self="showPrivacyModal = false">
      <div class="modal-content">
        <span class="modal-close" @click="showPrivacyModal = false">✕</span>
        <h3>隐私政策（示例占位）</h3>
        <p>1. 演示环境不会存储个人敏感信息。</p>
        <p>2. 提交的内容仅用于本地演示，不会上传。</p>
        <p>3. 关闭页面后临时数据将被清除。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { login } from '@/api/auth';

const router = useRouter();

const username = ref('');
const password = ref('');
const loading = ref(false);
const showServiceModal = ref(false);
const showPrivacyModal = ref(false);

const handleLogin = async () => {
  if (!username.value || !password.value) {
    alert('请输入账号和密码');
    return;
  }

  loading.value = true;

  try {
    const data = await login({
      username: username.value.trim(),
      password: password.value,
    });
    sessionStorage.setItem('authenticated', 'true');
    sessionStorage.setItem('session_token', data.session_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
    sessionStorage.setItem('user', JSON.stringify(data.user));
    sessionStorage.setItem('sessionToken', data.session_token);
    sessionStorage.setItem('refreshToken', data.refresh_token);
    sessionStorage.setItem('userType', data.user.account_type);
    sessionStorage.setItem('currentSpace', data.current_space?.space_name || '');
    sessionStorage.setItem('llmConfigured', data.user.llm_configured ? 'true' : 'false');
    sessionStorage.setItem('llmApiBase', data.user.llm_api_base || '');

    const redirect = router.currentRoute.value.query.redirect;
    if (typeof redirect === 'string' && redirect.length > 0) {
      router.push(redirect);
    } else {
      router.push('/');
    }
  } catch (err) {
    alert(err instanceof Error ? err.message : '登录失败');
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.push('/');
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--md-surface);
  color: var(--md-on-surface);
  padding-top: 72px;
}

.logo-badge {
  height: 36px;
  width: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.95), rgba(var(--md-accent-2-rgb), 0.85));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(10, 16, 28, 0.8);
  border: 1px solid var(--md-stroke);
  color: var(--md-on-surface-variant);
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-link:hover {
  border-color: rgba(var(--md-accent-rgb), 0.35);
}

.login-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  min-height: calc(100vh - 72px);
}

.login-wrap {
  display: grid;
  grid-template-columns: 3fr 2fr;
  min-height: calc(100vh - 144px);
  border: 1px solid var(--md-stroke);
  border-radius: 20px;
  overflow: hidden;
  max-width: 1000px;
  width: 100%;
  box-shadow: var(--md-card-shadow);
}

.visual {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(18, 36, 58, 0.9), rgba(9, 16, 28, 0.9));
  color: var(--md-on-secondary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-content {
  font-size: 18px;
  letter-spacing: 0.08em;
  text-align: center;
  padding: 24px;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--md-stroke);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  font-size: 20px;
}

.panel {
  background: var(--md-surface-card);
  border-left: 1px solid var(--md-stroke);
  padding: 48px 42px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--md-on-primary);
}

.logo-subtitle {
  letter-spacing: 0.18em;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--md-on-surface-variant);
}

.logo-title {
  color: var(--md-on-surface);
  font-weight: 600;
  font-size: 16px;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface-variant);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab.active {
  border-color: rgba(var(--md-accent-rgb), 0.55);
  background: rgba(var(--md-accent-rgb), 0.18);
  color: var(--md-on-surface);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.phone-input {
  display: flex;
  gap: 10px;
  align-items: center;
}

.country-code {
  padding: 12px 10px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface-variant);
}

.code-row {
  display: flex;
  gap: 10px;
}

input {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--md-stroke);
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  font-size: 14px;
}

input::placeholder {
  color: var(--md-on-surface-variant);
}

input:focus {
  outline: none;
  border-color: rgba(var(--md-accent-rgb), 0.45);
}

.btn-code {
  min-width: 110px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.8);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.btn-code:hover:not(:disabled) {
  background: rgba(var(--md-accent-rgb), 0.1);
}

.btn-code:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-submit {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.9), rgba(var(--md-accent-2-rgb), 0.85));
  color: #031019;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 28px rgba(var(--md-accent-rgb), 0.18);
  transition: all 0.2s ease;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.agreement {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  text-align: center;
}

.agreement a {
  color: var(--md-primary);
  text-decoration: underline;
}

.admin-link {
  margin-top: 16px;
  text-align: center;
  font-size: 12px;
}

.admin-link a {
  color: var(--md-primary);
  text-decoration: underline;
}

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(28, 27, 31, 0.35);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: var(--layer-modal);
}

.modal.active {
  display: flex;
}

.modal-content {
  width: min(600px, 90vw);
  max-height: 80vh;
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  padding: 24px;
  overflow-y: auto;
  color: var(--md-on-surface);
}

.modal-close {
  float: right;
  cursor: pointer;
  color: var(--md-primary);
  font-size: 18px;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.modal-content p {
  margin-bottom: 8px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .login-wrap {
    grid-template-columns: 1fr;
  }

  .visual {
    display: none;
  }

  .panel {
    padding: 32px 24px;
  }
}
</style>
