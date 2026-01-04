# Worker

The worker runs ZFlow's async video generation pipeline. It consumes tasks from the backend and executes prompt-driven stages that produce artifacts for the final render.

## Pipeline stages

1. **Script**: Build narrative structure and scene outline.
2. **Visual**: Translate script into shot and style directives.
3. **Render**: Assemble assets into a final video artifact.

## Prompt-driven design

Prompts live in `worker/prompts/` and are versioned files. Code should load prompts by version so experiments are traceable and safe to roll back.
