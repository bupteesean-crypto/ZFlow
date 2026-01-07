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
    { id: 'r1', name: '多啦A梦', tags: ['角色', '机器猫'], created: '2024-06-01', updated: '2024-07-10', usage: 18, preview: '<div class="preview-placeholder">🤖</div>', desc: '温柔机器猫，四次元口袋' },
    { id: 'r2', name: '大雄', tags: ['角色', '男孩'], created: '2024-06-02', updated: '2024-07-12', usage: 15, preview: '<div class="preview-placeholder">👦</div>', desc: '略紧张但勇敢的少年' },
    { id: 'r3', name: '静香', tags: ['角色', '女孩'], created: '2024-06-03', updated: '2024-07-08', usage: 12, preview: '<div class="preview-placeholder">👧</div>', desc: '温柔聪慧，准备科学展' },
    { id: 'r4', name: '角色预留 1', tags: ['角色'], created: '2024-06-04', updated: '2024-07-05', usage: 9, preview: '<div class="preview-placeholder">👤</div>', desc: '备用角色形象' },
    { id: 'r5', name: '角色预留 2', tags: ['角色'], created: '2024-06-05', updated: '2024-07-01', usage: 7, preview: '<div class="preview-placeholder">👤</div>', desc: '备用角色形象' },
  ],
  styles: [
    { id: 's1', name: '赛博霓虹', tags: ['风格', '赛博'], created: '2024-03-21', updated: '2024-06-18', usage: 22, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #0ff, #a0f"></div>', desc: '蓝紫主色，荧光光晕' },
    { id: 's2', name: '校园日常', tags: ['风格', '日常'], created: '2024-03-25', updated: '2024-06-10', usage: 18, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #ffd, #adf"></div>', desc: '明亮校园色，活泼轻盈' },
    { id: 's3', name: '月球探险', tags: ['风格', '科幻'], created: '2024-04-02', updated: '2024-06-05', usage: 14, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #345, #89f"></div>', desc: '冷色月光，银灰质感' },
    { id: 's4', name: '暖色故事书', tags: ['风格', '童趣'], created: '2024-04-12', updated: '2024-06-20', usage: 10, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #fc9, #f96"></div>', desc: '暖色插画风，柔和颗粒' },
    { id: 's5', name: '夜景电影感', tags: ['风格', '电影'], created: '2024-04-18', updated: '2024-06-22', usage: 9, preview: '<div class="preview-placeholder color-preview" style="background: linear-gradient(90deg, #123, #456"></div>', desc: '对比强烈，光影戏剧性' },
  ],
  scenes: [
    { id: 'sc1', name: '空中轨道站', tags: ['场景', '科幻'], created: '2024-04-10', updated: '2024-06-02', usage: 13, preview: '<div class="preview-placeholder">🏙️</div>', desc: '悬浮列车与霓虹高塔' },
    { id: 'sc2', name: '月面遗迹', tags: ['场景', '科幻'], created: '2024-04-12', updated: '2024-06-03', usage: 12, preview: '<div class="preview-placeholder">🌙</div>', desc: '风化巨石阵，发光符号' },
    { id: 'sc3', name: '时光机着陆点', tags: ['场景', '科幻'], created: '2024-04-15', updated: '2024-06-04', usage: 11, preview: '<div class="preview-placeholder">🚀</div>', desc: '月尘着陆，舱门蓝光' },
    { id: 'sc4', name: '秘密控制室', tags: ['场景', '室内'], created: '2024-04-18', updated: '2024-06-06', usage: 10, preview: '<div class="preview-placeholder">🎛️</div>', desc: '圆形控制室，玻璃穹顶' },
    { id: 'sc5', name: '校园草坪展区', tags: ['场景', '校园'], created: '2024-04-20', updated: '2024-06-08', usage: 9, preview: '<div class="preview-placeholder">🏫</div>', desc: '草坪展板，旗子与气球' },
  ],
  voices: [
    { id: 'v1', name: '亲切女声', tags: ['旁白', '女声'], created: '2024-05-08', updated: '2024-06-30', usage: 21, preview: '<div class="preview-placeholder">🎙️</div>', desc: '轻柔叙述，亲和语气' },
    { id: 'v2', name: '沉稳男声', tags: ['旁白', '男声'], created: '2024-05-10', updated: '2024-06-28', usage: 19, preview: '<div class="preview-placeholder">🎙️</div>', desc: '低沉磁性，品牌感' },
    { id: 'v3', name: '活力童声', tags: ['角色', '童声'], created: '2024-05-12', updated: '2024-06-26', usage: 12, preview: '<div class="preview-placeholder">🎙️</div>', desc: '活泼清晰，适合儿童角色' },
  ],
  templates: [
    { id: 't1', name: '分镜合集 1', tags: ['模板', '分镜'], created: '2024-02-10', updated: '2024-06-01', usage: 14, preview: '<div class="preview-placeholder">🎬</div>', desc: '包含航拍/城市夜景分镜' },
    { id: 't2', name: '分镜合集 2', tags: ['模板', '分镜'], created: '2024-02-12', updated: '2024-06-05', usage: 12, preview: '<div class="preview-placeholder">🎬</div>', desc: '校园/室内对话分镜' },
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface-variant);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.asset-tab-btn:hover {
  border-color: rgba(121, 116, 126, 0.35);
  background: rgba(103, 80, 164, 0.08);
}

.asset-tab-btn.active {
  border-color: rgba(103, 80, 164, 0.5);
  background: rgba(103, 80, 164, 0.12);
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
  background: var(--md-surface-container-low);
  border: 1px solid rgba(121, 116, 126, 0.25);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  background: var(--md-surface-container);
  color: var(--md-on-surface);
  cursor: pointer;
  font-size: 12px;
}

.toolbar-btn:hover {
  border-color: rgba(103, 80, 164, 0.3);
  background: rgba(103, 80, 164, 0.12);
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  border-radius: 12px;
  background: var(--md-surface-container);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;
}

.asset-card:hover {
  border-color: rgba(121, 116, 126, 0.35);
}

.asset-card.selected {
  border-color: rgba(103, 80, 164, 0.45);
  background: rgba(103, 80, 164, 0.12);
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
  border: 1px solid rgba(121, 116, 126, 0.25);
  color: var(--md-on-surface-variant);
  background: var(--md-surface-container-low);
}

.asset-preview {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container-low);
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
  border: 1px solid rgba(121, 116, 126, 0.2);
  background: var(--md-surface-container-low);
  color: var(--md-on-surface);
  font-size: 11px;
  cursor: pointer;
}

.asset-card-actions button:hover {
  border-color: rgba(103, 80, 164, 0.35);
  background: rgba(103, 80, 164, 0.15);
}

.empty-state {
  grid-column: 1 / -1;
  padding: 32px;
  text-align: center;
  color: var(--md-on-surface-variant);
  font-size: 14px;
}

.text-2xl { font-size: 24px; }
.font-semibold { font-weight: 600; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-slate-400 { color: var(--md-on-surface-variant); }
.m-0 { margin: 0; }
.mt-2 { margin-top: 8px; }
.mb-1 { margin-bottom: 4px; }
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
</style>
