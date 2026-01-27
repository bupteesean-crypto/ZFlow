<template>
  <div class="app-shell">
    <!-- Top Navigation -->
    <nav class="glass-nav">
      <div class="top-nav">
        <div class="top-nav__left">
          <div class="logo-badge">ZF</div>
          <div class="brand-name">ZFlow</div>
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
    <SideNav :items="navItems" />

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
          <button class="change-avatar" @click="handleChangeAvatar" :disabled="uploadingAvatar">
            {{ uploadingAvatar ? '上传中...' : '更换' }}
          </button>
        </div>
        <div class="user-meta">
          <div class="username">
            <template v-if="!editingName">
              {{ displayName }}
              <button class="ghost-link" @click="startEditName">编辑昵称</button>
            </template>
            <template v-else>
              <input v-model="displayNameDraft" class="inline-input" maxlength="24" />
              <button class="ghost-link" @click="saveDisplayName" :disabled="savingProfile">
                {{ savingProfile ? '保存中' : '保存' }}
              </button>
              <button class="ghost-link" @click="cancelEditName">取消</button>
            </template>
          </div>
          <div class="uid">
            UID: {{ userUid }}
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
        <button class="link-btn" @click="openApiSettings">API 设置</button>
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

  <ApiSettingsModal v-model:show="showApiSettings" @saved="handleApiSaved" />
  <input
    ref="avatarInput"
    type="file"
    accept="image/*"
    class="file-input"
    @change="handleAvatarSelected"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import SideNav from './SideNav.vue';
import ApiSettingsModal from '../ApiSettingsModal.vue';
import { fetchMyProfile, updateMyProfile, uploadMyAvatar } from '@/api/userProfile';

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
const avatarInput = ref<HTMLInputElement | null>(null);
const showProfile = ref(false);
const toastVisible = ref(false);
const toastMessage = ref('');
const currentSpace = ref('');
const showApiSettings = ref(false);
const uploadingAvatar = ref(false);
const savingProfile = ref(false);
const editingName = ref(false);
const displayNameDraft = ref('');

const profile = ref({
  id: '',
  username: props.username,
  displayName: props.username,
  avatarUrl: props.avatarUrl,
  uid: props.uid,
});

const navItems: NavItem[] = [
  { name: 'landing', to: '/', icon: '⌂', label: '首页' },
  { name: 'materials', to: '/materials', icon: '✦', label: '素材' },
  { name: 'editor', to: '/editor', icon: '✎', label: '编辑器' },
  { name: 'assets', to: '/assets', icon: '⟡', label: '资产库' },
  { name: 'space', to: '/space', icon: '★', label: '我的空间' },
];

const toggleProfile = () => {
  showProfile.value = !showProfile.value;
};

const closeProfile = () => {
  showProfile.value = false;
};

const copyUid = async () => {
  try {
    await navigator.clipboard.writeText(userUid.value);
    showToast('复制成功');
  } catch {
    showToast('复制失败');
  }
};

const handleChangeAvatar = () => {
  if (uploadingAvatar.value) return;
  avatarInput.value?.click();
};

const handleAvatarSelected = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploadingAvatar.value = true;
  try {
    const result = await uploadMyAvatar(file);
    applyProfileUpdate({ avatar_url: result.avatar_url });
    showToast('头像已更新');
  } catch (err) {
    showToast(err instanceof Error ? err.message : '上传失败');
  } finally {
    uploadingAvatar.value = false;
    input.value = '';
  }
};

const startEditName = () => {
  displayNameDraft.value = profile.value.displayName;
  editingName.value = true;
};

const cancelEditName = () => {
  editingName.value = false;
  displayNameDraft.value = '';
};

const saveDisplayName = async () => {
  const nextName = displayNameDraft.value.trim();
  if (!nextName) {
    showToast('请输入昵称');
    return;
  }
  savingProfile.value = true;
  try {
    const updated = await updateMyProfile({ display_name: nextName });
    applyProfile(updated);
    showToast('昵称已更新');
  } catch (err) {
    showToast(err instanceof Error ? err.message : '保存失败');
  } finally {
    savingProfile.value = false;
    editingName.value = false;
  }
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

const isAuthenticated = () => {
  return (
    sessionStorage.getItem('authenticated') === 'true' ||
    Boolean(sessionStorage.getItem('session_token'))
  );
};

const isPlatformAdmin = () => {
  const raw = sessionStorage.getItem('user');
  if (!raw) return false;
  try {
    return Boolean(JSON.parse(raw)?.is_platform_admin);
  } catch {
    return false;
  }
};

const checkApiSettings = () => {
  if (!isAuthenticated()) return;
  if (isPlatformAdmin()) return;
  const configured = sessionStorage.getItem('llmConfigured') === 'true';
  if (!configured) {
    showApiSettings.value = true;
  }
};

const openApiSettings = () => {
  showApiSettings.value = true;
};

const handleApiSaved = () => {
  showApiSettings.value = false;
};

const loadSessionProfile = () => {
  const raw = sessionStorage.getItem('user');
  if (!raw) return;
  try {
    const user = JSON.parse(raw);
    profile.value.id = user.id || '';
    profile.value.uid = user.uid || (user.id ? String(user.id).slice(0, 8) : '');
    profile.value.username = user.username || profile.value.username;
    profile.value.displayName = user.display_name || user.username || profile.value.displayName;
    profile.value.avatarUrl = user.avatar_url || profile.value.avatarUrl;
  } catch {
    // ignore session parse errors
  }
};

const applyProfileUpdate = (partial: { display_name?: string; avatar_url?: string }) => {
  const raw = sessionStorage.getItem('user');
  if (!raw) return;
  try {
    const user = JSON.parse(raw);
    if (partial.display_name !== undefined) {
      user.display_name = partial.display_name;
      profile.value.displayName = partial.display_name || profile.value.displayName;
    }
    if (partial.avatar_url !== undefined) {
      user.avatar_url = partial.avatar_url;
      profile.value.avatarUrl = partial.avatar_url || profile.value.avatarUrl;
    }
    sessionStorage.setItem('user', JSON.stringify(user));
  } catch {
    // ignore session update errors
  }
};

const applyProfile = (data: { id: string; username: string; display_name: string; avatar_url: string }) => {
  profile.value.id = data.id;
  profile.value.uid = data.id ? data.id.slice(0, 8) : profile.value.uid;
  profile.value.username = data.username;
  profile.value.displayName = data.display_name || data.username;
  profile.value.avatarUrl = data.avatar_url || '';
  applyProfileUpdate({ display_name: profile.value.displayName, avatar_url: profile.value.avatarUrl });
};

const refreshProfile = async () => {
  if (!isAuthenticated()) return;
  try {
    const data = await fetchMyProfile();
    applyProfile(data);
  } catch {
    // Ignore profile fetch errors for now
  }
};

const displayName = computed(() => profile.value.displayName || profile.value.username || props.username);
const userUid = computed(() => profile.value.uid || props.uid);
const avatarUrl = computed(() => profile.value.avatarUrl || props.avatarUrl);

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

onMounted(() => {
  loadSessionProfile();
  refreshProfile();
  checkApiSettings();
});
watch(
  () => route.fullPath,
  () => {
    if (!showApiSettings.value) {
      checkApiSettings();
    }
  },
);
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.logo-badge {
  height: 36px;
  width: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.95), rgba(var(--md-accent-2-rgb), 0.82));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  box-shadow: 0 12px 22px rgba(var(--md-accent-rgb), 0.28);
}

.space-select {
  font-size: 0.875rem;
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  border: 1px solid var(--md-stroke);
  border-radius: 0.375rem;
  padding: 0.25rem 0.5rem;
}

.space-select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--md-accent-rgb), 0.35);
}

.search-input {
  width: 256px;
  background: var(--md-surface-container-low);
  border: 1px solid var(--md-stroke);
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
  box-shadow: 0 0 0 2px rgba(var(--md-accent-rgb), 0.35);
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
  background: rgba(var(--md-accent-rgb), 0.12);
  color: var(--md-primary);
  border: 1px solid rgba(var(--md-accent-rgb), 0.25);
}

.beta-badge {
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(var(--md-accent-2-rgb), 0.12);
  color: #a7f3d0;
  border: 1px solid rgba(var(--md-accent-2-rgb), 0.25);
}

.avatar-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--md-stroke);
  overflow: hidden;
  padding: 0;
  background: linear-gradient(135deg, rgba(var(--md-accent-rgb), 0.15), rgba(var(--md-accent-2-rgb), 0.15));
  cursor: pointer;
  box-shadow: 0 12px 20px rgba(2, 6, 23, 0.35);
}

.avatar-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-popover {
  position: absolute;
  top: 60px;
  right: 12px;
  width: min(360px, 92vw);
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  box-shadow: 0 24px 56px rgba(2, 6, 23, 0.45);
  padding: 14px;
  backdrop-filter: blur(12px);
  z-index: var(--layer-popover);
}

.popover-header {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
}

.avatar-wrap {
  position: relative;
}

.avatar-wrap img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid rgba(var(--md-accent-rgb), 0.35);
}

.change-avatar {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  border: none;
  background: rgba(var(--md-accent-rgb), 0.12);
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
  background: rgba(var(--md-accent-rgb), 0.08);
  border: 1px solid rgba(var(--md-accent-rgb), 0.25);
  color: var(--md-primary);
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.ghost-link {
  margin-left: 8px;
  background: transparent;
  border: none;
  color: var(--md-primary);
  font-size: 12px;
  cursor: pointer;
}

.inline-input {
  min-width: 140px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: var(--md-field-bg);
  color: var(--md-on-surface);
  padding: 4px 8px;
  font-size: 12px;
  margin-right: 8px;
}

.file-input {
  display: none;
}

.section {
  margin-top: 12px;
  padding: 10px;
  border: 1px solid var(--md-stroke);
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
  border: 1px solid var(--md-stroke);
  background: rgba(15, 23, 42, 0.75);
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
  background: var(--md-surface-card);
  color: var(--md-on-surface);
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid var(--md-stroke);
  box-shadow: 0 12px 22px rgba(2, 6, 23, 0.35);
  font-size: 12px;
  z-index: var(--layer-toast);
}

.app-shell__content {
  margin-left: 64px;
  margin-top: 56px;
  padding: 16px;
}
</style>
