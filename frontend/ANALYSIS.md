# Z.Video HTML Prototype Analysis

## Overview
The static HTML prototype in `Z.video/` is a comprehensive UI/UX design for a video generation platform.
This document outlines the pages, components, and data structures that need to be migrated to the Vue frontend in `ZFlow/frontend/`.

---

## Page Mapping

| HTML File | Purpose | Vue Target |
|-----------|---------|------------|
| `index.html` | Entry redirect → login | N/A (router redirect) |
| `pages/login.html` | Login/Register (personal/team) | `pages/login/index.vue` |
| `pages/landing.html` | Home page with prompt input | `pages/landing/index.vue` |
| `pages/materials.html` | Material package editor (3-column layout) | `pages/materials/index.vue` |
| `pages/editor.html` | Video editing workspace (timeline, shots) | `pages/editor/index.vue` |
| `pages/assets.html` | Asset library (roles, styles, scenes, voices) | `pages/assets/index.vue` |
| `pages/space.html` | User space/history (personal/team) | `pages/space/index.vue` |

---

## Shared UI Components

### Layout Components

1. **AppShell** (`shared/app-shell.html`)
   - Top navigation bar with logo, search, quota badge, user avatar
   - Left sidebar icon navigation
   - Main content area

2. **GlassNav** (Top Navigation)
   - Logo: ZV badge + "Z.Video" label
   - Space selector dropdown
   - Search input (⌘K placeholder)
   - Quota/Beta badges
   - User avatar button → profile popover

3. **GlassSide** (Left Sidebar)
   - Icon-only navigation with tooltips
   - Items: Home (⌂), Materials (✦), Editor (✎), Assets (⟡), Space (★)
   - Active state highlighting

4. **ProfilePopover**
   - Avatar with "更换" (change) button
   - Username and UID with copy button
   - Membership status + points
   - Action buttons: subscribe, orders, logout

### Reusable UI Elements

1. **Card/Panel Components**
   - `.glass-panel` - gradient glass background
   - `.e-card` - editor card with header
   - `.demo-card` - hoverable card with transform
   - `.candidate-card` - selectable asset card

2. **Input Components**
   - `.entry-shell` - expandable prompt input (minimal/expanded states)
   - `.input-console` - terminal-style input
   - `.chat-input` - chat textarea + send button
   - `.toggle-switch` - iOS-style toggle
   - `.segmented` - segmented control
   - `.mode-toggle` - general/pro mode switcher

3. **Button Components**
   - `.pill-btn` - rounded pill button (primary/ghost)
   - `.btn-primary` - gradient primary button
   - `.btn-ghost` - transparent ghost button
   - `.link-btn` - text link button (danger variant)

4. **Status/Tag Components**
   - `.badge` / `.pill` / `.tag` - status indicators
   - `.status-pill` - dynamic status with colors (pending/loading/done/fail)
   - `.hero-badge` - glowing badge

5. **Feedback Components**
   - `.profile-toast` - floating toast message
   - `.modal` - overlay modal container
   - `.skeleton` - loading skeleton

---

## Data Structures (Mock → API)

### 1. Asset Package (素材包)
```typescript
interface AssetPackage {
  id: string;                  // e.g., "pkg-1", "pkg-2"
  title: string;               // e.g., "京韵田园绘梦（v1）"
  status: 'pending' | 'loading' | 'done' | 'fail';
  createdAt: number;
  summary: string;              // Story梗概
  style: string;                // 美术风格
  roles: Role[];
  scenes: Scene[];
  storyboard: StoryboardShot[];
}
```

### 2. Role (角色)
```typescript
interface Role {
  name: string;
  visuals: VisualCandidate[];   // Image candidates
  voices: VoiceCandidate[];     // Audio candidates
}

interface VisualCandidate {
  tag: string;         // e.g., "原图", "微调"
  text: string;        // Description
  img: string;         // Image URL
  prompt: string;      // AI prompt
  selected: boolean;
}

interface VoiceCandidate {
  tag: string;
  text: string;        // Description
  audio: string;       // Audio URL
  selected: boolean;
}
```

### 3. Scene (场景)
```typescript
interface Scene {
  name: string;
  candidates: VisualCandidate[];
}
```

### 4. Storyboard Shot (分镜)
```typescript
interface StoryboardShot {
  name: string;        // e.g., "分镜 1 · 田园初现"
  candidates: TextCandidate[];
}

interface TextCandidate {
  tag: string;
  text: string;        // Multi-line text with 【画面】【构图】【运镜】【旁白】
  selected: boolean;
}
```

### 5. Conversation (对话)
```typescript
interface Conversation {
  id: string;
  displayIndex: number;
  userPrompt: string;
  todoList: TodoItem[];
  status: 'loading' | 'done';
  assetPackageId: string;
  sysText: string;
}

interface TodoItem {
  title: string;       // e.g., "分析需求", "生成脚本"
  status: 'pending' | 'loading' | 'done';
}
```

### 6. Space/Journey (我的空间)
```typescript
interface Journey {
  id: string;
  title: string;
  lastPkgId: string;
  status: 'progress' | 'exported';
  updatedAt: number;
}
```

### 7. Assets Library (资产库)
```typescript
interface AssetItem {
  id: string;
  name: string;
  tags: string[];
  created: string;
  updated: string;
  usage: number;
  preview: string;     // HTML string with img/audio
  desc: string;
}

// Categories: roles, styles, scenes, voices, templates
```

---

## Page Flows

### Login → Landing
1. User enters phone + code (or team invite code)
2. On success: `sessionStorage.authenticated = true`
3. Redirect to `landing.html`

### Landing → Materials
1. User enters prompt in sticky input
2. Click submit → shows todo progress
3. On complete → generates AssetPackage
4. Auto-redirect to `materials.html`

### Materials (3-Column Layout)
- **Left**: Chat conversation history, new prompt input
- **Center**: Asset package display (summary, style, roles, scenes, storyboard)
- **Right**: Edit panel (current object, modification input, regenerate button)
- Flow: Click center item → shows in right → enter modification → regenerate → new candidate added

### Materials → Editor
1. Click "进入剪辑页面" button
2. Passes `currentAssetPackageId` via localStorage
3. Loads shots with images/videos

### Editor (Multi-Panel)
- **Top**: Sub-nav (画面/配音/音乐), project name, actions (return, generate, export)
- **Left**: Edit panel (visual cards for current shot, voice controls, music controls)
- **Center**: Canvas with video preview + thumbnail stack
- **Bottom**: Timeline with shot clips + audio tracks
- Tabs: visual (画面), voice (配音), music (音乐)

### Assets (Asset Library)
- Category tabs: 角色库, 风格库, 场景库, 音色库, 模板库
- Search + filter toolbar
- Grid of asset cards with preview
- Batch operations (delete, archive) - not for roles

### Space (User Space)
- Header: user type badge, space selector
- Two sections: In Progress (drafts), Done (exported)
- Journey cards link back to materials
- Team space support with multiple spaces

---

## Color System (CSS Variables)
```css
--bg: #05070f;
--panel: #0c101a;
--panel-2: #0f1626;
--muted: #7a88b8;
--border: rgba(255, 255, 255, 0.08);
--accent: #6cf9e0;
--accent-2: #7c5dff;
--accent-3: #f97316;
```

---

## Key Interactions to Preserve

1. **Sticky input on landing** - shrinks when scrolling
2. **Expandable input** - minimal → expanded on focus
3. **Resizable panels** - drag handles in Materials page
4. **Timeline navigation** - click clip to switch shot
5. **Asset selection** - click card to select, visual feedback
6. **Todo progress** - animated status changes
7. **Profile popover** - click avatar to toggle
8. **Mode toggle** - general/pro switch in landing input

---

## API Integration Points

| Feature | Current Mock | API Endpoint (TODO) |
|---------|-------------|---------------------|
| Login/Auth | Hardcoded credentials | POST /auth/login |
| Create Package | `seedFromAssets2()` | POST /packages |
| Get Packages | `assetPackages` object | GET /packages |
| Regenerate Asset | `finetunePools` | POST /packages/{id}/regenerate |
| List Assets | `assetsData` | GET /assets |
| Save Package | localStorage clone | POST /packages/{id}/archive |
| Get Journeys | localStorage | GET /journeys |
| Video Gen | `addVideoCard()` | POST /shots/{id}/video |

---

## Migration Priority

1. **Phase 1**: Layout & Navigation
   - AppShell component
   - GlassNav + GlassSide
   - Route structure

2. **Phase 2**: Core Pages
   - Login
   - Landing
   - Materials (main workflow)

3. **Phase 3**: Editor & Assets
   - Editor page
   - Assets library

4. **Phase 4**: Polish
   - Space page
   - Profile popover
   - Animations & transitions
