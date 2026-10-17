from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PatentProvider(ABC):
    """Abstract interface for patent search providers."""

    @abstractmethod
    def search_patents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches patent databases and returns standardized patent records."""
        pass
