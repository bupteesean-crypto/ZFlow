# State of the Project

## Version

ZFlow v0.2 - in-memory task demo with UI prototype

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
