# Prompt Assets

Prompts are versioned files used by the worker pipeline. Each prompt version lives in its own file to ensure changes are traceable and reversible.

## Versioning

- Use semantic, sequential versions (`v1.md`, `v2.md`) within each stage directory.
- Do not edit old versions once they are referenced in production.
- Add a new version when behavior, tone, or output structure changes.

## Safe tuning

- Document intent and expected changes at the top of the prompt file.
- Keep prompts deterministic and avoid embedding environment-specific details.
- Validate changes with test inputs before switching the version in code.
