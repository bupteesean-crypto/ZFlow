# Architecture Overview

ZFlow is a single monorepo with three primary components:

1. **Backend (FastAPI)**: Accepts requests, validates input, persists metadata, and exposes task status.
2. **Worker (async pipeline)**: Consumes tasks and executes generation stages using prompt assets.
3. **Frontend (Vue)**: User interface that depends on backend APIs.

## Data flow (conceptual)

1. Client submits a generation request to the backend.
2. Backend enqueues or registers the task for the worker.
3. Worker runs the pipeline stages and writes artifacts.
4. Backend exposes task status and asset locations to the client.

## Boundaries

- Backend owns API contracts and persistence.
- Worker owns generation logic and prompt assets.
- Frontend owns UX and presentation logic.

## Future expansion

- Replace placeholders with durable queue, object storage, and model orchestration.
- Formalize API versioning and auth once endpoints stabilize.
