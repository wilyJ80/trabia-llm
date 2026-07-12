"""spaCy embedding adapter — implements EmbedderPort using a local spaCy model.

This adapter is useful for comparative experiments: ingest the same document
with a lightweight static embedding (spaCy) vs a transformer-based embedding
(OpenAI-compatible), then compare RAG quality.

If the model is not installed, it will be downloaded automatically on first use
(``spacy download``).  The Docker image pre-downloads it at build time.
"""

import subprocess
import sys

import spacy

from core.port.embedder_port import EmbedderPort


class SpacyEmbedder(EmbedderPort):
    """Text embedder that uses a local spaCy model (e.g. pt_core_news_lg).

    spaCy embeddings are static (word2vec) and produce 300-dimensional
    vectors.  They are much faster to compute than transformer embeddings
    but capture less semantic nuance.
    """

    def __init__(self, model_name: str = "pt_core_news_lg"):
        try:
            self._nlp = spacy.load(model_name)
        except OSError:
            print(f"[INFO] spaCy model '{model_name}' not found. Downloading... (541MB)")
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"Falha ao baixar modelo spaCy '{model_name}'. "
                    f"Execute manualmente: python -m spacy download {model_name}"
                ) from exc
            self._nlp = spacy.load(model_name)
        self.batch_size = 32  # spaCy processes documents in batches internally

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        doc = self._nlp(text)
        return doc.vector.tolist()  # type: ignore[union-attr]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        spaCy handles batching internally via ``nlp.pipe()``.
        """
        docs = self._nlp.pipe(texts, batch_size=self.batch_size)
        return [doc.vector.tolist() for doc in docs]

    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a query string."""
        doc = self._nlp(query)
        return doc.vector.tolist()
