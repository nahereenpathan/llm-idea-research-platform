from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class PaperProvider(ABC):
    """Abstract interface for scholarly paper metadata providers."""

    @abstractmethod
    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Searches academic papers and returns a normalized list of paper dictionaries."""
        pass
