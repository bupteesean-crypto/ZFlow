# Pipeline Overview

The worker executes a prompt-driven pipeline with clear stage boundaries. Each stage reads prompt assets from `worker/prompts/` and produces structured artifacts for the next stage.

## Stages

1. **Script**: Generate the narrative or scene outline.
2. **Visual**: Translate the script into visual directives.
3. **Render**: Combine visuals, audio, and timing into a final video artifact.

## Artifacts (conceptual)

- `script.json`: scene breakdown and narration.
- `visual.json`: shot list, composition, and style cues.
- `render.mp4`: final video output.

## Design notes

- Prompts are versioned files, not hard-coded strings.
- Each stage should be independently testable.
- Pipeline state transitions should be explicit and logged.
