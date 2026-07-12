"""Tests for structured extraction parsing and validation."""

import pytest

from core.service import RAGService

pytestmark = pytest.mark.no_db


def test_parse_valid_extraction_json():
    raw = """
    {
      "document_type": "relatorio",
      "title": "Relatorio de teste",
      "main_event": "Evento analisado",
      "dates": ["2026-07-12"],
      "actors": ["Pessoa A"],
      "organizations": ["Orgao B"],
      "facts": ["Fato objetivo extraido"],
      "evidence": ["Trecho usado como evidencia"],
      "categories": ["administrativo"],
      "sources": [{"claim": "Fato objetivo extraido", "page": 1}],
      "confidence": "alta"
    }
    """

    extraction = RAGService._validate_extraction(RAGService._parse_extraction(raw))

    assert extraction.validation_status == "valid"
    assert extraction.missing_required_fields == []
    assert extraction.confidence == "alta"


def test_parse_invalid_extraction_marks_missing_fields():
    raw = '{"document_type": null, "title": null, "main_event": null, "facts": []}'

    extraction = RAGService._validate_extraction(RAGService._parse_extraction(raw))

    assert extraction.validation_status == "invalid"
    assert set(extraction.missing_required_fields) == {
        "document_type",
        "title",
        "main_event",
        "facts",
    }
    assert extraction.confidence == "baixa"


def test_parse_extraction_from_markdown_fenced_json():
    raw = """
    ```json
    {
      "document_type": "noticia",
      "title": "Titulo",
      "main_event": "Evento",
      "facts": ["Fato"],
      "sources": [{"claim": "Fato", "page": 0}],
      "confidence": "media"
    }
    ```
    """

    extraction = RAGService._validate_extraction(RAGService._parse_extraction(raw))

    assert extraction.validation_status == "valid"
    assert extraction.document_type == "noticia"


def test_parse_extraction_accepts_portuguese_keys_and_objects():
    raw = """
    {
      "tipo_documento": "ata",
      "titulo": "Reuniao do projeto",
      "evento_principal": {"descricao": "Validacao do cronograma"},
      "datas": [{"data": "2026-07-12"}],
      "atores": [{"nome": "Maria Silva"}],
      "organizacoes": ["Secretaria de Educacao"],
      "fatos": [{"descricao": "Cronograma validado"}],
      "fontes": [{"fato": "Cronograma validado", "pagina": "2"}],
      "confianca": "média"
    }
    """

    extraction = RAGService._validate_extraction(RAGService._parse_extraction(raw))

    assert extraction.validation_status == "valid"
    assert extraction.document_type == "ata"
    assert extraction.actors == ["Maria Silva"]
    assert extraction.facts == ["Cronograma validado"]
    assert extraction.sources[0].page == 2


def test_extraction_fallbacks_fill_obvious_required_fields():
    extraction = RAGService._parse_extraction('{"facts": []}')
    document_text = """Relatório: T3 IA
Definição do Problema
O problema consiste na criação de uma aplicação RAG que consiga retornar output estruturado, com mecanismos de validação.
Base Documental
A base documental consiste no relatório da CPMI de 8 de janeiro de 2023."""

    extraction = RAGService._apply_extraction_fallbacks(document_text, extraction)
    extraction = RAGService._validate_extraction(extraction)

    assert extraction.validation_status == "valid"
    assert extraction.document_type == "relatorio"
    assert extraction.title == "Relatório: T3 IA"
    assert extraction.main_event.startswith("O problema consiste")
    assert extraction.facts
