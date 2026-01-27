<template>
  <div class="admin-users-page">
    <header class="page-header">
      <div>
        <div class="page-title">账号管理后台</div>
        <div class="page-subtitle">用于管理企业邀请码、成员账号与密码（与创作平台分离）。</div>
      </div>
      <RouterLink to="/" class="back-link">返回平台</RouterLink>
    </header>

    <section class="panel">
      <div class="panel-title">企业管理</div>
      <div class="form-row">
        <input v-model="companyName" class="field" placeholder="新企业名称" />
        <button class="primary-btn" :disabled="creatingCompany" @click="handleCreateCompany">
          {{ creatingCompany ? '创建中...' : '创建企业' }}
        </button>
      </div>
      <div v-if="companiesLoading" class="muted">加载企业中...</div>
      <div v-else-if="companies.length === 0" class="muted">暂无企业，请先创建。</div>
      <div v-else class="company-grid">
        <div v-for="company in companies" :key="company.id" class="company-card">
          <div class="company-main">
            <div class="company-name">{{ company.name }}</div>
            <div class="company-meta">邀请码：{{ company.invite_code }}</div>
          </div>
          <div class="company-stats">
            <span :class="['pill', adminCountByCompany[company.id] > 5 ? 'warning' : '']">
              管理员 {{ adminCountByCompany[company.id] || 0 }}/5
            </span>
            <span class="pill">成员 {{ memberCountByCompany[company.id] || 0 }}</span>
          </div>
          <button class="ghost-btn" @click="handleResetInvite(company.id)">重置邀请码</button>
        </div>
      </div>
      <div class="hint">提示：管理员超过 5 人允许创建，但会提示超额。</div>
    </section>

    <section class="panel">
      <div class="panel-title">创建账号</div>
      <div class="form-grid">
        <input v-model="newUsername" class="field" placeholder="账号名称" />
        <input v-model="newPassword" class="field" type="password" placeholder="初始密码" />
        <select v-model="accountType" class="field">
          <option value="personal">个人账号</option>
          <option value="company">企业账号</option>
        </select>
        <div class="role-group">
          <label><input type="checkbox" value="admin" v-model="roles" /> 管理员</label>
          <label><input type="checkbox" value="creator" v-model="roles" /> 创作者</label>
        </div>
      </div>

      <div class="form-grid" v-if="accountType === 'company'">
        <select v-model="companyAction" class="field">
          <option value="create">创建企业邀请码</option>
          <option value="join">加入企业邀请码</option>
        </select>
        <input
          v-if="companyAction === 'create'"
          v-model="createCompanyName"
          class="field"
          placeholder="新企业名称"
        />
        <input
          v-else
          v-model="companyInviteCode"
          class="field"
          placeholder="企业邀请码"
        />
      </div>

      <div class="form-grid" v-else>
        <input
          v-model="companyInviteCode"
          class="field"
          placeholder="可选：企业邀请码（加入企业）"
        />
      </div>

      <button class="primary-btn" :disabled="creatingUser" @click="handleCreateUser">
        {{ creatingUser ? '创建中...' : '创建账号' }}
      </button>
    </section>

    <section class="panel">
      <div class="panel-title">账号列表</div>
      <div v-if="usersLoading" class="muted">加载账号中...</div>
      <div v-else-if="users.length === 0" class="muted">暂无账号，请先创建。</div>
      <div v-else class="user-list">
        <div v-for="user in users" :key="user.id" class="user-card">
          <div class="user-info">
            <div class="user-avatar">
              <img :src="user.avatar_url || defaultAvatar" alt="avatar" />
            </div>
            <div class="user-name">
              {{ user.display_name || user.username }}
              <span v-if="user.is_platform_admin" class="tag">平台管理员</span>
            </div>
            <div class="user-meta">
              {{ user.account_type === 'company' ? '企业账号' : '个人账号' }} · 角色：{{ formatRoles(user.roles) }}
            </div>
            <div class="user-meta">账号：{{ user.username }}</div>
            <div class="user-meta">企业：{{ companyNameById[user.company_id || ''] || '未绑定' }}</div>
          </div>
          <div class="user-actions">
            <div class="action-row">
              <input
                v-model="displayNameInputs[user.id]"
                type="text"
                class="field small"
                placeholder="新昵称"
              />
              <button class="ghost-btn" @click="handleUpdateDisplayName(user.id)">更新昵称</button>
            </div>
            <label class="ghost-btn upload-btn">
              上传头像
              <input
                type="file"
                accept="image/*"
                class="file-input"
                @change="handleAvatarUpload(user.id, $event)"
              />
            </label>
            <div class="action-row">
            <input
              v-model="passwordInputs[user.id]"
              type="password"
              class="field small"
              placeholder="新密码"
            />
            <button class="ghost-btn" @click="handleResetPassword(user.id)">改密码</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  createCompany,
  createUser,
  fetchCompanies,
  fetchUsers,
  resetCompanyInvite,
  updateUserPassword,
  type Company,
  type UserAccount,
} from '@/api/auth';
import { updateUserProfileByAdmin, uploadUserAvatarByAdmin } from '@/api/userProfile';

const companies = ref<Company[]>([]);
const users = ref<UserAccount[]>([]);
const companiesLoading = ref(false);
const usersLoading = ref(false);
const creatingCompany = ref(false);
const creatingUser = ref(false);

const companyName = ref('');
const newUsername = ref('');
const newPassword = ref('');
const accountType = ref<'personal' | 'company'>('personal');
const roles = ref<string[]>(['creator']);
const companyAction = ref<'create' | 'join'>('create');
const createCompanyName = ref('');
const companyInviteCode = ref('');
const passwordInputs = ref<Record<string, string>>({});
const displayNameInputs = ref<Record<string, string>>({});
const defaultAvatar = 'https://placehold.co/64x64';

const companyNameById = computed(() => {
  const map: Record<string, string> = {};
  companies.value.forEach(company => {
    map[company.id] = company.name;
  });
  return map;
});

const adminCountByCompany = computed(() => {
  const counts: Record<string, number> = {};
  users.value.forEach(user => {
    if (!user.company_id) return;
    if (!Array.isArray(user.roles) || !user.roles.includes('admin')) return;
    counts[user.company_id] = (counts[user.company_id] || 0) + 1;
  });
  return counts;
});

const memberCountByCompany = computed(() => {
  const counts: Record<string, number> = {};
  users.value.forEach(user => {
    if (!user.company_id) return;
    counts[user.company_id] = (counts[user.company_id] || 0) + 1;
  });
  return counts;
});

const formatRoles = (items: string[] = []) => {
  if (!items.length) return '未设置';
  return items
    .map(item => (item === 'admin' ? '管理员' : item === 'creator' ? '创作者' : item))
    .join(' / ');
};

const loadCompanies = async () => {
  companiesLoading.value = true;
  try {
    const data = await fetchCompanies();
    companies.value = data.list || [];
  } catch (err) {
    alert(err instanceof Error ? err.message : '企业加载失败');
  } finally {
    companiesLoading.value = false;
  }
};

const loadUsers = async () => {
  usersLoading.value = true;
  try {
    const data = await fetchUsers();
    users.value = data.list || [];
  } catch (err) {
    alert(err instanceof Error ? err.message : '账号加载失败');
  } finally {
    usersLoading.value = false;
  }
};

const handleCreateCompany = async () => {
  if (!companyName.value.trim()) {
    alert('请输入企业名称');
    return;
  }
  creatingCompany.value = true;
  try {
    await createCompany(companyName.value.trim());
    companyName.value = '';
    await loadCompanies();
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建企业失败');
  } finally {
    creatingCompany.value = false;
  }
};

const handleResetInvite = async (companyId: string) => {
  try {
    await resetCompanyInvite(companyId);
    await loadCompanies();
  } catch (err) {
    alert(err instanceof Error ? err.message : '重置邀请码失败');
  }
};

const handleCreateUser = async () => {
  if (!newUsername.value.trim() || !newPassword.value) {
    alert('请输入账号和密码');
    return;
  }
  if (accountType.value === 'company') {
    if (companyAction.value === 'create' && !createCompanyName.value.trim()) {
      alert('请输入企业名称');
      return;
    }
    if (companyAction.value === 'join' && !companyInviteCode.value.trim()) {
      alert('请输入企业邀请码');
      return;
    }
  }
  creatingUser.value = true;
  try {
    await createUser({
      username: newUsername.value.trim(),
      password: newPassword.value,
      account_type: accountType.value,
      roles: roles.value,
      create_company_name:
        accountType.value === 'company' && companyAction.value === 'create'
          ? createCompanyName.value.trim()
          : undefined,
      company_invite_code: companyInviteCode.value.trim() || undefined,
    });
    newUsername.value = '';
    newPassword.value = '';
    createCompanyName.value = '';
    companyInviteCode.value = '';
    if (!roles.value.length) {
      roles.value = ['creator'];
    }
    await loadUsers();
    await loadCompanies();
  } catch (err) {
    alert(err instanceof Error ? err.message : '创建账号失败');
  } finally {
    creatingUser.value = false;
  }
};

const handleResetPassword = async (userId: string) => {
  const nextPassword = passwordInputs.value[userId];
  if (!nextPassword) {
    alert('请输入新密码');
    return;
  }
  try {
    await updateUserPassword(userId, nextPassword);
    passwordInputs.value[userId] = '';
    alert('密码已更新');
  } catch (err) {
    alert(err instanceof Error ? err.message : '修改密码失败');
  }
};

const handleUpdateDisplayName = async (userId: string) => {
  const nextName = displayNameInputs.value[userId]?.trim();
  if (!nextName) {
    alert('请输入昵称');
    return;
  }
  try {
    await updateUserProfileByAdmin(userId, { display_name: nextName });
    displayNameInputs.value[userId] = '';
    await loadUsers();
  } catch (err) {
    alert(err instanceof Error ? err.message : '更新昵称失败');
  }
};

const handleAvatarUpload = async (userId: string, event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    await uploadUserAvatarByAdmin(userId, file);
    await loadUsers();
  } catch (err) {
    alert(err instanceof Error ? err.message : '上传头像失败');
  } finally {
    input.value = '';
  }
};

onMounted(() => {
  loadCompanies();
  loadUsers();
});
</script>

<style scoped>
.admin-users-page {
  min-height: 100vh;
  padding: 80px 6vw 60px;
  color: var(--md-on-surface);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
}

.page-subtitle {
  font-size: 14px;
  color: var(--md-on-surface-variant);
  margin-top: 6px;
}

.back-link {
  color: var(--md-primary);
}

.panel {
  background: var(--md-surface-card);
  border: 1px solid var(--md-stroke);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 18px;
  box-shadow: var(--md-card-shadow-soft);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  margin-bottom: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.role-group {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  color: var(--md-on-surface);
}

.field {
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 10px 12px;
  background: var(--md-field-bg);
  color: var(--md-on-surface);
}

.field.small {
  padding: 8px 10px;
}

.primary-btn {
  border-radius: 10px;
  padding: 10px 18px;
  background: var(--md-primary);
  color: var(--md-on-primary);
  border: none;
}

.ghost-btn {
  border-radius: 10px;
  padding: 8px 12px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: var(--md-on-surface);
}

.company-grid {
  display: grid;
  gap: 12px;
}

.company-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(10, 16, 28, 0.7);
}

.company-name {
  font-size: 15px;
  font-weight: 600;
}

.company-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.company-stats {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(77, 231, 255, 0.12);
  color: var(--md-on-surface);
}

.pill.warning {
  background: rgba(248, 113, 113, 0.2);
  color: #fecaca;
}

.hint {
  font-size: 12px;
  color: var(--md-on-surface-variant);
  margin-top: 12px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(10, 16, 28, 0.7);
  gap: 16px;
}

.user-info {
  display: grid;
  gap: 6px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
}

.user-meta {
  font-size: 12px;
  color: var(--md-on-surface-variant);
}

.user-actions {
  display: grid;
  gap: 8px;
  min-width: 280px;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.file-input {
  display: none;
}

.tag {
  margin-left: 8px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(77, 231, 255, 0.2);
  color: var(--md-on-surface);
}

.muted {
  font-size: 13px;
  color: var(--md-on-surface-variant);
}

@media (max-width: 960px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .company-card,
  .user-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
