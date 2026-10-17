import logging
import httpx
from typing import List, Dict, Any, Optional
from app.services.research.paper_provider import PaperProvider
from app.services.research.exceptions import (
    ResearchProviderError,
    ProviderNotConfiguredException,
    ProviderRateLimitError,
    ProviderTimeoutError
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class IEEEAdapter(PaperProvider):
    """
    Adapter for IEEE Xplore REST API.
    Requires IEEE_API_KEY to be configured in settings / .env.
    """

    BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.IEEE_API_KEY or "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ProviderNotConfiguredException(
                "IEEE Xplore API access is not configured. Please supply an IEEE_API_KEY in backend/.env.",
                provider="ieee"
            )

        sanitized_page = max(1, page)
        sanitized_limit = min(max(1, limit), 25)
        start_record = (sanitized_page - 1) * sanitized_limit + 1

        clean_query = query.strip()
        params: Dict[str, Any] = {
            "apikey": self.api_key,
            "max_records": sanitized_limit,
            "start_record": start_record,
            "format": "json"
        }

        if search_type == "title":
            params["article_title"] = clean_query
        elif search_type == "author":
            params["author"] = clean_query
        else:
            params["querytext"] = clean_query

        if year_from and year_to and year_from == year_to:
            params["publication_year"] = str(year_from)

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.BASE_URL, params=params)

                if response.status_code in (401, 403):
                    raise ResearchProviderError(
                        "IEEE Xplore authentication rejected. Please verify that your IEEE_API_KEY is active and valid.",
                        provider="ieee",
                        status_code=401
                    )
                if response.status_code == 429:
                    raise ProviderRateLimitError(
                        "IEEE Xplore rate limit reached. Please wait a moment before retrying.",
                        provider="ieee"
                    )

                response.raise_for_status()
                data = response.json()

                total_count = data.get("total_records")
                raw_articles = data.get("articles", [])

                papers: List[Dict[str, Any]] = []
                for art in raw_articles:
                    title = art.get("title") or "Untitled IEEE Article"

                    authors_data = art.get("authors", {}).get("authors", [])
                    authors = [a.get("full_name") for a in authors_data if a.get("full_name")]

                    abstract_raw = art.get("abstract")
                    has_abstract = bool(abstract_raw and abstract_raw.strip())
                    abstract_display = abstract_raw.strip() if has_abstract else "Abstract not provided in IEEE open metadata."

                    doi = art.get("doi")
                    html_url = art.get("html_url") or (f"https://doi.org/{doi}" if doi else "")

                    pub_year = None
                    if art.get("publication_year"):
                        try:
                            pub_year = int(art.get("publication_year"))
                        except (ValueError, TypeError):
                            pass

                    papers.append({
                        "external_id": str(art.get("article_number") or doi or ""),
                        "source": "ieee",
                        "title": title,
                        "authors": authors[:15],
                        "publication_year": pub_year,
                        "publication_date": art.get("publication_date"),
                        "abstract": abstract_display,
                        "has_abstract": has_abstract,
                        "doi": doi,
                        "source_url": html_url,
                        "venue": art.get("publication_title"),
                        "citation_count": art.get("citing_paper_count", 0),
                        "is_open_access": art.get("access_type") == "OPEN_ACCESS"
                    })

                return {
                    "query": query,
                    "source": "ieee",
                    "search_type": search_type,
                    "page": sanitized_page,
                    "limit": sanitized_limit,
                    "total_count": total_count,
                    "results": papers
                }

        except httpx.TimeoutException:
            logger.error("IEEE Xplore API timed out.")
            raise ProviderTimeoutError("IEEE Xplore request timed out after 15 seconds.", provider="ieee")
        except (ProviderNotConfiguredException, ProviderRateLimitError, ProviderTimeoutError, ResearchProviderError):
            raise
        except Exception as e:
            logger.error(f"Error querying IEEE Xplore: {e}")
            raise ResearchProviderError(f"IEEE Xplore query error: {str(e)}", provider="ieee")
