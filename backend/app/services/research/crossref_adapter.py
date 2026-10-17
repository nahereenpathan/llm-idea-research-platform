import re
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


def clean_xml_abstract(text: Optional[str]) -> Optional[str]:
    """Strips XML/HTML formatting tags (e.g. JATS XML) from abstracts."""
    if not text:
        return None
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned if cleaned else None


class CrossrefAdapter(PaperProvider):
    """
    Adapter for the official Crossref scholarly REST API.
    Operates without API key credentials using polite mailto headers.
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or settings.CROSSREF_MAILTO

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
        offset = (sanitized_page - 1) * sanitized_limit

        headers = {
            "User-Agent": f"IdeaLens/1.0 (mailto:{self.mailto})"
        }

        clean_query = query.strip()

        # Check if direct DOI lookup is requested
        if search_type == "doi" or (clean_query.startswith("10.") and "/" in clean_query):
            doi_candidate = clean_query.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            return self._lookup_by_doi(doi_candidate, headers, sanitized_page, sanitized_limit)

        params: Dict[str, Any] = {
            "rows": sanitized_limit,
            "offset": offset
        }

        if search_type == "title":
            params["query.title"] = clean_query
        elif search_type == "author":
            params["query.author"] = clean_query
        else:
            params["query"] = clean_query

        filter_parts: List[str] = []
        if year_from:
            filter_parts.append(f"from-pub-date:{year_from}-01-01")
        if year_to:
            filter_parts.append(f"until-pub-date:{year_to}-12-31")

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.BASE_URL, params=params, headers=headers)
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Crossref rate limit reached. Please wait a moment.", provider="crossref")
                
                response.raise_for_status()
                data = response.json()

                message = data.get("message", {})
                total_count = message.get("total-results")
                items = message.get("items", [])

                papers = [self._normalize_item(item) for item in items]

                return {
                    "query": query,
                    "source": "crossref",
                    "search_type": search_type,
                    "page": sanitized_page,
                    "limit": sanitized_limit,
                    "total_count": total_count,
                    "results": papers
                }

        except httpx.TimeoutException:
            logger.error("Crossref API request timed out.")
            raise ProviderTimeoutError("Scholarly provider Crossref timed out after 15 seconds.", provider="crossref")
        except (ProviderRateLimitError, ProviderTimeoutError):
            raise
        except Exception as e:
            logger.error(f"Error querying Crossref API: {e}")
            raise ResearchProviderError(f"Crossref service query error: {str(e)}", provider="crossref")

    def _lookup_by_doi(self, doi: str, headers: Dict[str, str], page: int, limit: int) -> Dict[str, Any]:
        """Direct DOI lookup via Crossref REST API."""
        url = f"{self.BASE_URL}/{doi}"
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 404:
                    return {
                        "query": doi,
                        "source": "crossref",
                        "search_type": "doi",
                        "page": 1,
                        "limit": limit,
                        "total_count": 0,
                        "results": []
                    }
                res.raise_for_status()
                item = res.json().get("message", {})
                paper = self._normalize_item(item)
                return {
                    "query": doi,
                    "source": "crossref",
                    "search_type": "doi",
                    "page": 1,
                    "limit": limit,
                    "total_count": 1,
                    "results": [paper]
                }
        except Exception as e:
            logger.error(f"Error looking up DOI in Crossref: {e}")
            raise ResearchProviderError(f"Crossref DOI lookup failed: {str(e)}", provider="crossref")

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        title_list = item.get("title", [])
        title = title_list[0] if title_list else "Untitled Work"

        authors: List[str] = []
        for auth in item.get("author", []):
            given = auth.get("given", "").strip()
            family = auth.get("family", "").strip()
            name = f"{given} {family}".strip() if (given or family) else auth.get("name", "")
            if name:
                authors.append(name)

        pub_parts = (
            item.get("published-print", {}).get("date-parts", [])
            or item.get("published-online", {}).get("date-parts", [])
            or item.get("created", {}).get("date-parts", [])
        )
        pub_year = pub_parts[0][0] if (pub_parts and pub_parts[0]) else None
        pub_date_str = "-".join([str(p).zfill(2) for p in pub_parts[0]]) if (pub_parts and pub_parts[0]) else (str(pub_year) if pub_year else None)

        doi = item.get("DOI")
        source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        
        raw_abstract = item.get("abstract")
        clean_abstract = clean_xml_abstract(raw_abstract)
        has_abstract = clean_abstract is not None
        abstract_display = clean_abstract if has_abstract else "Abstract not indexed by Crossref metadata."

        container = item.get("container-title", [])
        venue = container[0] if container else None

        return {
            "external_id": doi or item.get("prefix", ""),
            "source": "crossref",
            "title": title,
            "authors": authors[:15],
            "publication_year": pub_year,
            "publication_date": pub_date_str,
            "abstract": abstract_display,
            "has_abstract": has_abstract,
            "doi": doi,
            "source_url": source_url,
            "venue": venue,
            "citation_count": item.get("is-referenced-by-count", 0),
            "is_open_access": False
        }
