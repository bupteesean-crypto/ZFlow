<template>
  <div class="login-page">
    <nav class="glass-nav fixed top-0 left-0 right-0 z-50">
      <div class="px-5 py-3 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="logo-badge">ZV</div>
          <div>
            <div class="text-sm uppercase tracking-[0.2em] text-slate-400">Z.Video</div>
            <div class="text-xs text-slate-500">登录 / 注册</div>
          </div>
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-300">
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
            <div class="logo-mark">ZV</div>
            <div>
              <div class="logo-subtitle">Z.Vid</div>
              <div class="logo-title">欢迎回来</div>
            </div>
          </div>

          <div class="tabs">
            <button
              :class="['tab', { active: loginMode === 'personal' }]"
              @click="loginMode = 'personal'"
            >
              个人登录
            </button>
            <button
              :class="['tab', { active: loginMode === 'team' }]"
              @click="loginMode = 'team'"
            >
              团队登录
            </button>
          </div>

          <form class="login-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="label">手机号</label>
              <div class="phone-input">
                <div class="country-code">+86</div>
                <input
                  v-model="phone"
                  type="tel"
                  placeholder="请输入手机号"
                  maxlength="11"
                />
              </div>
            </div>

            <div class="form-group">
              <label class="label">验证码</label>
              <div class="code-row">
                <input
                  v-model="code"
                  type="text"
                  placeholder="6位验证码"
                  maxlength="6"
                />
                <button type="button" class="btn-code" @click="sendCode">
                  {{ codeButtonText }}
                </button>
              </div>
            </div>

            <div v-if="loginMode === 'team'" class="form-group">
              <label class="label">团队邀请码</label>
              <input
                v-model="teamInvite"
                type="text"
                placeholder="请输入团队邀请码"
              />
            </div>

            <button type="submit" class="btn-submit" :disabled="loading">
              {{ loading ? '登录中...' : '验证码登录' }}
            </button>

            <div class="agreement">
              登录即代表同意
              <a href="javascript:void(0)" @click="showServiceModal = true">《服务协议》</a>
              <a href="javascript:void(0)" @click="showPrivacyModal = true">《隐私政策》</a>
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
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

import { login } from '@/api/auth';

const router = useRouter();

const loginMode = ref<'personal' | 'team'>('personal');
const phone = ref('');
const code = ref('');
const teamInvite = ref('');
const loading = ref(false);
const showServiceModal = ref(false);
const showPrivacyModal = ref(false);
const countdown = ref(0);

const codeButtonText = computed(() => {
  if (countdown.value > 0) {
    return `${countdown.value}s 后重发`;
  }
  return '获取验证码';
});

const sendCode = () => {
  if (!phone.value) {
    alert('请输入手机号');
    return;
  }
  if (!/^1\d{10}$/.test(phone.value)) {
    alert('请输入正确的手机号');
    return;
  }

  // TODO: Call API to send code
  alert('验证码已发送（模拟）');
  countdown.value = 60;
  const timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(timer);
    }
  }, 1000);
};

const handleLogin = async () => {
  if (!phone.value || !code.value) {
    alert('请输入手机号和验证码');
    return;
  }

  if (!/^1\d{10}$/.test(phone.value)) {
    alert('请输入正确的手机号');
    return;
  }

  loading.value = true;

  try {
    const data = await login({
      phone: phone.value,
      code: code.value,
      invite_code: loginMode.value === 'team' ? teamInvite.value : undefined,
    });
    sessionStorage.setItem('authenticated', 'true');
    sessionStorage.setItem('session_token', data.session_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
    sessionStorage.setItem('user', JSON.stringify(data.user));
    sessionStorage.setItem('sessionToken', data.session_token);
    sessionStorage.setItem('refreshToken', data.refresh_token);
    sessionStorage.setItem('userType', data.user.user_type);
    sessionStorage.setItem('currentSpace', data.current_space?.space_name || '');

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

.glass-nav {
  background: rgba(255, 251, 254, 0.9);
  border-bottom: 1px solid rgba(121, 116, 126, 0.2);
  backdrop-filter: blur(12px);
}

.logo-badge {
  height: 36px;
  width: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(103, 80, 164, 0.85), rgba(125, 82, 96, 0.75));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.2);
  color: var(--md-on-surface-variant);
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-link:hover {
  border-color: rgba(103, 80, 164, 0.35);
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 18px;
  overflow: hidden;
  max-width: 1000px;
  width: 100%;
}

.visual {
  position: relative;
  overflow: hidden;
  background: var(--md-secondary-container);
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  font-size: 20px;
}

.panel {
  background: var(--md-surface-container);
  border-left: 1px solid rgba(121, 116, 126, 0.2);
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
  background: linear-gradient(135deg, rgba(103, 80, 164, 0.9), rgba(125, 82, 96, 0.8));
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface-variant);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab.active {
  border-color: rgba(103, 80, 164, 0.45);
  background: rgba(103, 80, 164, 0.12);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  font-size: 14px;
}

input::placeholder {
  color: var(--md-on-surface-variant);
}

input:focus {
  outline: none;
  border-color: rgba(103, 80, 164, 0.45);
}

.btn-code {
  min-width: 110px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container);
  color: var(--md-on-surface-variant);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.btn-code:hover:not(:disabled) {
  background: rgba(103, 80, 164, 0.1);
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
  background: var(--md-primary);
  color: var(--md-on-primary);
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 28px rgba(103, 80, 164, 0.18);
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

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(28, 27, 31, 0.35);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal.active {
  display: flex;
}

.modal-content {
  width: min(600px, 90vw);
  max-height: 80vh;
  background: var(--md-surface);
  border: 1px solid rgba(121, 116, 126, 0.2);
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
