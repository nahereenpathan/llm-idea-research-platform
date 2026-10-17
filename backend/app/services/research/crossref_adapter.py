import logging
import httpx
from typing import List, Dict, Any, Optional
from app.services.research.paper_provider import PaperProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class CrossrefAdapter(PaperProvider):
    """Adapter for the official Crossref scholarly REST API."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or settings.CROSSREF_MAILTO

    def search_papers(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "rows": min(limit, 25),
        }

        filter_parts = []
        if year_from:
            filter_parts.append(f"from-pub-date:{year_from}-01-01")
        if year_to:
            filter_parts.append(f"until-pub-date:{year_to}-12-31")

        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        headers = {
            "User-Agent": f"IdeaLens/1.0 (mailto:{self.mailto})"
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                items = data.get("message", {}).get("items", [])
                results = []
                for item in items:
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else "Untitled Work"
                    
                    authors = []
                    for auth in item.get("author", []):
                        given = auth.get("given", "")
                        family = auth.get("family", "")
                        name = f"{given} {family}".strip()
                        if name:
                            authors.append(name)

                    pub_parts = item.get("published-print", {}).get("date-parts", []) or item.get("published-online", {}).get("date-parts", [])
                    pub_year = pub_parts[0][0] if pub_parts and pub_parts[0] else None

                    doi = item.get("DOI")
                    source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
                    
                    abstract = item.get("abstract") or "Abstract not indexed by Crossref metadata."
                    # Remove XML tags from Crossref abstract if present
                    if "<" in abstract and ">" in abstract:
                        import re
                        abstract = re.sub(r"<[^>]+>", "", abstract)

                    results.append({
                        "external_id": doi or item.get("prefix", ""),
                        "source": "crossref",
                        "title": title,
                        "authors": authors[:10],
                        "publication_year": pub_year,
                        "publication_date": str(pub_year) if pub_year else None,
                        "abstract": abstract.strip(),
                        "doi": doi,
                        "source_url": source_url,
                        "citation_count": item.get("is-referenced-by-count", 0),
                        "is_open_access": False
                    })
                return results

        except Exception as e:
            logger.error(f"Error querying Crossref API: {e}")
            return []
