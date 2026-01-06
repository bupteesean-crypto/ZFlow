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
    sessionStorage.setItem('authenticated', String(data.authenticated));
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
  background: #05070f;
  color: #dfe8ff;
  padding-top: 72px;
}

.glass-nav {
  background: linear-gradient(120deg, rgba(14, 17, 28, 0.92), rgba(9, 12, 22, 0.92));
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

.logo-badge {
  height: 36px;
  width: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.8), rgba(16, 185, 129, 0.6), rgba(29, 78, 216, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-weight: bold;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-link:hover {
  border-color: rgba(52, 211, 153, 0.4);
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
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  overflow: hidden;
  max-width: 1000px;
  width: 100%;
}

.visual {
  position: relative;
  overflow: hidden;
  background: #0c2f25;
  color: #c7f4df;
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
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #cfd7ff;
  cursor: pointer;
  font-size: 20px;
}

.panel {
  background: linear-gradient(145deg, rgba(12, 16, 26, 0.96), rgba(7, 10, 18, 0.96));
  border-left: 1px solid rgba(255, 255, 255, 0.08);
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
  background: linear-gradient(135deg, rgba(108, 249, 224, 0.9), rgba(124, 93, 255, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #05070f;
}

.logo-subtitle {
  letter-spacing: 0.18em;
  font-size: 12px;
  text-transform: uppercase;
  color: #8fa0c7;
}

.logo-title {
  color: #e8eeff;
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
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: #cdd6ff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab.active {
  border-color: rgba(108, 249, 224, 0.4);
  background: rgba(108, 249, 224, 0.08);
  color: #e8eeff;
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
  color: #7f8aaa;
}

.phone-input {
  display: flex;
  gap: 10px;
  align-items: center;
}

.country-code {
  padding: 12px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #0b111d;
  color: #9fb1ff;
}

.code-row {
  display: flex;
  gap: 10px;
}

input {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #0b111d;
  color: #e8eeff;
  font-size: 14px;
}

input::placeholder {
  color: #5d6786;
}

input:focus {
  outline: none;
  border-color: rgba(108, 249, 224, 0.4);
}

.btn-code {
  min-width: 110px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #d6def7;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.btn-code:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
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
  background: linear-gradient(120deg, rgba(108, 249, 224, 0.9), rgba(124, 93, 255, 0.9));
  color: #05070f;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(108, 249, 224, 0.25);
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
  color: #7a88b8;
  text-align: center;
}

.agreement a {
  color: #9fb1ff;
  text-decoration: underline;
}

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
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
  background: #0f1626;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 24px;
  overflow-y: auto;
  color: #dfe8ff;
}

.modal-close {
  float: right;
  cursor: pointer;
  color: #9fb1ff;
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
