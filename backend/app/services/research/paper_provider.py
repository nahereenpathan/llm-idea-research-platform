from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PaperProvider(ABC):
    """Abstract interface for scholarly paper metadata providers."""

    @abstractmethod
    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Searches academic papers and returns a normalized dictionary:
        {
            "query": str,
            "source": str,
            "search_type": str,
            "page": int,
            "limit": int,
            "total_count": Optional[int],
            "results": List[Dict[str, Any]]
        }
        """
        pass

    def is_configured(self) -> bool:
        """Indicates whether this provider has all required credentials configured."""
        return True
