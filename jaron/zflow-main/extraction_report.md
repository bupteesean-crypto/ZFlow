# Extraction Report

## Sources (path + line numbers)

- Base URL default and env override: `src/utils/request.js:8-15`
- Default base URL constant: `src/utils/constants.js:5-6`
- Base URL persisted in localStorage and propagated to request client: `src/hooks/useApiConfig.js:38-52`
- Auth injection (Bearer Authorization header) and no-auth endpoint list: `src/utils/request.js:18-29`
- Chat endpoint (non-stream) and streaming fetch with auth header: `src/api/chat.js:7-27`
- Image generation endpoint and requestType handling: `src/api/image.js:7-16`
- Video generation endpoint and async status endpoint: `src/api/video.js:7-23`
- Model list endpoints: `src/api/model.js:7-33`
- Chat request payload (model/messages) and default model in useChat: `src/hooks/useApi.js:64-88`
- Image request payload fields and response mapping: `src/hooks/useApi.js:137-205`
- Video request payload fields and async polling/status handling: `src/hooks/useApi.js:248-391`
- Model IDs, defaults, and option lists: `src/config/models.js:60-165`
- API endpoint defaults note for images/videos: `docs/api_config.md:96-101`
- Endpoint constants (potential mismatch for video path): `src/utils/constants.js:9-23`

## Missing / UNKNOWN

- Authoritative response schemas for `/model/fullName` and `/model/types` (shape/status codes not defined in code).
- Definitive response schema for `/chat/completions` (non-streaming path not used in hooks).
- Definitive response schema for `/images/generations` and `/videos/generations` (only partial fields inferred from client parsing).
- Provider-level error codes beyond 401/429 and generic message handling.
- Official pricing or rate limits.
- Canonical video generation endpoint is ambiguous: code uses `/videos/generations`, constants mention `/videos`.
- Canonical task status endpoint shape and terminal state contract beyond observed fields.
- Request field enum/value constraints for `content` items and model-specific parameters.
