"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── PostgreSQL ────────────────────────────────────────────────
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    PG_HOST: str = Field(default="localhost")
    PG_PORT: str = Field(default="5432")

    # ── RAG ───────────────────────────────────────────────────────
    K: int = Field(default=5, ge=1, le=50, description="Número de chunks recuperados")

    # ── LLM (OpenAI-compatível) ───────────────────────────────────
    # Aponte para qualquer endpoint compatível com OpenAI:
    #   Ollama local → http://ollama:11434/v1
    #   OpenAI       → https://api.openai.com/v1
    #   Groq         → https://api.groq.com/openai/v1
    #   Together AI  → https://api.together.xyz/v1
    LLM_BASE_URL: str = Field(
        default="http://ollama:11434/v1",
        description="Base URL do endpoint compatível com OpenAI para o LLM",
    )
    LLM_API_KEY: str = Field(
        default="ollama",
        description="API key (para Ollama local qualquer valor serve)",
    )
    LLM_MODEL: str = Field(
        default="phi4-mini:latest",
        description="Nome do modelo para geração de texto",
    )

    # ── Embeddings (OpenAI-compatível) ────────────────────────────
    EMBED_BASE_URL: str = Field(
        default="http://ollama:11434/v1",
        description="Base URL do endpoint compatível com OpenAI para embeddings",
    )
    EMBED_API_KEY: str = Field(
        default="ollama",
        description="API key para embeddings (para Ollama local qualquer valor serve)",
    )
    EMBED_MODEL: str = Field(
        default="nomic-embed-text:latest",
        description="Nome do modelo para embeddings",
    )

    # ── Computed URLs ─────────────────────────────────────────────
    def MIGRATION_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.POSTGRES_DB}"
        )

    def DAO_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
