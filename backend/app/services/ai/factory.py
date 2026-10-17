import logging
from app.core.config import settings
from app.services.ai.provider_base import LLMProvider
from app.services.ai.heuristic_provider import HeuristicFallbackProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """
    Returns the configured LLM provider according to environment settings.
    If no valid API keys are configured or provider is unavailable,
    it gracefully returns the HeuristicFallbackProvider so the platform
    remains completely functional without crashing.
    """
    provider_type = settings.LLM_PROVIDER.lower()

    if (provider_type == "gemini" or provider_type == "auto") and settings.GEMINI_API_KEY:
        try:
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiProvider: {e}")

    if (provider_type == "openai" or provider_type == "auto") and settings.OPENAI_API_KEY:
        try:
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAIProvider: {e}")

    # Fallback heuristic provider
    return HeuristicFallbackProvider()
