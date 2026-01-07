<template>
  <div class="app-shell">
    <!-- Top Navigation -->
    <nav class="glass-nav">
      <div class="top-nav">
        <div class="top-nav__left">
          <div class="logo-badge">ZV</div>
          <div class="brand-name">Z.Video</div>
          <div v-if="showSpaceSelector" class="space-switcher">
            <span class="space-label">Space</span>
            <select class="space-select" v-model="currentSpace" @change="handleSpaceChange">
              <option class="bg-slate-900" value="">选择空间</option>
              <option v-for="space in spaces" :key="space.id" :value="space.id">
                {{ space.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="top-nav__right">
          <div v-if="showSearch" class="search-wrap">
            <input
              type="search"
              placeholder="⌘K / 搜索任务"
              class="search-input"
            />
            <span class="search-hint">CTRL+K</span>
          </div>
          <div class="top-nav__meta">
            <span v-if="quota" class="quota-badge">配额 {{ quota }} 次生成</span>
            <span class="beta-badge">Beta</span>
          </div>
          <button
            ref="avatarBtn"
            class="avatar-btn"
            aria-label="用户信息"
            @click="toggleProfile"
          >
            <img :src="avatarUrl" alt="avatar" />
          </button>
        </div>
      </div>
    </nav>

    <!-- Left Sidebar -->
    <aside class="side-nav">
      <div class="glass-side">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="item.to"
          class="nav-link icon-only"
          :class="{ active: isActive(item.to) }"
          :data-label="item.label"
        >
          {{ item.icon }}
        </RouterLink>
      </div>
    </aside>

    <!-- Profile Popover -->
    <div
      v-if="showProfile"
      class="profile-popover"
      role="dialog"
      aria-modal="false"
      @clickOutside="closeProfile"
    >
      <div class="popover-header">
        <div class="avatar-wrap">
          <img :src="avatarUrl" alt="avatar" />
          <button class="change-avatar" @click="handleChangeAvatar">更换</button>
        </div>
        <div class="user-meta">
          <div class="username">{{ username }}</div>
          <div class="uid">
            UID: {{ uid }}
            <button @click="copyUid">复制</button>
          </div>
        </div>
      </div>
      <div class="section membership">
        <div class="label">
          <span class="icon">◆</span> 付费会员
        </div>
        <div class="action">
          <span class="points">积分 {{ points }}</span>
          <button @click="$emit('openVip')">开通 / 续费</button>
        </div>
      </div>
      <div class="section points">
        <div class="points-row">
          <span>当前积分</span><strong>{{ points }}</strong>
        </div>
        <div class="points-row">
          <span>付费积分</span><strong>{{ paidPoints }}</strong>
        </div>
        <div class="points-row">
          <span>赠送积分</span><strong>{{ giftPoints }}</strong>
        </div>
      </div>
      <div class="section actions">
        <button class="link-btn" @click="$emit('subscribe')">订阅管理</button>
        <button class="link-btn" @click="$emit('orders')">订单记录</button>
        <button class="link-btn danger" @click="$emit('logout')">退出登录</button>
      </div>
    </div>

    <!-- Main Content Area -->
    <main class="app-shell__content">
      <slot />
    </main>

    <!-- Toast -->
    <div v-if="toastVisible" class="profile-toast">{{ toastMessage }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';

interface NavItem {
  name: string;
  to: string;
  icon: string;
  label: string;
}

interface Space {
  id: string;
  name: string;
}

const props = withDefaults(defineProps<{
  quota?: number;
  username?: string;
  uid?: string;
  points?: number;
  paidPoints?: number;
  giftPoints?: number;
  avatarUrl?: string;
  showSearch?: boolean;
  showSpaceSelector?: boolean;
  spaces?: Space[];
}>(), {
  quota: 5,
  username: '手机用户1121',
  uid: '9c7f-42a1',
  points: 350,
  paidPoints: 0,
  giftPoints: 350,
  avatarUrl: 'https://placehold.co/80x80',
  showSearch: true,
  showSpaceSelector: false,
  spaces: () => [],
});

const emit = defineEmits<{
  openVip: [];
  subscribe: [];
  orders: [];
  logout: [];
  spaceChange: [spaceId: string];
}>();

const route = useRoute();
const avatarBtn = ref<HTMLElement | null>(null);
const showProfile = ref(false);
const toastVisible = ref(false);
const toastMessage = ref('');
const currentSpace = ref('');

const navItems: NavItem[] = [
  { name: 'landing', to: '/', icon: '⌂', label: '首页' },
  { name: 'materials', to: '/materials', icon: '✦', label: '素材' },
  { name: 'editor', to: '/editor', icon: '✎', label: '编辑器' },
  { name: 'assets', to: '/assets', icon: '⟡', label: '资产库' },
  { name: 'space', to: '/space', icon: '★', label: '我的空间' },
];

const isActive = (path: string): boolean => {
  if (path === '/') {
    return route.path === '/' || route.path === '/landing';
  }
  return route.path.startsWith(path);
};

const toggleProfile = () => {
  showProfile.value = !showProfile.value;
};

const closeProfile = () => {
  showProfile.value = false;
};

const copyUid = async () => {
  try {
    await navigator.clipboard.writeText(props.uid);
    showToast('复制成功');
  } catch {
    showToast('复制失败');
  }
};

const handleChangeAvatar = () => {
  // TODO: Implement avatar change
  showToast('更换头像功能待实现');
};

const showToast = (message: string) => {
  toastMessage.value = message;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 1400);
};

const handleSpaceChange = () => {
  emit('spaceChange', currentSpace.value);
};

// Close popover when clicking outside
if (typeof document !== 'undefined') {
  document.addEventListener('click', (e) => {
    if (showProfile.value && avatarBtn.value && !avatarBtn.value.contains(e.target as Node)) {
      const popover = document.querySelector('.profile-popover');
      if (popover && !popover.contains(e.target as Node)) {
        closeProfile();
      }
    }
  });
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.glass-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(255, 251, 254, 0.9);
  border-bottom: 1px solid rgba(121, 116, 126, 0.2);
  backdrop-filter: blur(12px);
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
}

.top-nav__left,
.top-nav__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-name {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--md-on-surface-variant);
}

.space-switcher {
  display: none;
  align-items: center;
  gap: 8px;
  padding-left: 16px;
  margin-left: 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.space-label {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.search-wrap {
  position: relative;
  display: none;
}

.top-nav__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--md-on-surface-variant);
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
  box-shadow: 0 10px 18px rgba(103, 80, 164, 0.2);
}

.space-select {
  font-size: 0.875rem;
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  border: 1px solid rgba(121, 116, 126, 0.3);
  border-radius: 0.375rem;
  padding: 0.25rem 0.5rem;
}

.space-select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.35);
}

.search-input {
  width: 256px;
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: var(--md-on-surface);
}

.search-input::placeholder {
  color: var(--md-on-surface-variant);
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.35);
}

.search-hint {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  color: var(--md-on-surface-variant);
  letter-spacing: 0.1em;
}

.quota-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-primary);
  border: 1px solid rgba(103, 80, 164, 0.25);
}

.beta-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(125, 82, 96, 0.12);
  color: #6a3f4b;
  border: 1px solid rgba(125, 82, 96, 0.25);
}

.avatar-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(121, 116, 126, 0.3);
  overflow: hidden;
  padding: 0;
  background: linear-gradient(135deg, rgba(103, 80, 164, 0.15), rgba(125, 82, 96, 0.15));
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(26, 18, 44, 0.15);
}

.avatar-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.side-nav {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 64px;
  z-index: 40;
}

.glass-side {
  background: rgba(243, 237, 247, 0.9);
  border-right: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 16px;
  padding: 16px 0;
  margin: 0 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 16px 28px rgba(0, 0, 0, 0.18);
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  font-size: 15px;
  border-radius: 12px;
  color: var(--md-on-surface-variant);
  border: 1px solid transparent;
  transition: 0.2s ease;
  text-decoration: none;
  width: 48px;
  height: 48px;
  position: relative;
  box-shadow: 0 10px 20px rgba(26, 18, 44, 0.12);
}

.nav-link:hover {
  border-color: rgba(103, 80, 164, 0.2);
  background: rgba(103, 80, 164, 0.1);
  color: var(--md-on-surface);
  transform: translateY(-2px);
}

.nav-link.active {
  border-color: rgba(103, 80, 164, 0.4);
  background: rgba(103, 80, 164, 0.18);
  color: var(--md-on-surface);
}

.nav-link.icon-only::after {
  content: attr(data-label);
  position: absolute;
  left: 60px;
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.2);
  color: var(--md-on-surface);
  font-size: 12px;
  opacity: 0;
  transform: translateY(4px);
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.nav-link.icon-only:hover::after {
  opacity: 1;
  transform: translateY(0);
}

.profile-popover {
  position: absolute;
  top: 60px;
  right: 12px;
  width: min(360px, 92vw);
  background: var(--md-surface-container);
  border: 1px solid rgba(121, 116, 126, 0.25);
  border-radius: 16px;
  box-shadow: 0 18px 44px rgba(26, 18, 44, 0.18);
  padding: 14px;
  backdrop-filter: blur(12px);
  z-index: 120;
}

.popover-header {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(121, 116, 126, 0.15);
}

.avatar-wrap {
  position: relative;
}

.avatar-wrap img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid rgba(103, 80, 164, 0.35);
}

.change-avatar {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  border: none;
  background: rgba(103, 80, 164, 0.12);
  color: var(--md-primary);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 9999px;
  cursor: pointer;
}

.user-meta {
  flex: 1;
}

.username {
  font-size: 16px;
  font-weight: 600;
  color: var(--md-on-surface);
}

.uid {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  display: flex;
  gap: 6px;
  align-items: center;
}

.uid button {
  background: rgba(103, 80, 164, 0.08);
  border: 1px solid rgba(103, 80, 164, 0.2);
  color: var(--md-primary);
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.section {
  margin-top: 12px;
  padding: 10px;
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  background: var(--md-surface-container-low);
}

.membership {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-on-surface);
}

.icon {
  color: var(--md-primary);
}

.action {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action .points {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.action button {
  background: var(--md-primary);
  color: var(--md-on-primary);
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}

.points .points-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--md-on-surface);
}

.points strong {
  color: var(--md-on-surface);
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.link-btn {
  width: 100%;
  text-align: left;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  font-size: 13px;
  cursor: pointer;
}

.link-btn.danger {
  border-color: rgba(180, 35, 24, 0.35);
  color: #b42318;
  background: rgba(180, 35, 24, 0.08);
}

.profile-toast {
  position: fixed;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--md-surface-container);
  color: var(--md-on-surface);
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid rgba(121, 116, 126, 0.2);
  box-shadow: 0 10px 22px rgba(26, 18, 44, 0.12);
  font-size: 12px;
  z-index: 200;
}

@media (min-width: 768px) {
  .search-wrap {
    display: block;
  }
}

@media (min-width: 1024px) {
  .space-switcher {
    display: flex;
  }
}

.app-shell__content {
  margin-left: 64px;
  margin-top: 56px;
  padding: 16px;
}
</style>
