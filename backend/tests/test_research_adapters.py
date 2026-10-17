import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.research.openalex_adapter import reconstruct_abstract_from_inverted_index, OpenAlexAdapter
from app.services.research.crossref_adapter import CrossrefAdapter, clean_xml_abstract
from app.services.research.ieee_adapter import IEEEAdapter
from app.services.research.uspto_adapter import USPTOAdapter, DISCLAIMER_TEXT
from app.services.research.epo_adapter import EPOAdapter
from app.services.research.exceptions import (
    ProviderNotConfiguredException,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ResearchProviderError
)


# ============================================================================
# Unit Tests for Helper Functions
# ============================================================================

def test_inverted_index_abstract_reconstruction():
    mock_inverted = {
        "Deep": [0],
        "learning": [1],
        "accelerates": [2],
        "scientific": [3],
        "discovery": [4]
    }
    abstract = reconstruct_abstract_from_inverted_index(mock_inverted)
    assert abstract == "Deep learning accelerates scientific discovery"


def test_inverted_index_none_or_empty():
    assert reconstruct_abstract_from_inverted_index(None) is None
    assert reconstruct_abstract_from_inverted_index({}) is None
    assert reconstruct_abstract_from_inverted_index("invalid") is None


def test_clean_xml_abstract():
    raw_jats = "<jats:title>Abstract</jats:title><jats:p>This study <jats:bold>demonstrates</jats:bold> transformer scalability.</jats:p>"
    cleaned = clean_xml_abstract(raw_jats)
    assert cleaned == "Abstract This study demonstrates transformer scalability."
    assert clean_xml_abstract(None) is None
    assert clean_xml_abstract("") is None


# ============================================================================
# OpenAlexAdapter Unit & Mocked Tests
# ============================================================================

def test_openalex_adapter_search_success():
    adapter = OpenAlexAdapter(mailto="test@idealens.ai")
    assert adapter.is_configured() is True

    mock_response = {
        "meta": {"count": 42},
        "results": [
            {
                "id": "https://openalex.org/W2741809807",
                "doi": "https://doi.org/10.48550/arxiv.1706.03762",
                "title": "Attention Is All You Need",
                "publication_year": 2017,
                "publication_date": "2017-06-12",
                "cited_by_count": 85000,
                "open_access": {"is_oa": True},
                "authorships": [
                    {"author": {"display_name": "Ashish Vaswani"}},
                    {"author": {"display_name": "Noam Shazeer"}}
                ],
                "abstract_inverted_index": {
                    "The": [0], "dominant": [1], "sequence": [2], "transduction": [3], "models": [4]
                },
                "primary_location": {
                    "source": {"display_name": "Advances in Neural Information Processing Systems"},
                    "pdf_url": "https://arxiv.org/pdf/1706.03762"
                }
            }
        ]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_papers(query="attention is all you need", page=2, limit=5, search_type="title")

        assert data["page"] == 2
        assert data["limit"] == 5
        assert data["total_count"] == 42
        assert len(data["results"]) == 1

        paper = data["results"][0]
        assert paper["title"] == "Attention Is All You Need"
        assert paper["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
        assert paper["has_abstract"] is True
        assert paper["abstract"] == "The dominant sequence transduction models"
        assert paper["is_open_access"] is True
        assert paper["venue"] == "Advances in Neural Information Processing Systems"


def test_openalex_adapter_missing_abstract():
    adapter = OpenAlexAdapter()
    mock_response = {
        "meta": {"count": 1},
        "results": [
            {
                "id": "https://openalex.org/W9999",
                "title": "Paper Without Abstract",
                "publication_year": 2020,
                "authorships": [],
                "abstract_inverted_index": None
            }
        ]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_papers(query="no abstract")
        assert len(data["results"]) == 1
        assert data["results"][0]["has_abstract"] is False
        assert "Abstract not provided" in data["results"][0]["abstract"]


def test_openalex_rate_limit_and_timeout():
    adapter = OpenAlexAdapter()

    # Rate limit (429)
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp
        with pytest.raises(ProviderRateLimitError):
            adapter.search_papers("test")

    # Timeout
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(ProviderTimeoutError):
            adapter.search_papers("test")


# ============================================================================
# CrossrefAdapter Unit & Mocked Tests
# ============================================================================

def test_crossref_adapter_search_success():
    adapter = CrossrefAdapter(mailto="test@idealens.ai")
    assert adapter.is_configured() is True

    mock_response = {
        "message": {
            "total-results": 120,
            "items": [
                {
                    "DOI": "10.1145/3318464.3389700",
                    "title": ["Scalable Deep Learning for Autonomous Agents"],
                    "author": [
                        {"given": "Jane", "family": "Doe"},
                        {"name": "Anonymous Consortium"}
                    ],
                    "published-online": {"date-parts": [[2021, 5, 20]]},
                    "abstract": "<jats:p>Autonomous agent architecture overview.</jats:p>",
                    "is-referenced-by-count": 45,
                    "container-title": ["ACM Transactions on Computing Systems"]
                }
            ]
        }
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_papers(query="autonomous agents", page=1, limit=10, search_type="keyword")
        assert data["total_count"] == 120
        assert len(data["results"]) == 1

        paper = data["results"][0]
        assert paper["title"] == "Scalable Deep Learning for Autonomous Agents"
        assert paper["authors"] == ["Jane Doe", "Anonymous Consortium"]
        assert paper["publication_year"] == 2021
        assert paper["abstract"] == "Autonomous agent architecture overview."
        assert paper["has_abstract"] is True
        assert paper["doi"] == "10.1145/3318464.3389700"


def test_crossref_adapter_doi_direct_lookup():
    adapter = CrossrefAdapter()
    mock_response = {
        "message": {
            "DOI": "10.1000/182",
            "title": ["Handbook of Modern Computing"],
            "author": [{"given": "Alan", "family": "Turing"}],
            "published-print": {"date-parts": [[1950]]}
        }
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_papers(query="10.1000/182", search_type="doi")
        assert data["total_count"] == 1
        assert data["results"][0]["title"] == "Handbook of Modern Computing"
        assert data["results"][0]["authors"] == ["Alan Turing"]


# ============================================================================
# IEEEAdapter Unit & Mocked Tests
# ============================================================================

def test_ieee_adapter_unconfigured():
    adapter = IEEEAdapter(api_key="")
    assert adapter.is_configured() is False
    with pytest.raises(ProviderNotConfiguredException):
        adapter.search_papers("distributed consensus")


def test_ieee_adapter_configured_search():
    adapter = IEEEAdapter(api_key="valid_ieee_test_key")
    assert adapter.is_configured() is True

    mock_response = {
        "total_records": 15,
        "articles": [
            {
                "article_number": "9876543",
                "title": "Quantum Error Mitigation Algorithms",
                "authors": {"authors": [{"full_name": "Alice Smith"}, {"full_name": "Bob Jones"}]},
                "publication_year": "2023",
                "abstract": "We present robust quantum error mitigation techniques.",
                "doi": "10.1109/TQE.2023.12345",
                "html_url": "https://ieeexplore.ieee.org/document/9876543",
                "publication_title": "IEEE Transactions on Quantum Engineering",
                "citing_paper_count": 12,
                "access_type": "OPEN_ACCESS"
            }
        ]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_papers(query="quantum error", page=1, limit=5)
        assert data["total_count"] == 15
        assert len(data["results"]) == 1
        res = data["results"][0]
        assert res["title"] == "Quantum Error Mitigation Algorithms"
        assert res["authors"] == ["Alice Smith", "Bob Jones"]
        assert res["publication_year"] == 2023
        assert res["is_open_access"] is True


def test_ieee_adapter_auth_failure():
    adapter = IEEEAdapter(api_key="bad_key")
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp
        with pytest.raises(ResearchProviderError) as exc_info:
            adapter.search_papers("test")
        assert exc_info.value.status_code == 401


# ============================================================================
# Patent Adapters: USPTO & EPO Unit & Mocked Tests
# ============================================================================

def test_uspto_adapter_unconfigured():
    adapter = USPTOAdapter(api_key="")
    assert adapter.is_configured() is False
    with pytest.raises(ProviderNotConfiguredException):
        adapter.search_patents("machine learning")


def test_uspto_adapter_configured_search():
    adapter = USPTOAdapter(api_key="valid_uspto_key")
    assert adapter.is_configured() is True

    mock_response = {
        "total": 5,
        "patentApplicationBibliographicDataBag": [
            {
                "applicationNumberText": "16123456",
                "inventionTitle": "Autonomous Robotic Path Planning Systems",
                "publicationDate": "2021-08-15",
                "filingDate": "2018-09-10",
                "abstractText": "Methods and systems for robotic motion optimization using reinforcement learning.",
                "applicationStatusDescriptionText": "Patented Case",
                "partyBag": {
                    "applicantBag": [{"contactNameText": "Cyberdyne Systems Corp."}]
                }
            }
        ]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        data = adapter.search_patents(query="robotic motion optimization", limit=5)
        assert data["total_count"] == 5
        assert "disclaimer" in data
        assert "not constitute formal legal opinions" in data["disclaimer"].lower()
        assert len(data["results"]) == 1

        pat = data["results"][0]
        assert pat["patent_number"] == "US16123456"
        assert pat["title"] == "Autonomous Robotic Path Planning Systems"
        assert pat["inventors"] == ["Cyberdyne Systems Corp."]
        assert "robotic" in pat["similarity_notes"].lower() or "concept overlap" in pat["similarity_notes"].lower()


def test_epo_adapter_unconfigured():
    adapter = EPOAdapter(consumer_key="", consumer_secret="")
    assert adapter.is_configured() is False
    with pytest.raises(ProviderNotConfiguredException):
        adapter.search_patents("neural network")


def test_epo_adapter_configured_search():
    adapter = EPOAdapter(consumer_key="my_key", consumer_secret="my_secret")
    assert adapter.is_configured() is True

    mock_token_resp = {"access_token": "mock_token_12345"}
    mock_search_resp = {
        "ops:world-patent-data": {
            "ops:biblio-search": {
                "@total-result-count": "25",
                "ops:search-result": {
                    "ops:publication-reference": [
                        {
                            "document-id": {
                                "country": {"$": "EP"},
                                "doc-number": {"$": "3124567"},
                                "kind": {"$": "A1"}
                            }
                        }
                    ]
                }
            }
        }
    }

    with patch("httpx.Client.post") as mock_post, patch("httpx.Client.get") as mock_get:
        # Token post
        t_resp = MagicMock()
        t_resp.status_code = 200
        t_resp.json.return_value = mock_token_resp
        mock_post.return_value = t_resp

        # Search get
        s_resp = MagicMock()
        s_resp.status_code = 200
        s_resp.json.return_value = mock_search_resp
        mock_get.return_value = s_resp

        data = adapter.search_patents(query="neural network", page=1, limit=5)
        assert data["total_count"] == 25
        assert len(data["results"]) == 1
        assert data["results"][0]["patent_number"] == "EP3124567A1"
        assert "espacenet.com" in data["results"][0]["source_url"]


# ============================================================================
# API Endpoints & Tenant Isolation Integration Tests
# ============================================================================

def test_paper_sources_endpoint(client, auth_headers):
    res = client.get("/api/v1/research/papers/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 3
    ids = [s["id"] for s in sources]
    assert "openalex" in ids
    assert "crossref" in ids
    assert "ieee" in ids


def test_patent_sources_endpoint(client, auth_headers):
    res = client.get("/api/v1/research/patents/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 2
    ids = [s["id"] for s in sources]
    assert "uspto" in ids
    assert "epo" in ids


def test_paper_search_endpoint_with_mock(client, auth_headers):
    mock_payload = {
        "query": "transformer",
        "source": "openalex",
        "search_type": "keyword",
        "page": 1,
        "limit": 10,
        "total_count": 100,
        "results": [
            {
                "external_id": "https://openalex.org/W1",
                "source": "openalex",
                "title": "Attention Is All You Need",
                "authors": ["Vaswani et al."],
                "publication_year": 2017,
                "publication_date": "2017-06-12",
                "abstract": "The dominant sequence transduction models.",
                "has_abstract": True,
                "doi": "https://doi.org/10.48550/arxiv.1706.03762",
                "source_url": "https://doi.org/10.48550/arxiv.1706.03762",
                "citation_count": 80000,
                "is_open_access": True
            }
        ]
    }

    with patch("app.services.research.openalex_adapter.OpenAlexAdapter.search_papers", return_value=mock_payload):
        res = client.get(
            "/api/v1/research/papers/search?query=transformer&source=openalex&page=1&limit=10",
            headers=auth_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "transformer"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Attention Is All You Need"


def test_paper_search_unconfigured_provider(client, auth_headers):
    # When IEEE is not configured, search should return 503
    with patch("app.services.research.ieee_adapter.IEEEAdapter.is_configured", return_value=False):
        res = client.get(
            "/api/v1/research/papers/search?query=antenna&source=ieee",
            headers=auth_headers
        )
        assert res.status_code == 503
        assert "not configured" in res.json()["detail"].lower()


def test_patent_search_unconfigured_provider(client, auth_headers):
    # When USPTO is not configured, search should return 503 with helpful message
    with patch("app.services.research.uspto_adapter.USPTOAdapter.is_configured", return_value=False):
        res = client.get(
            "/api/v1/research/patents/search?query=robot&source=uspto",
            headers=auth_headers
        )
        assert res.status_code == 503
        assert "uspto" in res.json()["detail"].lower()


def test_save_paper_and_duplicate_prevention(client, auth_headers):
    # Create project
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Paper Library Test"}).json()
    proj_id = proj_res["id"]

    paper_payload = {
        "external_id": "https://openalex.org/W998877",
        "source": "openalex",
        "title": "Unique Research Paper Title",
        "authors": ["Scientist One", "Scientist Two"],
        "publication_year": 2024,
        "abstract": "Detailed scientific abstract demonstrating novel experimental methodology.",
        "doi": "https://doi.org/10.1234/unique.2024",
        "source_url": "https://doi.org/10.1234/unique.2024",
        "user_notes": "First read."
    }

    # 1. First save succeeds (201 Created)
    save_res = client.post(f"/api/v1/research/projects/{proj_id}/papers/save", headers=auth_headers, json=paper_payload)
    assert save_res.status_code == 201
    paper_id = save_res.json()["id"]

    # 2. Duplicate save attempts must be rejected with 409 Conflict
    dup_res = client.post(f"/api/v1/research/projects/{proj_id}/papers/save", headers=auth_headers, json=paper_payload)
    assert dup_res.status_code == 409
    assert "already saved" in dup_res.json()["detail"].lower()

    # 3. Verify detail endpoint
    detail_res = client.get(f"/api/v1/research/papers/{paper_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Unique Research Paper Title"

    # 4. Delete paper
    del_res = client.delete(f"/api/v1/research/papers/{paper_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 5. Verify deleted from library
    library_res = client.get(f"/api/v1/research/projects/{proj_id}/papers", headers=auth_headers)
    assert len(library_res.json()) == 0


def test_save_patent_and_duplicate_prevention(client, auth_headers):
    # Create project
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Patent Library Test"}).json()
    proj_id = proj_res["id"]

    patent_payload = {
        "patent_number": "US9999999B2",
        "title": "Quantum Computing Superposition Maintenance Device",
        "inventors": ["E. Schroedinger"],
        "publication_date": "2023-01-01",
        "filing_date": "2020-05-12",
        "abstract": "Apparatus maintaining coherence in multi-qubit registers.",
        "status": "Granted",
        "source": "uspto",
        "source_url": "https://patents.google.com/patent/US9999999B2",
        "similarity_notes": "Quantum coherence prior art."
    }

    # 1. First save succeeds (201 Created)
    save_res = client.post(f"/api/v1/research/projects/{proj_id}/patents/save", headers=auth_headers, json=patent_payload)
    assert save_res.status_code == 201
    patent_id = save_res.json()["id"]

    # 2. Duplicate save must be rejected with 409 Conflict
    dup_res = client.post(f"/api/v1/research/projects/{proj_id}/patents/save", headers=auth_headers, json=patent_payload)
    assert dup_res.status_code == 409
    assert "already saved" in dup_res.json()["detail"].lower()

    # 3. Verify detail endpoint
    detail_res = client.get(f"/api/v1/research/patents/{patent_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["patent_number"] == "US9999999B2"

    # 4. Delete patent
    del_res = client.delete(f"/api/v1/research/patents/{patent_id}", headers=auth_headers)
    assert del_res.status_code == 204


def test_tenant_authorization_isolation(client, auth_headers):
    # User A creates a project and saves a paper
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "User A Project"}).json()
    proj_id = proj_res["id"]

    paper_res = client.post(
        f"/api/v1/research/projects/{proj_id}/papers/save",
        headers=auth_headers,
        json={"title": "Secret Paper", "authors": ["Author"], "source": "openalex"}
    ).json()
    paper_id = paper_res["id"]

    # Create User B
    b_res = client.post("/api/v1/auth/register", json={
        "email": "user_b_isolation@example.com",
        "password": "Password123!",
        "full_name": "User B"
    }).json()
    b_token = b_res["access_token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    # User B attempts to access User A's project papers: should be 403 Forbidden
    access_res = client.get(f"/api/v1/research/projects/{proj_id}/papers", headers=b_headers)
    assert access_res.status_code == 403

    # User B attempts to view User A's paper details: should be 403 Forbidden
    detail_res = client.get(f"/api/v1/research/papers/{paper_id}", headers=b_headers)
    assert detail_res.status_code == 403

    # User B attempts to delete User A's paper: should be 403 Forbidden
    del_res = client.delete(f"/api/v1/research/papers/{paper_id}", headers=b_headers)
    assert del_res.status_code == 403
