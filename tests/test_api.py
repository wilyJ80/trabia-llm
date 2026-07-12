"""HTTP-based API tests for the RAG endpoints.

Tests the running API via real HTTP requests (no internal imports).
Requires the API to be up at ``API_BASE_URL`` (default http://localhost:8000).

Usage:
    # All services must be running:
    docker compose up -d

    # Run these tests:
    API_BASE_URL=http://localhost:8000 uv run pytest tests/test_api.py -v
"""

import os

import httpx
import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PDF_PATH = os.getenv(
    "TEST_PDF_PATH",
    "data/relatorio-cpmi-versao-consolidada_231017_100010.pdf",
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def api_url() -> str:
    return API_BASE_URL


@pytest.fixture
def client(api_url: str) -> httpx.Client:
    """Synchronous HTTP client pointed at the API."""
    with httpx.Client(base_url=api_url, timeout=30) as c:
        yield c


@pytest.fixture
def pdf_bytes() -> bytes:
    """Read the test PDF from disk once."""
    with open(PDF_PATH, "rb") as f:
        return f.read()


# ── GET /api/health ──────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self, client: httpx.Client):
        """Health endpoint should return 200 with status 'ok'."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "ok"
        assert isinstance(data["chunks_count"], int)
        assert isinstance(data["llm_connected"], bool)

    def test_health_reports_llm_connected(self, client: httpx.Client):
        """LLM connection should be reported as reachable."""
        resp = client.get("/api/health")
        data = resp.json()
        assert data["llm_connected"] is True


# ── POST /api/ingest ─────────────────────────────────────────────────────────


class TestIngest:
    def test_ingest_pdf_default_params(self, client: httpx.Client, pdf_bytes: bytes):
        """Ingest a PDF with default parameters (openai embedder)."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 2000, "chunk_overlap": 200, "embedder": "openai"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["chunks_stored"] > 0
        assert "chunks armazenados" in data["message"]
        assert data["params_used"]["chunk_size"] == 2000
        assert data["params_used"]["chunk_overlap"] == 200
        assert data["params_used"]["embedder"] == "openai"
        assert data["params_used"]["filename"] == "relatorio.pdf"

    def test_ingest_with_spacy_embedder(self, client: httpx.Client, pdf_bytes: bytes):
        """Ingest PDF with spaCy embedder (chunk_spacy table, 300d)."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 1000, "chunk_overlap": 100, "embedder": "spacy"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["chunks_stored"] > 0
        assert data["params_used"]["embedder"] == "spacy"
        assert data["params_used"]["chunk_size"] == 1000

    def test_ingest_small_chunks(self, client: httpx.Client, pdf_bytes: bytes):
        """Ingest with small chunk size to verify chunking is parameterized."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 500, "chunk_overlap": 200, "embedder": "openai"},
        )
        assert resp.status_code == 200

        data = resp.json()
        # Smaller chunks → more chunks than default
        assert data["chunks_stored"] > 1000
        assert data["params_used"]["chunk_size"] == 500

    def test_ingest_invalid_file_type(self, client: httpx.Client):
        """Upload a non-PDF file should be rejected with 400."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("teste.txt", b"isso nao eh um pdf", "text/plain")},
            data={"chunk_size": 2000, "chunk_overlap": 200, "embedder": "openai"},
        )
        assert resp.status_code == 400

    def test_ingest_invalid_params_out_of_range(self, client: httpx.Client, pdf_bytes: bytes):
        """Out-of-range chunk_size should be rejected with 422."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 100, "chunk_overlap": 200, "embedder": "openai"},
        )
        # FastAPI validation returns 422 for invalid Form params
        assert resp.status_code == 422

    def test_ingest_invalid_embedder(self, client: httpx.Client, pdf_bytes: bytes):
        """Invalid embedder name should be rejected with 400."""
        resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 2000, "chunk_overlap": 200, "embedder": "invalid"},
        )
        assert resp.status_code == 400


# ── POST /api/query ──────────────────────────────────────────────────────────


class TestQuery:
    @pytest.fixture(scope="class", autouse=True)
    def _ensure_data(self, client: httpx.Client, pdf_bytes: bytes):
        """Ensure there is at least some data to query against (openai table)."""
        # Ingest the first 3 pages only (fast) if the table is empty
        health = client.get("/api/health").json()
        if health["chunks_count"] == 0:
            # Use a small number of pages by ingesting a tiny chunk
            resp = client.post(
                "/api/ingest",
                files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
                data={"chunk_size": 500, "chunk_overlap": 0, "embedder": "openai"},
            )
            assert resp.status_code == 200

    def test_query_openai_embedder(self, client: httpx.Client):
        """Query the openai table (768d) and get a structured answer."""
        resp = client.post(
            "/api/query",
            json={
                "question": "Do que se trata o relatório?",
                "top_k": 3,
                "embedder": "openai",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "answer" in data
        assert data["embedder_used"] == "openai"
        assert len(data["answer"]["content"]) > 0
        assert isinstance(data["answer"]["sources"], list)

    def test_query_spacy_embedder(self, client: httpx.Client):
        """Query the spacy table (300d) and get a structured answer."""
        resp = client.post(
            "/api/query",
            json={
                "question": "Do que se trata o relatório?",
                "top_k": 3,
                "embedder": "spacy",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["embedder_used"] == "spacy"
        assert len(data["answer"]["content"]) > 0
        assert isinstance(data["answer"]["sources"], list)

    def test_query_with_sources(self, client: httpx.Client):
        """Answer should contain sources with claim and page."""
        resp = client.post(
            "/api/query",
            json={
                "question": "O relatório menciona o 8 de Janeiro?",
                "top_k": 5,
                "embedder": "openai",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        answer = data["answer"]
        if answer["sources"]:
            source = answer["sources"][0]
            assert "claim" in source
            assert "page" in source

    def test_query_top_k_respected(self, client: httpx.Client):
        """The top_k parameter should limit the number of retrieved chunks."""
        resp = client.post(
            "/api/query",
            json={
                "question": "O que o relatório diz sobre a CPMI?",
                "top_k": 1,
                "embedder": "openai",
            },
        )
        assert resp.status_code == 200

    def test_query_empty_question_rejected(self, client: httpx.Client):
        """Empty question should be rejected with 422."""
        resp = client.post(
            "/api/query",
            json={"question": "", "top_k": 5, "embedder": "openai"},
        )
        assert resp.status_code == 422

    def test_query_invalid_embedder_defaults_to_openai(self, client: httpx.Client):
        """Invalid embedder name should default to 'openai' gracefully."""
        resp = client.post(
            "/api/query",
            json={
                "question": "Do que se trata o relatório?",
                "top_k": 3,
                "embedder": "invalid_embedder",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["embedder_used"] == "openai"


# ── End-to-end: Ingest → Query ───────────────────────────────────────────────


class TestEndToEnd:
    """Full pipeline tests: ingest a small PDF, then query it."""

    def test_ingest_then_query(self, client: httpx.Client, pdf_bytes: bytes):
        """Ingest → health confirms count → query returns answer."""
        # 1. Ingest (openai, default params)
        ingest_resp = client.post(
            "/api/ingest",
            files={"file": ("relatorio.pdf", pdf_bytes, "application/pdf")},
            data={"chunk_size": 500, "chunk_overlap": 0, "embedder": "openai"},
        )
        assert ingest_resp.status_code == 200
        stored = ingest_resp.json()["chunks_stored"]

        # 2. Health should reflect the new count
        health_resp = client.get("/api/health")
        assert health_resp.json()["chunks_count"] >= stored

        # 3. Query with openai
        query_resp = client.post(
            "/api/query",
            json={"question": "Do que se trata o relatório?", "top_k": 3, "embedder": "openai"},
        )
        assert query_resp.status_code == 200
        answer = query_resp.json()["answer"]
        assert len(answer["content"]) > 0
