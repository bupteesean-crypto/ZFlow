# State of the Project

## Version

ZFlow v0.2 - feature-complete (mocked) in-memory task demo with UI prototype

## What works now

- FastAPI backend: `GET /health`, `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`
- In-memory task lifecycle with status progression and mock output
- Frontend task list and task detail pages with polling
- Task creation from the frontend
- Landing page prompt entry routes to materials workspace
- Login UI with client-side access gating for protected routes
- Materials, editor, assets, and space pages render with demo data

## Mocked or simulated

- Task execution uses a background delay and mock output
- Worker is not connected to task execution
- Multi-provider LLM/image/video key management is env-based; services are stubs
- Landing prompt flow uses sessionStorage only
- Login verification is client-only and does not call a backend API
- Materials/editor/assets/space data is hardcoded or stored in sessionStorage
- Export and generation actions are UI-only

## Known limitations

- Task data resets on backend restart
- No persistence, queue, or object storage
- No backend authentication or user management
- No API support for materials, assets, or editor actions
- No CORS middleware configured

## DO NOT IMPLEMENT YET

- Do not treat mock outputs as real artifacts
- Do not build workflows that assume the worker is active
- Do not add production authentication without backend support

## Roadmap (short)

1. Add persistence for tasks with basic schema validation.
2. Connect task creation to the worker via a queue.
3. Implement real pipeline execution and artifact storage.

## State Update Protocol

AI may update docs/state.md ONLY when explicitly asked.

When updating state.md, AI MUST:

1. Preserve the existing structure
2. Only modify or append to these sections:
   - "What Changed"
   - "Current Capabilities"
   - "Known Limitations"
   - "Next Confirmed Steps"

3. Use factual language only:
   - Describe what was implemented or changed
   - Do NOT infer readiness level upgrades
   - Do NOT promote future plans to current state

4. Never:
   - Change version labels unless instructed
   - Remove previously documented limitations
   - Add speculative roadmap items

## What Changed

- Added `/api/v1` auth, projects, material-packages, and generation (mock) endpoints with a unified response wrapper.
- Introduced in-memory stores for users, sessions, projects, material packages, and generation tasks.
- Provider and API key validation now happens lazily inside service calls.
- `/api/v1` is the v0 API surface; legacy `/tasks` routes are no longer mounted.
- Updated collaboration rules to reference lowercase doc paths.
- Archived the legacy uppercase state file at `docs/ARCHIVE/STATE.md`.
- Added v0 API request/response examples to `docs/temp/interface_merge.md`.
- Wired the frontend to `/api/v1` for login, project creation/listing, material packages, and generation start/progress.
- Decided to treat `/space` as the project list and `/materials` as the project detail + material package view.
- Landing page now creates a project from the first 20 characters of the prompt and starts mock generation.
- Added `docs/temp/interface_merge.md` to the mandatory context list in `docs/ai_rules.md`.

## Current Capabilities

- Mock login via phone/code returning tokens and user/session payloads.
- Project CRUD with pagination and in-memory storage.
- Material package list/detail/update endpoints.
- Generation start/progress/retry/skip with simulated status updates.
- v0 API scope is limited to auth, projects, material-packages, and generation (mock) under `/api/v1`.
- Interface examples exist for the implemented v0 endpoints.
- Login page calls `/api/v1/auth/login` and stores tokens in sessionStorage.
- Space page lists projects from `/api/v1/projects` and navigates to materials.
- Materials page loads project info and material packages from `/api/v1` and can trigger mock generation.
- Collaboration rules explicitly require reading `docs/temp/interface_merge.md`.

## Known Limitations

- No persistence for v0 API data; everything resets on restart.
- No backend auth enforcement; tokens are not validated.
- All generation/material outputs are mock placeholders.
- Provider selection and keys are only validated at call time; services are still stubs.
- Legacy task list pages rely on `/tasks`, which is not available under v0.
- API docs include only the v0 subset; other PRD endpoints remain unimplemented.
- Materials chat/regeneration UI is still client-only except for triggering new mock generation runs.
- Project detail does not have a dedicated page; `/materials` serves as the detail view.
- No additional runtime limitations introduced by the docs rule change.

## Next Confirmed Steps

- Verify the v0 login -> project -> generation -> materials flow end-to-end.
