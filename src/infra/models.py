"""SQLAlchemy ORM models for the RAG application."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ChunkModel(Base):
    """ORM model for the chunk table (OpenAI / nomic-embed-text — 768d)."""

    __tablename__ = "chunk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snippet = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    page = Column(Integer, nullable=False)


class ChunkSpacyModel(Base):
    """ORM model for the chunk_spacy table (spaCy pt_core_news_lg — 300d)."""

    __tablename__ = "chunk_spacy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snippet = Column(Text, nullable=False)
    embedding = Column(Vector(300), nullable=False)
    page = Column(Integer, nullable=False)
