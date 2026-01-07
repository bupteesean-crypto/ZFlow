import json
import logging
from pathlib import Path
from urllib import error, request

from app.core.config import normalize_provider, settings

logger = logging.getLogger(__name__)

GLM_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "llm_generation.md"
DEFAULT_SYSTEM_PROMPT = (
    "You are a creative assistant for video content and material generation. "
    "Return a JSON object only with keys: summary (string), storyline (string), "
    "keywords (array of strings). Summary: 1-2 sentences. Storyline: short paragraph. "
    "Keywords: 3-8 short tags. No Markdown, no extra text."
)


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8").strip() or DEFAULT_SYSTEM_PROMPT
    except OSError:
        logger.warning("Failed to read prompt asset at %s; using default prompt", PROMPT_PATH)
        return DEFAULT_SYSTEM_PROMPT


SYSTEM_PROMPT = _load_system_prompt()


class LLMService:
    def __init__(self) -> None:
        self._provider = settings.llm_provider

    def generate(self, prompt: str) -> dict:
        provider = normalize_provider(self._provider)
        if not provider or provider == "mock":
            return self._mock_output(prompt)
        if provider == "glm":
            return self._generate_glm(prompt)
        logger.warning("LLM provider %s not implemented; using mock output", provider)
        return self._mock_output(prompt)

    def generate_text(self, prompt: str) -> str:
        result = self.generate(prompt)
        if isinstance(result, dict):
            storyline = result.get("storyline")
            summary = result.get("summary")
            if isinstance(storyline, str) and storyline.strip():
                return storyline.strip()
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
        return "Demo content"

    def _mock_output(self, prompt: str) -> dict:
        fallback = (prompt or "").strip() or "Demo content"
        return {"summary": fallback, "storyline": fallback, "keywords": []}

    def _extract_json(self, content: str) -> str:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return ""
        return content[start : end + 1]

    def _parse_structured_output(self, content: str, fallback_text: str) -> dict:
        parsed = None
        for candidate in (content, self._extract_json(content)):
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not isinstance(parsed, dict):
            return self._mock_output(fallback_text)

        summary = parsed.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            summary = fallback_text
        storyline = parsed.get("storyline")
        if not isinstance(storyline, str) or not storyline.strip():
            storyline = summary

        keywords = parsed.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [item.strip() for item in keywords.split(",") if item.strip()]
        elif isinstance(keywords, list):
            keywords = [str(item).strip() for item in keywords if str(item).strip()]
        else:
            keywords = []

        return {"summary": summary.strip(), "storyline": storyline.strip(), "keywords": keywords}

    def _generate_glm(self, prompt: str) -> dict:
        api_key = settings.glm_api_key
        model = settings.glm_model
        if not api_key or not model:
            logger.error("GLM provider selected but GLM_API_KEY or GLM_MODEL is missing")
            return self._mock_output(prompt)

        user_input = (prompt or "").strip() or "No user input provided."
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            "temperature": 0.7,
        }

        req = request.Request(
            GLM_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                response_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            logger.error("GLM API error: status=%s reason=%s", exc.code, exc.reason)
            return self._mock_output(prompt)
        except Exception:
            logger.exception("GLM API request failed")
            return self._mock_output(prompt)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error("GLM API response was not valid JSON")
            return self._mock_output(prompt)

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        if not content:
            logger.error("GLM API response missing content")
            return self._mock_output(prompt)
        return self._parse_structured_output(content.strip(), user_input)
