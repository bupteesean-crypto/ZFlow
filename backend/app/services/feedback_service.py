from __future__ import annotations

import logging
from typing import Any

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class FeedbackService:
    """Routes feedback handling by target type.

    Phase 2 only implements image prompt rewriting. Text-based feedback remains a TODO because
    it should create new text candidates without mutating blueprint fields and does not reuse
    the image regeneration flow.
    """

    def __init__(self) -> None:
        self._llm = LLMService()

    def rewrite_prompt(
        self,
        target_type: str,
        original_value: Any,
        feedback: str,
        prompt_parts: dict[str, Any] | None = None,
    ) -> Any:
        target = (target_type or "").strip().lower()
        if target == "image":
            return self._rewrite_image_prompt(str(original_value or ""), feedback, prompt_parts)
        if target == "art_style":
            return self._rewrite_art_style(original_value, feedback)
        if target == "storyboard_description":
            return self._rewrite_storyboard_description(str(original_value or ""), feedback)

        # TODO: general text feedback should produce candidate text blobs stored alongside materials.
        raise NotImplementedError(f"Feedback target '{target_type}' is not implemented")

    def _rewrite_image_prompt(
        self,
        original_prompt: str,
        feedback: str,
        prompt_parts: dict[str, Any] | None,
    ) -> str:
        rewritten = self._llm.rewrite_prompt(original_prompt, feedback, prompt_parts)
        if not rewritten.strip():
            logger.warning("Rewrite returned empty prompt; falling back to original prompt.")
            return (original_prompt or "").strip()
        return rewritten.strip()

    def _rewrite_art_style(self, current_style: Any, feedback: str) -> dict:
        if not isinstance(current_style, dict):
            current_style = {}
        rewritten = self._llm.rewrite_art_style(current_style, feedback)
        return rewritten

    def _rewrite_storyboard_description(self, current_description: str, feedback: str) -> str:
        rewritten = self._llm.rewrite_storyboard_description(current_description, feedback)
        return rewritten.strip()
