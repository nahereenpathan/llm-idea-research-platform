import base64
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
from app.services.research.uspto_adapter import DISCLAIMER_TEXT, extract_concept_observations
from app.core.config import settings

logger = logging.getLogger(__name__)


class EPOAdapter(PatentProvider):
    """
    Adapter for European Patent Office (EPO) Open Patent Services (OPS) API.
    Uses OAuth2 client credentials flow with EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET.
    """

    TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
    SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None
    ):
        self.consumer_key = (consumer_key or settings.EPO_CONSUMER_KEY or "").strip()
        self.consumer_secret = (consumer_secret or settings.EPO_CONSUMER_SECRET or "").strip()
        self._cached_token: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret)

    def _get_access_token(self) -> str:
        """Obtains an OAuth2 bearer token from EPO OPS token service."""
        auth_bytes = f"{self.consumer_key}:{self.consumer_secret}".encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(self.TOKEN_URL, headers=headers, data=data)
                if res.status_code in (401, 403):
                    raise ResearchProviderError(
                        "EPO OPS authentication rejected. Verify your EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET.",
                        provider="epo",
                        status_code=401
                    )
                res.raise_for_status()
                token_data = res.json()
                token = token_data.get("access_token")
                if not token:
                    raise ResearchProviderError("Failed to receive access token from EPO OPS.", provider="epo")
                self._cached_token = token
                return token
        except httpx.TimeoutException:
            raise ProviderTimeoutError("EPO OAuth token request timed out.", provider="epo")
        except Exception as e:
            logger.error(f"Error obtaining EPO OAuth token: {e}")
            raise ResearchProviderError(f"EPO authentication error: {str(e)}", provider="epo")

    def search_patents(
        self,
        query: str,
        search_type: str = "keyword",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ProviderNotConfiguredException(
                "European Patent Office (EPO OPS) access is not configured. Please supply EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET in backend/.env.",
                provider="epo"
            )

        sanitized_page = max(1, page)
        sanitized_limit = min(max(1, limit), 25)
        start_range = (sanitized_page - 1) * sanitized_limit + 1
        end_range = sanitized_page * sanitized_limit

        token = self._cached_token or self._get_access_token()

        clean_query = query.strip()
        # Formulate CQL query for EPO OPS: search title or abstract
        cql_query = f'ta="{clean_query}"' if " " in clean_query else f"ta={clean_query}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-OPS-Range": f"{start_range}-{end_range}"
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(self.SEARCH_URL, params={"q": cql_query}, headers=headers)

                if res.status_code == 401:
                    # Token may have expired, retry once with fresh token
                    token = self._get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                    res = client.get(self.SEARCH_URL, params={"q": cql_query}, headers=headers)

                if res.status_code == 429:
                    raise ProviderRateLimitError("EPO OPS fair-use threshold exceeded. Please wait a moment.", provider="epo")

                res.raise_for_status()
                data = res.json()

                ops_response = data.get("ops:world-patent-data", {})
                biblio_search = ops_response.get("ops:biblio-search", {})
                total_count = biblio_search.get("@total-result-count")
                if total_count is not None:
                    try:
                        total_count = int(total_count)
                    except ValueError:
                        pass

                search_results = biblio_search.get("ops:search-result", {}).get("ops:publication-reference", [])
                if isinstance(search_results, dict):
                    search_results = [search_results]

                patents: List[Dict[str, Any]] = []
                for ref in search_results:
                    doc_id = ref.get("document-id", {})
                    country = doc_id.get("country", {}).get("$", "EP")
                    doc_number = doc_id.get("doc-number", {}).get("$", "")
                    kind = doc_id.get("kind", {}).get("$", "")
                    full_num = f"{country}{doc_number}{kind}".strip()

                    title = f"European Patent Document {full_num}"
                    espacenet_url = f"https://worldwide.espacenet.com/patent/search/family/en/publication/{full_num}"

                    patents.append({
                        "patent_number": full_num,
                        "title": title,
                        "inventors": ["EPO Published Patent Record"],
                        "publication_date": None,
                        "filing_date": None,
                        "abstract": "Bibliographic record indexed in EPO Open Patent Services.",
                        "status": "Published",
                        "source": "epo",
                        "source_url": espacenet_url,
                        "similarity_notes": extract_concept_observations(title, None, clean_query)
                    })

                return {
                    "query": query,
                    "source": "epo",
                    "search_type": search_type,
                    "page": sanitized_page,
                    "limit": sanitized_limit,
                    "total_count": total_count,
                    "disclaimer": DISCLAIMER_TEXT,
                    "results": patents
                }

        except httpx.TimeoutException:
            logger.error("EPO OPS API timed out.")
            raise ProviderTimeoutError("EPO Open Patent Services request timed out.", provider="epo")
        except (ProviderNotConfiguredException, ProviderRateLimitError, ProviderTimeoutError, ResearchProviderError):
            raise
        except Exception as e:
            logger.error(f"Error querying EPO OPS: {e}")
            raise ResearchProviderError(f"EPO OPS query error: {str(e)}", provider="epo")
