<template>
  <div class="app-shell">
    <!-- Top Navigation -->
    <nav class="glass-nav fixed top-0 left-0 right-0 z-50">
      <div class="px-5 py-3 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="logo-badge">ZV</div>
          <div>
            <div class="text-sm uppercase tracking-[0.2em] text-slate-400">Z.Video</div>
          </div>
          <div v-if="showSpaceSelector" class="hidden lg:flex items-center space-x-2 pl-4 ml-4 border-l border-white/5">
            <span class="text-xs text-slate-500">Space</span>
            <select class="space-select" v-model="currentSpace" @change="handleSpaceChange">
              <option class="bg-slate-900" value="">选择空间</option>
              <option v-for="space in spaces" :key="space.id" :value="space.id">
                {{ space.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <div v-if="showSearch" class="relative hidden md:block">
            <input
              type="search"
              placeholder="⌘K / 搜索任务"
              class="search-input"
            />
            <span class="search-hint">CTRL+K</span>
          </div>
          <div class="flex items-center space-x-2 text-xs text-slate-400">
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
    <aside class="fixed left-0 top-1/2 -translate-y-1/2 w-16 z-40">
      <div class="glass-side rounded-2xl py-4 flex flex-col items-center space-y-2 mx-2 shadow-lg shadow-black/40">
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
  background: #05070f;
  color: #dfe8ff;
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
  box-shadow: 0 10px 15px -3px rgba(6, 182, 212, 0.3);
}

.space-select {
  text-sm bg-transparent text-slate-200 border border-white/10 rounded-md px-2 py-1 focus:outline-none;
}

.search-input {
  width: 256px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #f1f5f9;
}

.search-input::placeholder {
  color: #64748b;
}

.search-input:focus {
  outline: none;
  ring: 2px;
  ring-color: rgba(34, 211, 238, 0.6);
}

.search-hint {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  color: #64748b;
  letter-spacing: 0.1em;
}

.quota-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(52, 211, 153, 0.1);
  color: #a7f3d0;
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.beta-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.1);
  color: #c7d2fe;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.avatar-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  overflow: hidden;
  padding: 0;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.25), rgba(124, 93, 255, 0.25));
  cursor: pointer;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.35);
}

.avatar-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.glass-side {
  background: linear-gradient(180deg, rgba(11, 14, 24, 0.9), rgba(5, 7, 15, 0.9));
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  font-size: 15px;
  border-radius: 12px;
  color: #6b7599;
  border: 1px solid transparent;
  transition: 0.2s ease;
  text-decoration: none;
  width: 48px;
  height: 48px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

.nav-link:hover {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(124, 93, 255, 0.08);
  color: #e5e9ff;
  transform: translateY(-2px);
}

.nav-link.active {
  border-color: rgba(108, 249, 224, 0.35);
  background: linear-gradient(120deg, rgba(108, 249, 224, 0.12), rgba(124, 93, 255, 0.12));
  color: #e5e9ff;
}

.nav-link.icon-only::after {
  content: attr(data-label);
  position: absolute;
  left: 60px;
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(12, 16, 26, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #dfe8ff;
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
  background: rgba(12, 16, 26, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
  padding: 14px;
  backdrop-filter: blur(12px);
  z-index: 120;
}

.popover-header {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.avatar-wrap {
  position: relative;
}

.avatar-wrap img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid rgba(108, 249, 224, 0.35);
}

.change-avatar {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #e7ecf7;
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
  color: #e7ecf7;
}

.uid {
  font-size: 12px;
  color: #9aa8c7;
  display: flex;
  gap: 6px;
  align-items: center;
}

.uid button {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e7ecf7;
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.section {
  margin-top: 12px;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
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
  color: #e7ecf7;
}

.icon {
  color: #9cfbe6;
}

.action {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action .points {
  font-size: 12px;
  color: #c7d2fe;
}

.action button {
  background: linear-gradient(135deg, rgba(108, 249, 224, 0.24), rgba(124, 93, 255, 0.24));
  color: #0b1324;
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
  color: #dfe8ff;
}

.points strong {
  color: #e7ecf7;
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
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: #e7ecf7;
  font-size: 13px;
  cursor: pointer;
}

.link-btn.danger {
  border-color: rgba(248, 113, 113, 0.3);
  color: #fecdd3;
  background: rgba(248, 113, 113, 0.08);
}

.profile-toast {
  position: fixed;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 24, 36, 0.92);
  color: #e7ecf7;
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  font-size: 12px;
  z-index: 200;
}

.app-shell__content {
  margin-left: 64px;
  margin-top: 56px;
  padding: 16px;
}
</style>
