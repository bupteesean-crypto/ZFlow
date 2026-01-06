# INTERFACE_FIELD_INVENTORY

Backend-facing field checklist extracted from frontend code.

---

## 1. Pages → Data Dependencies

### `/pages/login.html`
- **Primary entity**: `User`
- **Fields**: `phone`, `code` (verification), `invite` (team invite code)
- **Operations**: Authentication (write-only)
- **Mode toggle**: Personal vs Team login
- **Session storage**: `authenticated`, `userType`, `currentSpace`

### `/pages/landing.html`
- **Primary entity**: `User`, `Quota`
- **Fields displayed**:
  - User: `username`, `uid`, `avatar`, `membership`
  - Points: `current`, `paid`, `bonus`
  - Quota: generation count
- **Operations**: Read-only display, project creation initiation
- **Create form**: `prompt` (video idea input), `mode` (General/Pro toggle), `model` selection

### `/pages/materials.html`
- **Primary entities**: `Conversation`, `AssetPackage`, `Material`
- **Operations**: Read + Edit (full CRUD)
- **Left panel (dialogue timeline)**: `conversations[]`
- **Center panel (workspace)**: `assetPackages[]`
- **Right panel (edit)**: Current selected object for modification
- **Sub-entities**:
  - `AssetPackage.roles[]` (visuals, voices)
  - `AssetPackage.scenes[]`
  - `AssetPackage.storyboard[]`

### `/pages/editor.html`
- **Primary entities**: `Project`, `Shot`, `TimelineClip`, `AudioTrack`
- **Operations**: Read + Edit
- **Left panels**:
  - Visual: `shots[]` with image/video generation
  - Voice: `shot[].narration`, `shot[].voiceSettings`
  - Music: `shot[].music` (AI or library)
- **Center**: Canvas preview with `video`, `subtitle`
- **Bottom**: `timeline.clips[]`, `audioTracks.bgm`, `audioTracks.tts`
- **Export**: Output video path

### `/pages/assets.html`
- **Primary entity**: `Asset`
- **Operations**: Read, Search, Filter, Batch Delete/Archive
- **Categories**: `roles`, `styles`, `scenes`, `voices`, `templates`
- **Filters**: `type`, `sortBy` (recent/name/usage)
- **Search**: By name/tags/description

### `/pages/space.html`
- **Primary entities**: `User`, `Space`, `Journey`
- **Operations**: Read, Select space
- **Displayed**:
  - `userType` (personal/team)
  - `currentSpace`
  - `teamSpaces[]`
  - `journeys[]` (drafts and done projects)

---

## 2. Core Entities and Fields

### Entity: User

| Field | Usage | Notes |
|-------|-------|-------|
| `username` | display | Shown in profile popover |
| `uid` | display, routing | Copyable UID |
| `avatar` | display | Image URL, 3 local options |
| `phone` | editable | Login input |
| `membership` | display | e.g., "付费会员" |
| `points.current` | display | Current points balance |
| `points.paid` | display | Paid points |
| `points.bonus` | display | Bonus/gifted points |
| `quota` | display | Generation quota count |
| `userType` | control | "personal" or "team" |

### Entity: Session

| Field | Usage | Notes |
|-------|-------|-------|
| `authenticated` | control | Boolean, stored in sessionStorage |
| `userType` | control | "personal" / "team" |
| `currentSpace` | control | "personal-space" / team space name |

### Entity: Conversation (materials.html left panel)

| Field | Usage | Notes |
|-------|-------|-------|
| `id` | display, routing | Unique conversation ID |
| `displayIndex` | display | Round number (1, 2, ...) |
| `userPrompt` | display | User's input text |
| `sysText` | display | System response |
| `status` | display | "pending", "loading", "done", "fail" |
| `assetPackageId` | display, routing | Links to AssetPackage |
| `todoList[]` | display | Progress checklist items |
| `todoList[].title` | display | Task name |
| `todoList[].status` | display | "pending", "loading", "done" |

### Entity: AssetPackage

| Field | Usage | Notes |
|-------|-------|-------|
| `id` | display, routing | e.g., "pkg-1", "pkg-2" |
| `title` | display, editable | e.g., "京韵田园绘梦（v1）" |
| `status` | display | "pending", "loading", "done", "fail" |
| `createdAt` | display | Timestamp |
| `summary` | display, editable | Story overview text |
| `style` | display, editable | Art direction description |
| `roles[]` | display, editable | Array of Role objects |
| `scenes[]` | display, editable | Array of Scene objects |
| `storyboard[]` | display, editable | Array of Shot objects |
| `templateIndex` | internal | For demo generation |

#### Entity: Role (nested in AssetPackage)

| Field | Usage | Notes |
|-------|-------|-------|
| `name` | display | Character name |
| `visuals[]` | display, editable | Image candidate objects |
| `voices[]` | display, editable | Audio candidate objects |

#### Entity: Scene (nested in AssetPackage)

| Field | Usage | Notes |
|-------|-------|-------|
| `name` | display | Scene name |
| `candidates[]` | display, editable | Image candidate objects |

#### Entity: Shot (nested in AssetPackage.storyboard)

| Field | Usage | Notes |
|-------|-------|-------|
| `name` | display | Shot name, e.g., "分镜 1" |
| `candidates[]` | display, editable | Text candidate objects |

### Entity: Candidate (polymorphic - used for visuals, voices, shots)

| Field | Usage | Notes |
|-------|-------|-------|
| `tag` | display | e.g., "原图", "微调", "新", "当前" |
| `text` | display | Description text |
| `prompt` | editable | AI generation prompt |
| `selected` | control | Boolean, currently active |
| `img` | display | Image URL (for visual candidates) |
| `audio` | display | Audio URL (for voice candidates) |

### Entity: Asset (assets.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `id` | display, routing | Asset identifier |
| `name` | display | Asset name |
| `tags[]` | display | Classification tags |
| `created` | display | Creation date |
| `updated` | display | Last update date |
| `usage` | display | Usage count |
| `preview` | display | HTML preview (img/audio) |
| `desc` | display | Description text |

**Asset Categories**: `roles`, `styles`, `scenes`, `voices`, `templates`

### Entity: Journey (space.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `id` | routing | Journey identifier |
| `title` | display | Project title |
| `lastPkgId` | routing | Links to AssetPackage |
| `status` | display | "progress", "exported" |
| `updatedAt` | display | Timestamp |
| `desc` | display | Status description |

### Entity: TeamSpace (space.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `id` | routing | Space identifier |
| `name` | display | Space display name |
| `members` | display | Member count |
| `recent` | display | Boolean, recently used |

### Entity: Shot (editor.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `index` | display | Shot number (1-based) |
| `img` | display | Image URL (poster) |
| `videoPath` | display | Video file URL |
| `video` | display, control | Currently loaded video source |
| `videoGenerated` | control | Boolean flag |
| `title` | display | Display title |
| `prompt` | editable | Generation description |
| `narration` | editable | Voiceover text |
| `voiceSettings` | editable | { name, tags, volume, speed, emotion } |
| `music` | editable | { mode, prompt, audioSrc, volume } |

### Entity: TimelineClip (editor.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `index` | display | Clip position |
| `shotIndex` | display | Linked shot index |
| `img` | display | Thumbnail URL |
| `videoGenerated` | display | Has video flag |
| `active` | control | Currently selected |

### Entity: AudioTrack (editor.html)

| Field | Usage | Notes |
|-------|-------|-------|
| `type` | display | "bgm" or "tts" |
| `src` | display | Audio file URL |
| `volume` | editable | 0-100 range |
| `duration` | display | Time display |

---

## 3. Entity Relationships

```
User
├── Session (1:1, via sessionStorage)
├── points (1:1)
├── quota (1:1)
├── Space (many:1, user has many spaces)
│   └── Journey[] (1:many, space contains journeys)
│       └── AssetPackage (1:1, journey points to package)
└── avatar (1:1, URL reference)

Conversation
└── AssetPackage (1:1, references by assetPackageId)

AssetPackage
├── Role[] (1:many)
│   ├── visuals[] (1:many, Candidate with img)
│   └── voices[] (1:many, Candidate with audio)
├── Scene[] (1:many)
│   └── candidates[] (1:many, Candidate with img)
└── Storyboard[] (1:many, Shot)
    └── candidates[] (1:many, Candidate with text)

Project (editor context)
├── Shot[] (1:many, ordered)
│   ├── img (1:1)
│   ├── video (1:1, optional)
│   ├── narration (1:1)
│   ├── voiceSettings (1:1)
│   └── music (1:1)
├── TimelineClip[] (1:many, derived from Shot[])
└── AudioTrack[] (1:many, bgm + tts)

Asset (library)
└── Category (1:1, roles|styles|scenes|voices|templates)
```

---

## 4. Open Questions / Ambiguities

### Authentication Flow
- Frontend uses `sessionStorage` for auth state. Backend implementation should clarify:
  - Token format and storage (JWT? session key?)
  - Token refresh mechanism
  - How `userType` and `currentSpace` are persisted

### AssetPackage vs Project Naming
- Materials page calls it `AssetPackage`
- Editor/space page calls it `Project`/`Journey`
- **Clarify needed**: Are these the same entity with different names per context, or separate entities?

### ID Formats
- Frontend uses string IDs like `"pkg-1"`, `"conv-1"`, `"journey-1"`
- Backend should specify:
  - ID format (UUID? auto-increment?)
  - Ownership rules (who can edit which IDs)

### Versioning
- Frontend shows `v1`, `v2` in titles but has no explicit `version` field
- **Clarify**: Is versioning implicit (create new package) or explicit (version field on entity)?

### Candidate Selection History
- When selecting a different candidate, the old one is kept in array
- **Clarify**: Should backend store full history or just current selection?

### Media File Storage
- Frontend uses relative paths like `../assets/images/roles/role-01.png`
- **Clarify**:
  - Upload endpoint contract
  - URL format after upload (absolute? signed URLs?)
  - File size limits and allowed formats

### Audio Settings per Shot vs Global
- Editor shows voice settings per shot with "apply to linked role" toggle
- **Clarify**: How are role-level defaults merged with shot-level overrides?

### Export/Render Job
- Frontend shows "导出" button with path prompt
- **Clarify**:
  - Async job status polling?
  - Where to store job status?
  - Notification mechanism on completion?

### Team Space Permissions
- Frontend shows member count but no permission fields
- **Clarify**:
  - Space ownership
  - Member roles (owner/editor/viewer)
  - Cross-space asset sharing

### Quota/Points Deduction
- Frontend displays quota but doesn't show deduction logic
- **Clarify**:
  - What actions cost quota/points?
  - When are they deducted (generation start? completion?)
  - Refund policy on failure?

### Search/Filter Backend
- Assets page has search by name/tags/description
- **Clarify**:
  - Full-text search implementation
  - Tag filtering exact or partial match?
  - Sort by "usage" - where is usage tracked?
