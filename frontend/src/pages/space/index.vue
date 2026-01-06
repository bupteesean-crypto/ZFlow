<template>
  <div class="space-page">
    <div class="space-hero">
      <div>
        <h1 class="text-2xl font-semibold">{{ userType === 'team' ? '团队空间' : '我的空间' }}</h1>
        <div class="flex items-center gap-2 mt-1 text-xs text-slate-400">
          <span class="space-badge">{{ userType === 'team' ? '团队用户' : '个人用户' }}</span>
          <span class="space-badge">{{ spaceName }}</span>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs">
        <button class="space-btn" @click="toggleUserType">
          模拟切换个人/团队
        </button>
        <button class="space-btn" @click="showSpaceSelector = true">
          选择空间
        </button>
      </div>
    </div>

    <div class="section-title">
      <h2>进行中 / 素材生成中</h2>
      <span class="pill">草稿 + 未剪辑</span>
    </div>
    <div class="space-cards">
      <div
        v-for="item in inProgressItems"
        :key="item.id"
        class="space-card"
        @click="openJourney(item)"
      >
        <div class="flex items-center justify-between mb-1">
          <h3>{{ item.title }}</h3>
          <StatusBadge status="progress" />
        </div>
        <p>{{ item.desc }}</p>
        <div class="mt-2 flex items-center gap-2 text-xs text-slate-400">
          <span class="space-badge">最后更新：{{ formatTime(item.updatedAt) }}</span>
        </div>
      </div>
      <div v-if="inProgressItems.length === 0" class="empty-state">
        暂无进行中的项目
      </div>
    </div>

    <div class="section-title">
      <h2>已完成 / 已导出</h2>
      <span class="pill">成片 / 可下载</span>
    </div>
    <div class="space-cards">
      <div
        v-for="item in doneItems"
        :key="item.id"
        class="space-card"
      >
        <div class="flex items-center justify-between mb-1">
          <h3>{{ item.title }}</h3>
          <StatusBadge status="exported" />
        </div>
        <p>{{ item.desc }}</p>
        <div class="card-actions">
          <button class="action-btn">预览</button>
          <button class="action-btn">下载</button>
        </div>
      </div>
      <div v-if="doneItems.length === 0" class="empty-state">
        暂无已完成的项目
      </div>
    </div>

    <!-- Space Selector Modal -->
    <div v-if="showSpaceSelector" class="modal-overlay" @click.self="showSpaceSelector = false">
      <div class="space-selector">
        <div class="flex items-center justify-between mb-3">
          <div>
            <div class="text-sm text-slate-400">选择团队空间</div>
            <div class="text-lg font-semibold text-slate-100">最近使用优先</div>
          </div>
          <button class="text-slate-400 text-sm" @click="showSpaceSelector = false">关闭</button>
        </div>
        <div class="space-grid">
          <div
            v-for="space in teamSpaces"
            :key="space.id"
            class="space-option"
            @click="selectSpace(space)"
          >
            <div class="flex items-center justify-between">
              <div>
                <div class="font-semibold text-slate-100">{{ space.name }}</div>
                <div class="meta">成员 {{ space.members }} | 最近使用 {{ space.recent ? '是' : '否' }}</div>
              </div>
              <span v-if="space.recent" class="pill">最近</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import StatusBadge from '@/components/common/StatusBadge.vue';
import { fetchProjects } from '@/api/projects';

const router = useRouter();

interface Journey {
  id: string;
  title: string;
  desc: string;
  status: 'progress' | 'exported';
  updatedAt: number;
}

interface TeamSpace {
  id: string;
  name: string;
  recent: boolean;
  members: number;
}

const userType = ref<'personal' | 'team'>('personal');
const spaceName = ref('个人空间');
const showSpaceSelector = ref(false);

const teamSpaces: TeamSpace[] = [
  { id: 'team-alpha', name: 'Alpha 团队', recent: true, members: 12 },
  { id: 'team-beta', name: 'Beta 创意组', recent: false, members: 9 },
  { id: 'team-lab', name: '实验室 Space', recent: false, members: 5 },
];

const inProgressItems = ref<Journey[]>([]);
const doneItems = ref<Journey[]>([]);

const formatTime = (ts: number) => {
  return new Date(ts).toLocaleString();
};

const toggleUserType = () => {
  userType.value = userType.value === 'team' ? 'personal' : 'team';
  spaceName.value = userType.value === 'team' ? 'Alpha 团队' : '个人空间';
};

const selectSpace = (space: TeamSpace) => {
  spaceName.value = space.name;
  showSpaceSelector.value = false;
};

const openJourney = (item: Journey) => {
  // Store journey info and navigate to materials
  sessionStorage.setItem('currentProjectName', item.title);
  sessionStorage.setItem('currentProjectId', item.id);
  sessionStorage.setItem('currentAssetPackageId', item.pkgId || '');
  router.push('/materials');
};

const statusToJourney = (status: string) => {
  if (status === 'exported') return 'exported';
  return 'progress';
};

const buildDesc = (status: string) => {
  if (status === 'exported') return '视频已完成渲染';
  if (status === 'editing') return '素材包已生成，可继续微调/剪辑';
  if (status === 'generating') return '素材生成中';
  return '草稿创建中';
};

onMounted(async () => {
  const storedUserType = sessionStorage.getItem('userType');
  if (storedUserType === 'team') {
    userType.value = 'team';
    spaceName.value = '团队空间';
  }

  try {
    const data = await fetchProjects();
    const progress: Journey[] = [];
    const done: Journey[] = [];

    data.list.forEach(project => {
      const mapped: Journey = {
        id: project.id,
        title: project.name || '未命名创作',
        desc: buildDesc(project.status),
        status: statusToJourney(project.status),
        updatedAt: project.updated_at ? Date.parse(project.updated_at) : Date.now(),
        pkgId: project.last_material_package_id || '',
      };
      if (mapped.status === 'exported') {
        done.push(mapped);
      } else {
        progress.push(mapped);
      }
    });

    inProgressItems.value = progress;
    doneItems.value = done;
  } catch (err) {
    inProgressItems.value = [];
    doneItems.value = [];
  }
});
</script>

<style scoped>
.space-page {
  min-height: calc(100vh - 56px);
}

.space-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.space-badge {
  padding: 6px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
  color: #a5b0d5;
}

.space-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #c7d2fe;
  cursor: pointer;
  font-size: 12px;
}

.space-btn:hover {
  border-color: rgba(108, 249, 224, 0.3);
  background: rgba(108, 249, 224, 0.1);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 24px 0 12px;
}

.section-title h2 {
  margin: 0;
  font-size: 18px;
  color: #e5ecff;
}

.pill {
  padding: 4px 8px;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 11px;
  color: #9fb1ff;
}

.space-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.space-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
}

.space-card:hover {
  border-color: rgba(108, 249, 224, 0.3);
  background: rgba(108, 249, 224, 0.05);
}

.space-card h3 {
  margin: 0 0 6px;
  font-size: 14px;
  color: #e5ecff;
}

.space-card p {
  margin: 0;
  font-size: 12px;
  color: #8ca0c9;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.action-btn {
  flex: 1;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #e5ecff;
  cursor: pointer;
  font-size: 12px;
}

.action-btn:hover {
  border-color: rgba(108, 249, 224, 0.3);
  background: rgba(108, 249, 224, 0.1);
}

.empty-state {
  grid-column: 1 / -1;
  padding: 32px;
  text-align: center;
  color: #6b7599;
  font-size: 14px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.space-selector {
  width: min(520px, 90vw);
  background: rgba(10, 14, 24, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.6);
}

.space-option {
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 8px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  transition: all 0.2s ease;
}

.space-option:hover {
  border-color: rgba(108, 249, 224, 0.35);
}

.meta {
  font-size: 12px;
  color: #8ca0c9;
}

.space-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.text-2xl { font-size: 24px; }
.font-semibold { font-weight: 600; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-lg { font-size: 18px; }
.text-slate-100 { color: #e5ecff; }
.text-slate-400 { color: #9aa8c7; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mb-1 { margin-bottom: 4px; }
.mb-3 { margin-bottom: 12px; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 8px; }
</style>
