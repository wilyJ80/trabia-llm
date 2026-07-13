"""Tests for the reproducible Project 2 evaluation metrics."""

import pytest

from run_extraction_evaluation import (
    is_schema_valid,
    required_complete,
    score_expected_values,
    status_matches,
    summarize,
)

pytestmark = pytest.mark.no_db


def test_expected_value_scoring_normalizes_accents_and_case():
    extraction = {
        "document_type": "Relatorio tecnico",
        "title": "AUDITORIA DE SEGURANCA",
        "facts": ["Foram encontradas duas contas sem autenticacao."],
    }
    expected = {
        "document_type": ["relatorio", "parecer"],
        "title": ["auditoria de seguranca"],
        "facts": ["duas contas"],
    }

    assert score_expected_values(extraction, expected) == (3, 3)


def test_schema_validation_checks_sources_and_status():
    extraction = {
        "dates": [],
        "actors": [],
        "organizations": [],
        "facts": [],
        "evidence": [],
        "categories": [],
        "sources": [{"claim": "Fato", "page": 1}],
        "validation_status": "partial",
    }

    assert is_schema_valid(extraction)
    extraction["sources"] = [{"claim": "Fato", "page": -1}]
    assert not is_schema_valid(extraction)


def test_inferred_fields_do_not_count_as_required_complete():
    extraction = {
        "document_type": "documento",
        "title": "Titulo inferido",
        "main_event": "Evento",
        "facts": ["Fato"],
        "inferred_fields": ["title"],
    }

    assert not required_complete(extraction)


def test_partial_expected_status_accepts_partial_or_invalid():
    assert status_matches("partial", "partial")
    assert status_matches("invalid", "partial")
    assert not status_matches("valid", "partial")


def test_summary_does_not_count_empty_timeout_error_as_completed():
    summary = summarize(
        [
            {"category": "limite", "error": "", "latency_seconds": 180.0},
            {
                "category": "facil",
                "error": None,
                "latency_seconds": 1.0,
                "schema_valid": True,
                "required_complete": True,
                "status_match": True,
            },
        ]
    )

    assert summary["completed"] == 1
    assert summary["average_latency_seconds"] == 1.0
