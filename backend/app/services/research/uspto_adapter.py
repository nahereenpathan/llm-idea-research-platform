import re
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.services.research.patent_provider import PatentProvider
from app.services.research.exceptions import (
    ResearchProviderError,
    ProviderNotConfiguredException,
    ProviderRateLimitError,
    ProviderTimeoutError
)
from app.core.config import settings

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "Automated patent searches identify potential prior art and concept similarities based on retrieved metadata. "
    "They do NOT constitute formal legal opinions, patentability determinations, non-infringement clearance, "
    "or freedom-to-operate analyses. Consult a registered patent attorney for legal counsel."
)


def extract_concept_observations(title: str, abstract: Optional[str], query: str) -> str:
    """
    Generates concept observation notes based STRICTLY on retrieved textual evidence.
    Does NOT assert legal validity, patentability, or freedom to operate.
    """
    query_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 3]
    text_corpus = f"{title} {abstract or ''}".lower()

    matched_terms = [t for t in query_terms if t in text_corpus]
    if matched_terms:
        unique_matches = list(dict.fromkeys(matched_terms))[:4]
        return f"Concept overlap observed on retrieved keywords: {', '.join(unique_matches)}. Relevant technical domain matches query context."
    return f"Retrieved metadata matches search query '{query}' in official patent indexing."


class USPTOAdapter(PatentProvider):
    """
    Adapter for official USPTO Open Data Portal (ODP) REST API.
    Requires USPTO_API_KEY configured in environment variables.
    """

    BASE_URL = "https://api.uspto.gov/api/v1/patent/applications/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.USPTO_API_KEY or "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_patents(
        self,
        query: str,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ProviderNotConfiguredException(
                "USPTO Open Data Portal is not configured. Please set USPTO_API_KEY in backend/.env to query live USPTO patents.",
                provider="uspto"
            )

        sanitized_page = max(1, page)
        sanitized_limit = min(max(1, limit), 25)
        start_offset = (sanitized_page - 1) * sanitized_limit

        clean_query = query.strip()
        params: Dict[str, Any] = {
            "q": clean_query,
            "rows": sanitized_limit,
            "start": start_offset
        }

        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "User-Agent": "IdeaLens/1.0"
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.BASE_URL, params=params, headers=headers)

                if response.status_code in (401, 403):
                    raise ResearchProviderError(
                        "USPTO API rejected authorization. Please verify your USPTO_API_KEY.",
                        provider="uspto",
                        status_code=401
                    )
                if response.status_code == 429:
                    raise ProviderRateLimitError(
                        "USPTO Open Data Portal rate limit reached. Please wait before retrying.",
                        provider="uspto"
                    )

                response.raise_for_status()
                data = response.json()

                total_count = data.get("total") or data.get("numFound")
                raw_records = (
                    data.get("patentApplicationBibliographicDataBag")
                    or data.get("results")
                    or data.get("patents")
                    or []
                )

                patents: List[Dict[str, Any]] = []
                for item in raw_records:
                    # Parse standard USPTO fields
                    app_num = str(item.get("applicationNumberText") or item.get("patent_number") or item.get("id") or "").strip()
                    title = item.get("inventionTitle") or item.get("patent_title") or "Patent Document"
                    
                    # Extract inventors
                    inventors = []
                    party_bag = item.get("partyBag", {})
                    if "applicantBag" in party_bag:
                        for app in party_bag.get("applicantBag", []):
                            name = app.get("contactNameText")
                            if name:
                                inventors.append(name)
                    elif "inventor_last_name" in item:
                        last = item.get("inventor_last_name", "")
                        first = item.get("inventor_first_name", "")
                        inventors.append(f"{first} {last}".strip())
                    elif isinstance(item.get("inventors"), list):
                        inventors = [str(inv) for inv in item.get("inventors")]

                    pub_date = item.get("publicationDate") or item.get("patent_date")
                    filing_date = item.get("filingDate") or item.get("filing_date") or pub_date
                    abstract_raw = item.get("abstractText") or item.get("patent_abstract")
                    abstract = abstract_raw.strip() if abstract_raw else "Abstract not returned in USPTO summary record."

                    status_str = item.get("applicationStatusDescriptionText") or item.get("status") or "Published"

                    clean_id = re.sub(r"[^\w]", "", app_num)
                    google_link = f"https://patents.google.com/patent/US{clean_id}" if clean_id else "https://patents.google.com"

                    concept_obs = extract_concept_observations(title, abstract, clean_query)

                    patents.append({
                        "patent_number": f"US{clean_id}" if not clean_id.startswith("US") else clean_id,
                        "title": title,
                        "inventors": inventors[:10] if inventors else ["USPTO Record Assignee"],
                        "publication_date": pub_date,
                        "filing_date": filing_date,
                        "abstract": abstract,
                        "status": status_str,
                        "source": "uspto",
                        "source_url": google_link,
                        "similarity_notes": concept_obs
                    })

                return {
                    "query": query,
                    "source": "uspto",
                    "search_type": search_type,
                    "page": sanitized_page,
                    "limit": sanitized_limit,
                    "total_count": total_count,
                    "disclaimer": DISCLAIMER_TEXT,
                    "results": patents
                }

        except httpx.TimeoutException:
            logger.error("USPTO API request timed out.")
            raise ProviderTimeoutError("USPTO Open Data Portal timed out after 15 seconds.", provider="uspto")
        except (ProviderNotConfiguredException, ProviderRateLimitError, ProviderTimeoutError, ResearchProviderError):
            raise
        except Exception as e:
            logger.error(f"Error querying USPTO API: {e}")
            raise ResearchProviderError(f"USPTO query error: {str(e)}", provider="uspto")
