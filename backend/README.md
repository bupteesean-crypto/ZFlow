# Backend

The backend exposes the ZFlow API, validates input, persists task metadata, and serves task status to clients.

## Responsibilities

- API contracts and request validation
- Task state tracking and persistence
- Service boundaries for worker integration

## Out of scope

- Video generation logic (owned by the worker)
- Prompt authoring or tuning (stored in `worker/prompts/`)
- Frontend rendering or UI concerns

## Run locally (placeholder)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
./scripts/run_backend.sh
```

Adjust environment variables in `.env.example` as needed.
