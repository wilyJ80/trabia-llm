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


def test_parse_extraction_with_null_confidence_defaults_to_baixa():
    """Null confidence should normalize to 'baixa', not crash validation."""
    raw = """
    {
      "document_type": "relatorio",
      "title": "Teste",
      "main_event": "Evento",
      "facts": ["Fato"],
      "sources": [{"claim": "Fato", "page": 1}],
      "confidence": null
    }
    """

    extraction = RAGService._validate_extraction(RAGService._parse_extraction(raw))

    assert extraction.validation_status == "valid"
    assert extraction.confidence == "baixa"


def test_extraction_fallbacks_do_not_turn_missing_fields_into_valid_output():
    extraction = RAGService._parse_extraction('{"facts": []}')
    document_text = """Relatório: T3 IA
Definição do Problema
O problema consiste na criação de uma aplicação RAG que consiga retornar output estruturado, com mecanismos de validação.
Base Documental
A base documental consiste no relatório da CPMI de 8 de janeiro de 2023."""

    extraction = RAGService._apply_extraction_fallbacks(document_text, extraction)
    extraction = RAGService._validate_extraction(extraction)

    assert extraction.validation_status == "invalid"
    assert set(extraction.missing_required_fields) == {
        "document_type",
        "title",
        "main_event",
        "facts",
    }
    assert set(extraction.inferred_fields) == {
        "document_type",
        "title",
        "main_event",
        "facts",
    }
    assert extraction.document_type == "relatorio"
    assert extraction.title == "Relatório: T3 IA"
    assert extraction.main_event.startswith("O problema consiste")
    assert extraction.facts


def test_long_document_excerpt_samples_start_middle_and_end():
    blocks = [f"[pagina {index}]\nConteudo marcador pagina {index}. " * 80 for index in range(1, 61)]

    excerpt = RAGService._select_document_excerpt("\n\n".join(blocks))

    assert len(excerpt) <= 24000
    assert "marcador pagina 1" in excerpt
    assert "marcador pagina 60" in excerpt
    assert any(f"marcador pagina {index}" in excerpt for index in range(25, 36))


def test_retrieval_query_samples_long_document():
    document = "A" * 4000 + "B" * 4000 + "C" * 4000

    query = RAGService._build_retrieval_query(document)

    assert len(query) == 3002
    assert "A" * 100 in query
    assert "B" * 100 in query
    assert "C" * 100 in query
