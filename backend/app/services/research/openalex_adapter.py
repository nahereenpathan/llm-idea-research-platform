import logging
import httpx
from typing import List, Dict, Any, Optional
from app.services.research.paper_provider import PaperProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def reconstruct_abstract_from_inverted_index(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstructs text from OpenAlex's abstract_inverted_index format."""
    if not inverted_index:
        return None
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join([w[1] for w in word_positions])
    except Exception as e:
        logger.debug(f"Failed to reconstruct abstract: {e}")
        return None


class OpenAlexAdapter(PaperProvider):
    """Adapter for the official OpenAlex scholarly metadata REST API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or settings.OPENALEX_MAILTO

    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        params = {
            "search": query,
            "per-page": min(limit, 25),
            "mailto": self.mailto,
        }

        filter_parts = []
        if year_from:
            filter_parts.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filter_parts.append(f"to_publication_date:{year_to}-12-31")

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        try:
            with httpx.Client(timeout=15.0) as client:
                headers = {"User-Agent": f"IdeaLens/1.0 (mailto:{self.mailto})"}
                response = client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    title = item.get("title") or "Untitled Paper"
                    authors = []
                    for auth in item.get("authorships", []):
                        author_name = auth.get("author", {}).get("display_name")
                        if author_name:
                            authors.append(author_name)

                    abstract = reconstruct_abstract_from_inverted_index(item.get("abstract_inverted_index"))
                    doi = item.get("doi")
                    source_url = doi or item.get("id") or ""
                    
                    results.append({
                        "external_id": item.get("id", ""),
                        "source": "openalex",
                        "title": title,
                        "authors": authors[:10],
                        "publication_year": item.get("publication_year"),
                        "publication_date": item.get("publication_date"),
                        "abstract": abstract or "Abstract not provided in open metadata index.",
                        "doi": doi,
                        "source_url": source_url,
                        "citation_count": item.get("cited_by_count", 0),
                        "is_open_access": item.get("open_access", {}).get("is_oa", False)
                    })
                return results

        except Exception as e:
            logger.error(f"Error querying OpenAlex API: {e}")
            return []
