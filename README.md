# ZFlow

ZFlow is an AI-powered, one-stop video generation platform. This repository provides the initial, production-ready skeleton for collaboration across backend, worker pipeline, and frontend teams.

## High-level architecture

- **Backend (FastAPI)** exposes REST endpoints for task submission, status, and metadata.
- **Worker (async pipeline)** processes prompt-driven generation stages (script → visual → render).
- **Frontend (Vue)** consumes backend APIs and presents the end-user experience.

## Repo navigation

- `backend/` contains the FastAPI application and API surface.
- `worker/` hosts the async generation pipeline and prompt assets.
- `frontend/` contains the Vite + Vue 3 frontend that consumes backend APIs.
- `docs/` captures shared context, architecture, API contracts, and collaboration guidelines.
- `scripts/` includes local convenience scripts for running services.
- `tests/` houses cross-cutting tests (pipeline-focused for now).

Start in `docs/00_PROJECT_CONTEXT.md` for product intent, then `docs/01_ARCHITECTURE.md` for the system view.

## Local development

Backend (port 8000):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
./scripts/run_backend.sh
```

Frontend (port 5173):
```bash
cd frontend
npm install
npm run dev
```
