from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PatentProvider(ABC):
    """Abstract interface for patent metadata search providers."""

    @abstractmethod
    def search_patents(
        self,
        query: str,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Searches patent databases and returns standardized patent records:
        {
            "query": str,
            "source": str,
            "search_type": str,
            "page": int,
            "limit": int,
            "total_count": Optional[int],
            "disclaimer": str,
            "results": List[Dict[str, Any]]
        }
        """
        pass

    def is_configured(self) -> bool:
        """Indicates whether this provider has all required credentials configured."""
        return True
