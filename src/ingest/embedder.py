from fastembed import TextEmbedding
from ingest.models import CPMIDocPage

class Embedder:
    def __init__(self):
        try:
            self.model = TextEmbedding(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f'[ERROR] Could not load embedding model. {e}')

    def embed(self, chunks: list[CPMIDocPage]) -> list[CPMIDocPage]:
        embedded_chunks: list[CPMIDocPage] = []
        for chunk in chunks:
            embeddings_generator = self.model.embed(chunk.content)
            embedding = next(iter(embeddings_generator))
            embedded_chunks.append(
                CPMIDocPage(
                    content=chunk.content,
                    page=chunk.page,
                    embeddings=embedding.tolist()
                )
            )

        return embedded_chunks
