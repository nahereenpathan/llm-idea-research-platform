import logging
import httpx
from typing import List, Dict, Any, Optional
from app.services.research.paper_provider import PaperProvider
from app.services.research.exceptions import (
    ResearchProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def reconstruct_abstract_from_inverted_index(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstructs coherent text from OpenAlex abstract_inverted_index structure."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return None
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join([w[1] for w in word_positions]).strip()
    except Exception as e:
        logger.debug(f"Failed to reconstruct abstract from inverted index: {e}")
        return None


class OpenAlexAdapter(PaperProvider):
    """
    Adapter for the official OpenAlex scholarly metadata REST API.
    Operates without API key credentials using polite mailto headers.
    """

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or settings.OPENALEX_MAILTO

    def is_configured(self) -> bool:
        return True

    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        sanitized_page = max(1, page)
        sanitized_limit = min(max(1, limit), 50)

        params: Dict[str, Any] = {
            "per-page": sanitized_limit,
            "page": sanitized_page,
            "mailto": self.mailto,
        }

        filter_parts: List[str] = []

        clean_query = query.strip()
        if search_type == "doi" or clean_query.startswith("10.") or "doi.org" in clean_query:
            doi_val = clean_query.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            filter_parts.append(f"doi:https://doi.org/{doi_val}")
        elif search_type == "title":
            filter_parts.append(f"title.search:{clean_query}")
        elif search_type == "author":
            filter_parts.append(f"raw_author_name.search:{clean_query}")
        else:
            # Default keyword / full-text search
            params["search"] = clean_query

        if year_from:
            filter_parts.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filter_parts.append(f"to_publication_date:{year_to}-12-31")

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        headers = {
            "User-Agent": f"IdeaLens/1.0 (mailto:{self.mailto})"
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.BASE_URL, params=params, headers=headers)
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("OpenAlex API rate limit reached. Please wait a moment.", provider="openalex")
                
                response.raise_for_status()
                data = response.json()

                total_count = data.get("meta", {}).get("count")
                raw_results = data.get("results", [])

                papers: List[Dict[str, Any]] = []
                for item in raw_results:
                    title = item.get("title") or "Untitled Scholarly Work"
                    
                    authors: List[str] = []
                    for auth in item.get("authorships", []):
                        author_name = auth.get("author", {}).get("display_name")
                        if author_name:
                            authors.append(author_name)

                    reconstructed_abstract = reconstruct_abstract_from_inverted_index(item.get("abstract_inverted_index"))
                    has_abstract = reconstructed_abstract is not None
                    abstract_display = reconstructed_abstract if has_abstract else "Abstract not provided in open metadata index."

                    doi = item.get("doi")
                    external_id = item.get("id") or (doi or "")
                    source_url = doi or external_id

                    primary_loc = item.get("primary_location") or {}
                    venue = primary_loc.get("source", {}).get("display_name") if primary_loc.get("source") else None
                    pdf_url = primary_loc.get("pdf_url")

                    papers.append({
                        "external_id": external_id,
                        "source": "openalex",
                        "title": title,
                        "authors": authors[:15],
                        "publication_year": item.get("publication_year"),
                        "publication_date": item.get("publication_date"),
                        "abstract": abstract_display,
                        "has_abstract": has_abstract,
                        "doi": doi,
                        "source_url": source_url,
                        "pdf_url": pdf_url,
                        "venue": venue,
                        "citation_count": item.get("cited_by_count", 0),
                        "is_open_access": item.get("open_access", {}).get("is_oa", False)
                    })

                return {
                    "query": query,
                    "source": "openalex",
                    "search_type": search_type,
                    "page": sanitized_page,
                    "limit": sanitized_limit,
                    "total_count": total_count,
                    "results": papers
                }

        except httpx.TimeoutException:
            logger.error("OpenAlex API request timed out.")
            raise ProviderTimeoutError("Scholarly provider OpenAlex timed out after 15 seconds.", provider="openalex")
        except (ProviderRateLimitError, ProviderTimeoutError):
            raise
        except Exception as e:
            logger.error(f"Error querying OpenAlex API: {e}")
            raise ResearchProviderError(f"OpenAlex service query error: {str(e)}", provider="openalex")
