"""Tests for the vector repository operations using SQLAlchemy ORM."""

import pytest

from core.models import Chunk


@pytest.mark.asyncio
async def test_insert_and_count(repo):
    assert await repo.count_chunks() == 0

    chunk = Chunk(content="Teste de chunk", page=1, embeddings=[0.1] * 768)
    await repo.insert_chunk(chunk)

    assert await repo.count_chunks() == 1


@pytest.mark.asyncio
async def test_insert_chunks_in_one_batch(repo):
    chunks = [
        Chunk(content="Primeiro", page=1, embeddings=[0.1] * 768),
        Chunk(content="Segundo", page=2, embeddings=[0.2] * 768),
    ]

    inserted = await repo.insert_chunks(chunks)

    assert inserted == 2
    assert await repo.count_chunks() == 2


@pytest.mark.asyncio
async def test_search_similarity(repo):
    chunk_a = Chunk(content="CPI da COVID", page=1, embeddings=[1.0] * 768)
    chunk_b = Chunk(content="Relatório da CPMI do 8 de Janeiro", page=2, embeddings=[0.5] * 768)

    await repo.insert_chunk(chunk_a)
    await repo.insert_chunk(chunk_b)

    results = await repo.search_similar([0.5] * 768, limit=2)
    assert len(results) == 2
    assert results[0].distance <= results[1].distance


@pytest.mark.asyncio
async def test_delete_all(repo):
    await repo.insert_chunk(Chunk(content="Teste", page=1, embeddings=[0.1] * 768))
    await repo.insert_chunk(Chunk(content="Teste 2", page=2, embeddings=[0.2] * 768))

    assert await repo.count_chunks() == 2
    await repo.delete_all()
    assert await repo.count_chunks() == 0
