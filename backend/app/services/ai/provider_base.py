from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates plain text response."""
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generates a structured JSON dictionary response."""
        pass
