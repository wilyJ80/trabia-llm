"""Tests for the lightweight web interface."""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.mark.no_db
def test_web_interface_is_served():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Trabia LLM" in response.text
    assert "Ingerir e extrair PDF" in response.text
    assert "/static/app.js" in response.text


@pytest.mark.no_db
def test_static_assets_are_served():
    client = TestClient(create_app())

    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "primary-action" in css_response.text
    assert "/api/query" in js_response.text
    assert "/api/ingest" in js_response.text
    assert "/api/extract" in js_response.text
    assert "chunks-openai-count" in js_response.text
    assert "chunks-spacy-count" in js_response.text
    assert "chunks_by_embedder" in js_response.text
