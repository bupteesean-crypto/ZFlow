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
- Added SQLAlchemy DB layer with Project and MaterialPackage models, session setup, and repositories.
- Added a manual DB init path in `scripts/init_db.py`.
- Replaced in-memory Project/MaterialPackage storage with SQLAlchemy-backed repositories.
- Generation mock now writes MaterialPackage status updates to the database.
- Updated `DATABASE_URL` example to use the psycopg2 driver scheme.
- Unignored `.env.example` in `.gitignore` so the example config can be tracked.
- Documented pg_schema_simple simplifications for the v1 DB layer (kept API-facing fields like `package_name`/`parent_id`, omitted `version` and `started_at`/`completed_at`, tags stored as JSON).
- Mapped the Project `metadata` column to a `metadata_json` attribute to avoid SQLAlchemy name collisions.
- Confirmed Project/MaterialPackage storage is DB-backed only; in-memory store now covers auth sessions and generation tasks.
- Attempted local Postgres-backed verification; initdb failed due to shared memory restrictions in the execution sandbox.
- Marked v1 implementation complete; runtime verification is blocked by the sandbox environment.
- Added minimal SQLAlchemy error handling to v1 API endpoints to avoid leaking session failures.
- Fixed missing frontend component import for materials and tightened space page typing to avoid runtime/TS errors.
- Completed a static end-to-end flow review to confirm the login → space → materials → generation path is wired.
- Enabled local dev CORS for http://localhost:5173 to unblock frontend auth/login.
- Persisted login state to sessionStorage (session_token, authenticated, user) and aligned route guard checks.
- Enforced MaterialPackage project linkage, single-active-per-project behavior, and safe project deletes in repositories.
- Added defensive validation for project/material package updates and generation start inputs.
- MaterialPackage updates now auto-stamp generated_at when status becomes completed.
- Added in-memory domain event logging with trace IDs for generation lifecycle and project/material package changes.
- Replaced init_db print statements with structured logging for consistent backend logs.
- Performed a static end-to-end integration review; runtime browser verification remains blocked in this environment.
- Integrated GLM-4.7 LLM provider support with a direct HTTP call and mock fallback in the LLM service.
- Generation start now writes LLM output into MaterialPackage storyline content/summary when provider=glm.
- GLM-4.7 is now the first real LLM provider integrated into ZFlow.
- Investigated POST `/api/v1/projects` 500s tied to `user_id` persistence and moved to schema alignment (removed `user_id` from ORM writes).
- Project creation failures now log full SQLAlchemy tracebacks to aid diagnosis.
- Fixed POST `/api/v1/projects` 500s caused by ORM/schema mismatch (projects table has no `user_id`); removed `user_id` from the Project model and repository writes while keeping the API response field as null.
- `/api/v1/generation/start` now accepts prompt input, calls the LLM, and stores the generated text in material package storyline fields while marking the package completed.
- Frontend generation calls now pass the user prompt so LLM output can render in materials.
- Added a structured LLM prompt contract (summary/storyline/keywords) with safe JSON parsing and fallback to plain text.
- Stored structured LLM output inside material package materials metadata while keeping storyline fields for backward compatibility.
- Moved the LLM system prompt into a reusable prompt asset and added metadata placeholders for future image/video plans.
- Added a sequential text → image pipeline: derive image_plan from LLM output, call Seedream, and persist image metadata under materials.metadata.images.
- Updated Seedream integration to use the confirmed API contract (doubao-seedream-4.0, size=2K, configurable API base/model).
- Added Seedream multi-image storyboard generation with scene/character references plus optional previous frame continuity.
- Added a storyboard image regeneration flow and a force-regenerate entrypoint from the editor UI.
- Added Vidu image-to-video generation for storyboard shots and persisted video task metadata in materials.
- Added Vidu async-result polling in the editor UI and a backend task lookup endpoint to refresh task status and URLs.
- Editor canvas now plays video clips when available; timeline badges reflect video processing/ready/failed state.
- Added GitHub raw → jsDelivr CDN URL conversion for image references to improve model fetch reliability.
- Extracted image quality constraints into prompt files under `worker/prompts/image/constraints` and load them in generation endpoints.
- Split material package generation into base output + per-section refine prompts with a review pass and retry loop (fallbacks to base on review failure).
- Added prompt files for summary/art_style/subjects/scenes/storyboard refinement and for package review.
- Blueprint now preserves LLM-provided `image_prompt` fields for scenes, subjects, and storyboard shots.
- Added a local `prompt-lab/index.html` tool for prompt tuning against GLM/Seedream/Vidu with localStorage-based keys.

## Current Capabilities

- Mock login via phone/code returning tokens and user/session payloads.
- Project CRUD with pagination backed by PostgreSQL persistence.
- Material package list/detail/update endpoints.
- Generation start/progress/retry/skip with simulated status updates.
- v0 API scope is limited to auth, projects, material-packages, and generation (mock) under `/api/v1`.
- Interface examples exist for the implemented v0 endpoints.
- Login page calls `/api/v1/auth/login` and stores tokens in sessionStorage.
- Space page lists projects from `/api/v1/projects` and navigates to materials.
- Materials page loads project info and material packages from `/api/v1` and can trigger mock generation.
- Collaboration rules explicitly require reading `docs/temp/interface_merge.md`.
- SQLAlchemy models exist for Project and MaterialPackage and are wired into the API.
- `/api/v1/projects` and `/api/v1/material-packages` now persist to PostgreSQL via SQLAlchemy.
- Mock generation creates MaterialPackage rows and updates their status to completed.
- Project/MaterialPackage persistence follows a simplified pg_schema_simple mapping for v1.
- Project `metadata` is stored in a JSON column and exposed via the `metadata` response field.
- v1 deliverables: SQLAlchemy persistence for Project/MaterialPackage, manual DB init, and DB-backed generation updates.
- v1 endpoints return structured errors on database failures without changing response shapes.
- Materials page resolves CandidateRow components correctly; space page task mapping is type-safe.
- End-to-end demo flow is wired to `/api/v1` for login, projects, material packages, and mock generation.
- Local frontend requests from http://localhost:5173 are allowed via CORS on the backend.
- Storyboard images can be generated and regenerated via `/api/v1/material-packages/{id}/storyboard-images`.
- Storyboard videos can be generated via Vidu and queried via `/api/v1/material-packages/{id}/storyboard-videos/{task_id}`.
- Editor UI polls video tasks and updates processing/ready state for each shot.
- Image quality constraints are now read from external prompt files for easier tuning.
- Material package generation now uses base + refine steps with an LLM review loop before persisting the blueprint.
- Login state now persists across navigation via sessionStorage-backed guard checks.
- Project deletes now remove related material packages; package creation deactivates previous versions.
- /api/v1 project and material package updates now reject invalid status/progress/shape values with 400s.
- MaterialPackage completion updates now normalize generated_at timestamps.
- Backend now logs structured domain events for project/material package/generation actions.
- init_db scripts now emit log lines instead of print output.
- End-to-end login → project → generation → material package flow aligns with current API responses (static review).
- GLM-4.7 can generate storyline text during generation when LLM_PROVIDER=glm.
- Generation start accepts prompt input and surfaces GLM output in material package storyline text.
- Generation stores structured summary/storyline/keywords in material package materials metadata for future expansion.
- Materials metadata now reserves empty image/video plan placeholders for future generation stages.
- Text + image generation now runs sequentially in the backend pipeline.
- Generation now includes image_plan and optional images metadata alongside storyline text.

## Known Limitations

- No persistence for v0 API data; everything resets on restart.
- Projects and material packages now persist in PostgreSQL; generation tasks and sessions still reset on restart.
- No backend auth enforcement; tokens are not validated.
- All generation/material outputs are mock placeholders.
- Provider selection and keys are only validated at call time; services are still stubs.
- Legacy task list pages rely on `/tasks`, which is not available under v0.
- API docs include only the v0 subset; other PRD endpoints remain unimplemented.
- Materials chat/regeneration UI is still client-only except for triggering new mock generation runs.
- Project detail does not have a dedicated page; `/materials` serves as the detail view.
- No additional runtime limitations introduced by the docs rule change.
- Database requires manual initialization; no migrations framework is present.
- Generation execution state remains in memory and resets on restart.
- Project/MaterialPackage schema omits pg_schema_simple fields like `version`, `started_at`, and `completed_at` for v1 simplicity.
- Project metadata is not validated beyond JSON shape.
- Local Postgres verification could not run in the sandbox (shared memory not permitted).
- Runtime verification of PostgreSQL persistence remains blocked by the sandbox environment.
- Database errors are surfaced as generic 500 responses; details are not exposed.
- Frontend runtime checks are based on static review; no browser console run yet.
- End-to-end flow has not been exercised in a live browser session yet.
- CORS is only configured for local dev origin and not for production domains.
- Login persistence has not been validated in a live browser session yet.
- MaterialPackage active-state enforcement happens on create/update only; existing data may need cleanup if inconsistent.
- Validation is limited to basic field shape checks; no deeper content validation yet.
- MaterialPackage timestamp normalization only applies on status=completed updates.
- Domain events are in-memory only and not exposed via the API.
- Generation trace IDs are logged but not returned in responses.
- End-to-end UI flow has not been exercised in a live browser session in this environment.
- GLM integration is single-turn and synchronous; failures fall back to mock output.
- GLM output only populates storyline text; other material fields remain mocked.
- User records are not used for projects; there is no persisted user lifecycle.
- Projects are not linked to users in the database schema; `user_id` is not persisted.
- Generation progress remains simulated even when LLM output is used.
- Structured LLM output parsing is best-effort; invalid JSON falls back to plain text.
- Structured metadata is stored inside materials JSON, not a dedicated column.
- Image/video plan metadata is mostly placeholder; image generation is best-effort and video remains unimplemented.
- Seedream integration is best-effort; image failures are logged and do not block text generation.
- Seedream response parsing assumes the documented response structure; unexpected shapes fall back to no image.
- Image generation is limited to a single Seedream image with minimal controls.
- Video generation depends on externally hosted, publicly accessible image URLs; signed TOS URLs may fail.
- Video task polling only runs in the editor UI; there is no backend scheduler for async results.

## Next Confirmed Steps

- Verify frontend flows against DB-backed APIs and fix any persistence-related bugs.
- Run a local DB-backed smoke test after initializing schema with `scripts/init_db.py`.
- Confirm DB-backed Project/MaterialPackage flows remain stable under generation updates.
- Confirm Project `metadata` storage works without SQLAlchemy attribute conflicts.
- Re-run the persistence verification in an environment that allows Postgres shared memory.
- Re-run the v1 API flow against a live Postgres instance to confirm DB error handling.
- Run the end-to-end demo flow in the browser to validate frontend runtime stability.
- Execute the full login → generation demo once a browser run is available.
- Re-test login flow with browser-based CORS preflight handling.
- Validate login persistence in the browser after CORS changes.
- Validate MaterialPackage active-state transitions via generation flow.
- Exercise update endpoints with invalid payloads to confirm 400 responses in practice.
- Confirm generated_at auto-stamping when material package status is set to completed.
- Decide whether to persist domain events or expose them via admin tooling (not yet).
- Run the full frontend flow in a browser and confirm logs match project/package events.
- Run a live GLM-backed generation to verify content is returned and stored in material packages.
- Validate GLM error handling against missing/invalid credentials in a runtime environment.
- Improve frontend rendering for generated images and add multi-image support.
- Run the landing → materials flow in a live browser to confirm GLM text renders after generation.
- Validate structured JSON output from GLM in a live browser flow.
- Confirm scope for a text → image pipeline (image_plan + Seedream integration) before implementation.
- Decide on a public image rehosting strategy for video generation (OSS/CDN/GitHub).
- Audit user management, persistence, and project ownership behavior.
- Improve generation quality controls (prompt tuning, validation, retries) for storyboard consistency.
