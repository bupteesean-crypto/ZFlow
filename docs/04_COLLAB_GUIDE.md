# Collaboration Guide

## Development workflow

- Keep changes scoped to a component (backend, worker, or frontend).
- Add or update docs alongside code when behavior changes.
- Prefer small, reviewable pull requests.

## Prompt edits

- Update prompt files in `worker/prompts/` with versioned paths.
- Avoid overwriting existing versions; create a new version when behavior shifts.
- Record intent and expected changes in the prompt file itself.

## Testing

- Add focused unit tests for pipeline logic and API contracts.
- Keep tests deterministic; avoid external dependencies when possible.

## Code style

- Favor clarity and explicit naming.
- Keep module responsibilities narrow and well documented.
