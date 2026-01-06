from app.core.config import require_api_key, require_provider, settings


class LLMService:
    def __init__(self) -> None:
        self._provider = settings.llm_provider

    def generate_text(self, prompt: str) -> str:
        provider = require_provider(self._provider, {"openai", "anthropic"}, "LLM_PROVIDER")
        if provider == "openai":
            require_api_key(settings.openai_api_key, "OPENAI_API_KEY")
            raise NotImplementedError("OpenAI provider not implemented")
        if provider == "anthropic":
            require_api_key(settings.anthropic_api_key, "ANTHROPIC_API_KEY")
            raise NotImplementedError("Anthropic provider not implemented")
        raise RuntimeError("Unsupported LLM provider")
