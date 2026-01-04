# API Spec (Initial)

This is a lightweight, evolving contract for the first iteration of the backend API.

## Health

`GET /health`

Response:
```json
{
  "status": "ok"
}
```

## Tasks

`POST /tasks`

Request (placeholder):
```json
{
  "prompt": "string",
  "style": "string",
  "duration_seconds": 30
}
```

Response (placeholder):
```json
{
  "task_id": "uuid",
  "status": "queued"
}
```

`GET /tasks/{task_id}`

Response (placeholder):
```json
{
  "task_id": "uuid",
  "status": "running",
  "progress": 0.4
}
```

## Notes

- Auth and rate limiting are intentionally omitted at this stage.
- Errors should be structured and consistent once the error model is defined.
