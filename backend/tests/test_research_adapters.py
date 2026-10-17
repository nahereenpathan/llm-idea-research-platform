from app.services.research.openalex_adapter import reconstruct_abstract_from_inverted_index, OpenAlexAdapter
from app.services.research.uspto_adapter import USPTOAdapter


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


def test_uspto_adapter_search():
    adapter = USPTOAdapter()
    results = adapter.search_patents("machine learning pipeline", limit=5)
    assert len(results) > 0
    first = results[0]
    assert "patent_number" in first
    assert "title" in first
    assert first["source"] == "uspto"
    assert "google.com/patent" in first["source_url"]


def test_save_paper_and_patent_flow(client, auth_headers):
    # Create project
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Library Test"}).json()
    proj_id = proj_res["id"]

    # 1. Save paper
    paper_payload = {
        "external_id": "https://openalex.org/W123456",
        "source": "openalex",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "publication_year": 2017,
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        "doi": "https://doi.org/10.48550/arXiv.1706.03762",
        "source_url": "https://doi.org/10.48550/arXiv.1706.03762",
        "user_notes": "Seminal transformer architecture paper."
    }
    p_res = client.post(f"/api/v1/research/projects/{proj_id}/papers/save", headers=auth_headers, json=paper_payload)
    assert p_res.status_code == 201
    paper_id = p_res.json()["id"]

    # 2. Save patent
    patent_payload = {
        "patent_number": "US10289965B2",
        "title": "Systems and methods for machine learning task automation",
        "inventors": ["D. Sculley"],
        "publication_date": "2019-05-14",
        "abstract": "Methods and systems for orchestrating machine learning training pipelines.",
        "status": "Granted",
        "source": "uspto",
        "source_url": "https://patents.google.com/patent/US10289965B2",
        "similarity_notes": "Relevant prior art in ML task orchestration."
    }
    pat_res = client.post(f"/api/v1/research/projects/{proj_id}/patents/save", headers=auth_headers, json=patent_payload)
    assert pat_res.status_code == 201
    patent_id = pat_res.json()["id"]

    # 3. Retrieve saved papers and patents
    papers_list = client.get(f"/api/v1/research/projects/{proj_id}/papers", headers=auth_headers).json()
    assert len(papers_list) == 1
    assert papers_list[0]["title"] == "Attention Is All You Need"

    patents_list = client.get(f"/api/v1/research/projects/{proj_id}/patents", headers=auth_headers).json()
    assert len(patents_list) == 1
    assert patents_list[0]["patent_number"] == "US10289965B2"
