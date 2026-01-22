<template>
  <div class="assets-page">
    <h1 class="text-2xl font-semibold">Assets Library</h1>
    <p class="text-slate-400">浏览角色、风格、场景、音色和模板。</p>

    <div class="asset-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['asset-tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.name }}
      </button>
    </div>

    <div class="asset-toolbar mt-2">
      <input
        v-model="searchQuery"
        type="search"
        placeholder="搜索资产（名称/标签/描述）"
        class="toolbar-input"
      />
      <select v-model="filterType" class="toolbar-select">
        <option value="">类型不限</option>
        <option v-for="type in currentFilterTypes" :key="type" :value="type">
          {{ type }}
        </option>
      </select>
      <select v-model="sortBy" class="toolbar-select">
        <option value="recent">按更新时间</option>
        <option value="name">按名称</option>
        <option value="usage">按使用频率</option>
      </select>
      <div class="flex items-center gap-2 text-xs">
        <input id="selectAll" type="checkbox" v-model="selectAll" @change="handleSelectAll" />
        <label for="selectAll">批量选择</label>
      </div>
      <div class="asset-actions">
        <button class="toolbar-btn" @click="handleBatchDelete">批量删除</button>
        <button class="toolbar-btn" @click="handleBatchArchive">批量归类</button>
      </div>
    </div>

    <div class="asset-grid">
      <div
        v-for="item in filteredAssets"
        :key="item.id"
        :class="['asset-card', { selected: selectedIds.has(item.id) }]"
      >
        <header>
          <div>
            <div class="flex items-center gap-2">
              <input
                v-if="activeTab !== 'roles'"
                type="checkbox"
                :checked="selectedIds.has(item.id)"
                @change="toggleSelect(item.id)"
              />
              <h3 class="font-semibold m-0 text-sm">{{ item.name }}</h3>
            </div>
            <div class="asset-meta">
              <span>{{ item.created }} 创建</span>
              <span>{{ item.updated }} 更新</span>
              <span>使用 {{ item.usage }}</span>
            </div>
          </div>
          <span class="tag">{{ item.tags.join(' / ') }}</span>
        </header>
        <div class="asset-preview" v-html="item.preview"></div>
        <p class="text-xs text-slate-400 m-0">{{ item.desc }}</p>
        <div v-if="activeTab !== 'roles'" class="asset-card-actions">
          <button @click="handlePreview(item)">预览</button>
          <button @click="handleEdit(item)">编辑</button>
          <button @click="handleDelete(item)">删除</button>
        </div>
      </div>
      <div v-if="filteredAssets.length === 0" class="empty-state">
        暂无该类别的资产
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface AssetItem {
  id: string;
  name: string;
  tags: string[];
  created: string;
  updated: string;
  usage: number;
  preview: string;
  desc: string;
}

const tabs = [
  { id: 'roles', name: '角色库' },
  { id: 'styles', name: '风格库' },
  { id: 'scenes', name: '场景库' },
  { id: 'voices', name: '音色库' },
  { id: 'templates', name: '模板库' },
];

const activeTab = ref('roles');
const searchQuery = ref('');
const filterType = ref('');
const sortBy = ref('recent');
const selectAll = ref(false);
const selectedIds = ref<Set<string>>(new Set());

// Demo data
const assetsData: Record<string, AssetItem[]> = {
  roles: [
    { id: 'r1', name: '零零', tags: ['角色', '机器人'], created: '2024-06-01', updated: '2024-07-10', usage: 18, preview: '<div class="preview-placeholder">🤖</div>', desc: '城市服务机器人，圆润机身，屏幕表情丰富' },
    { id: 'r2', name: '阿沐', tags: ['角色', '快递'], created: '2024-06-02', updated: '2024-07-12', usage: 15, preview: '<div class="preview-placeholder">🛵</div>', desc: '年轻外卖员，短发夹克，背包醒目' },
    { id: 'r3', name: '禾米', tags: ['角色', '植物'], created: '2024-06-03', updated: '2024-07-08', usage: 12, preview: '<div class="preview-placeholder">🌿</div>', desc: '温和植物学家，棕色围裙，随身带本子' },
    { id: 'r4', name: '陈小北', tags: ['角色', '学生'], created: '2024-06-04', updated: '2024-07-05', usage: 9, preview: '<div class="preview-placeholder">📚</div>', desc: '高中生，校服外套，背包贴满贴纸' },
    { id: 'r5', name: '织雾', tags: ['角色', '设计师'], created: '2024-06-05', updated: '2024-07-01', usage: 7, preview: '<div class="preview-placeholder">🧵</div>', desc: '服装设计师，黑白穿搭，轻薄围巾' },
  ],
  styles: [
    { id: 's1', name: '赛博霓虹', tags: ['风格', '赛博'], created: '2024-03-21', updated: '2024-06-18', usage: 22, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #00e5ff, #9c27ff)"></div>', desc: '蓝紫高饱和，霓虹边缘光，金属反射' },
    { id: 's2', name: '校园清晨', tags: ['风格', '日常'], created: '2024-03-25', updated: '2024-06-10', usage: 18, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #fff4c2, #b4d7ff)"></div>', desc: '暖阳与清风感，柔和阴影' },
    { id: 's3', name: '月面银灰', tags: ['风格', '科幻'], created: '2024-04-02', updated: '2024-06-05', usage: 14, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #2c3e50, #8e9eab)"></div>', desc: '冷光、低饱和、颗粒质感' },
    { id: 's4', name: '纸雕童话', tags: ['风格', '童趣'], created: '2024-04-12', updated: '2024-06-20', usage: 10, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #fbd3a6, #f08a5d)"></div>', desc: '纸层叠影、柔和光晕、暖色主调' },
    { id: 's5', name: '雨夜电影感', tags: ['风格', '电影'], created: '2024-04-18', updated: '2024-06-22', usage: 9, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #1a2a6c, #4b6584)"></div>', desc: '高对比冷暖光，湿润反射' },
  ],
  scenes: [
    { id: 'sc1', name: '清晨巷口咖啡店', tags: ['场景', '城市'], created: '2024-04-10', updated: '2024-06-02', usage: 13, preview: '<div class="preview-placeholder">☕</div>', desc: '玻璃门反光，木质吧台，路面湿润' },
    { id: 'sc2', name: '屋顶微风台', tags: ['场景', '城市'], created: '2024-04-12', updated: '2024-06-03', usage: 12, preview: '<div class="preview-placeholder">🌬️</div>', desc: '低矮围栏，晾衣杆与天际线' },
    { id: 'sc3', name: '雨夜公交站', tags: ['场景', '雨夜'], created: '2024-04-15', updated: '2024-06-04', usage: 11, preview: '<div class="preview-placeholder">🌧️</div>', desc: '雨滴灯箱，积水倒影，空旷站台' },
    { id: 'sc4', name: '旧仓库工作室', tags: ['场景', '室内'], created: '2024-04-18', updated: '2024-06-06', usage: 10, preview: '<div class="preview-placeholder">🧰</div>', desc: '金属梁架，落地窗光束，工具散落' },
    { id: 'sc5', name: '山间观景栈道', tags: ['场景', '自然'], created: '2024-04-20', updated: '2024-06-08', usage: 9, preview: '<div class="preview-placeholder">⛰️</div>', desc: '木质栈道，远处云海，逆光轮廓' },
  ],
  voices: [
    { id: 'v1', name: '清亮女声', tags: ['旁白', '女声'], created: '2024-05-08', updated: '2024-06-30', usage: 21, preview: '<div class="preview-placeholder">🎙️</div>', desc: '语速适中，口齿清晰，亲和力强' },
    { id: 'v2', name: '沉稳男声', tags: ['旁白', '男声'], created: '2024-05-10', updated: '2024-06-28', usage: 19, preview: '<div class="preview-placeholder">🎙️</div>', desc: '低沉磁性，适合品牌叙述' },
    { id: 'v3', name: '温柔低语', tags: ['角色', '女声'], created: '2024-05-12', updated: '2024-06-26', usage: 12, preview: '<div class="preview-placeholder">🎙️</div>', desc: '轻声讲述，情绪细腻' },
    { id: 'v4', name: '元气少年', tags: ['角色', '男声'], created: '2024-05-14', updated: '2024-06-24', usage: 10, preview: '<div class="preview-placeholder">🎙️</div>', desc: '语气有活力，适合校园与运动' },
  ],
  templates: [
    { id: 't1', name: '情绪转折模板', tags: ['模板', '剧情'], created: '2024-02-10', updated: '2024-06-01', usage: 14, preview: '<div class="preview-placeholder">🎬</div>', desc: '铺垫→冲突→转念→收束' },
    { id: 't2', name: '产品拆解模板', tags: ['模板', '产品'], created: '2024-02-12', updated: '2024-06-05', usage: 12, preview: '<div class="preview-placeholder">🧩</div>', desc: '痛点→方案→对比→价值' },
    { id: 't3', name: '三段式叙事', tags: ['模板', '故事'], created: '2024-02-18', updated: '2024-06-11', usage: 9, preview: '<div class="preview-placeholder">📚</div>', desc: '开场设定→推进→结尾反转' },
    { id: 't4', name: '旅行节奏模板', tags: ['模板', 'Vlog'], created: '2024-02-20', updated: '2024-06-14', usage: 8, preview: '<div class="preview-placeholder">🧳</div>', desc: '出发→路途→目的地→回程' },
  ],
};

const currentFilterTypes = computed(() => {
  const currentItems = assetsData[activeTab.value] || [];
  const types = new Set<string>();
  currentItems.forEach(item => {
    item.tags.forEach(tag => types.add(tag));
  });
  return Array.from(types);
});

const filteredAssets = computed(() => {
  let list = assetsData[activeTab.value] || [];

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    list = list.filter(item => {
      return item.name.toLowerCase().includes(query) ||
        item.desc.toLowerCase().includes(query) ||
        item.tags.some(t => t.toLowerCase().includes(query));
    });
  }

  // Filter by type
  if (filterType.value) {
    list = list.filter(item => {
      return item.name.includes(filterType.value) ||
        item.tags.some(t => t.toLowerCase().includes(filterType.value.toLowerCase()));
    });
  }

  // Sort
  list = [...list].sort((a, b) => {
    if (sortBy.value === 'name') return a.name.localeCompare(b.name);
    if (sortBy.value === 'usage') return b.usage - a.usage;
    return b.updated.localeCompare(a.updated);
  });

  return list;
});

const toggleSelect = (id: string) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id);
  } else {
    selectedIds.value.add(id);
  }
};

const handleSelectAll = () => {
  if (selectAll.value) {
    filteredAssets.value.forEach(item => selectedIds.value.add(item.id));
  } else {
    selectedIds.value.clear();
  }
};

const handlePreview = (item: AssetItem) => {
  alert(`预览：${item.name}`);
};

const handleEdit = (item: AssetItem) => {
  alert(`编辑：${item.name}`);
};

const handleDelete = (item: AssetItem) => {
  if (confirm(`确定删除 ${item.name} 吗？`)) {
    alert(`删除：${item.name}`);
  }
};

const handleBatchDelete = () => {
  if (selectedIds.value.size === 0) {
    alert('请先选择要删除的资产');
    return;
  }
  if (confirm(`确定删除选中的 ${selectedIds.value.size} 个资产吗？`)) {
    alert(`批量删除：${Array.from(selectedIds.value).join(', ')}`);
    selectedIds.value.clear();
    selectAll.value = false;
  }
};

const handleBatchArchive = () => {
  if (selectedIds.value.size === 0) {
    alert('请先选择要归类的资产');
    return;
  }
  alert(`批量归类：${Array.from(selectedIds.value).join(', ')}`);
};
</script>

<style scoped>
.assets-page {
  min-height: calc(100vh - 56px);
  background: var(--md-surface);
  color: var(--md-on-surface);
}

.asset-tabs {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.asset-tab-btn {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.75);
  color: var(--md-on-surface-variant);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.asset-tab-btn:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(var(--md-accent-rgb), 0.08);
}

.asset-tab-btn.active {
  border-color: rgba(var(--md-accent-rgb), 0.6);
  background: rgba(var(--md-accent-rgb), 0.18);
  color: var(--md-on-surface);
}

.asset-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  padding: 12px 0;
}

.toolbar-input,
.toolbar-select {
  background: var(--md-field-bg);
  border: 1px solid var(--md-stroke);
  color: var(--md-on-surface);
  border-radius: 8px;
  padding: 8px;
  font-size: 13px;
}

.toolbar-input {
  width: 200px;
}

.toolbar-select {
  width: 120px;
}

.toolbar-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
  color: var(--md-on-surface);
  cursor: pointer;
  font-size: 12px;
}

.toolbar-btn:hover {
  border-color: rgba(var(--md-accent-rgb), 0.3);
  background: rgba(var(--md-accent-rgb), 0.12);
}

.asset-actions {
  display: flex;
  gap: 6px;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.asset-card {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 14px;
  background: var(--md-surface-card);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: var(--md-card-shadow-soft);
}

.asset-card:hover {
  border-color: rgba(148, 163, 184, 0.35);
}

.asset-card.selected {
  border-color: rgba(var(--md-accent-rgb), 0.5);
  background: rgba(var(--md-accent-rgb), 0.18);
}

.asset-card header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
}

.asset-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 11px;
  border: 1px solid rgba(var(--md-accent-rgb), 0.35);
  color: #dff8ff;
  background: rgba(var(--md-accent-rgb), 0.18);
}

.asset-preview {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(10, 16, 28, 0.75);
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--md-on-surface-variant);
  font-size: 32px;
  text-align: center;
  padding: 8px;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-preview {
  height: 60px;
  border-radius: 6px;
}

.asset-card-actions {
  display: flex;
  gap: 6px;
}

.asset-card-actions button {
  flex: 1;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(10, 16, 28, 0.85);
  color: var(--md-on-surface);
  font-size: 11px;
  cursor: pointer;
}

.asset-card-actions button:hover {
  border-color: rgba(var(--md-accent-rgb), 0.35);
  background: rgba(var(--md-accent-rgb), 0.15);
}

.empty-state {
  grid-column: 1 / -1;
  padding: 32px;
  text-align: center;
  color: var(--md-on-surface-variant);
  font-size: 14px;
}

</style>
