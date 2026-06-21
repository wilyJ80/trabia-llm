import spacy
from ingest.models import CPMIDocPage

class Embedder:
    def __init__(self):
        try:
            self.nlp = spacy.load('pt_core_news_lg')
        except Exception as e:
            print(f'[ERROR] Could not load embedding model. {e}')

    def embed(self, chunks: list[CPMIDocPage]) -> list[CPMIDocPage]:
        embedded_chunks: list[CPMIDocPage] = []
        for chunk in chunks:
            embeddings = self.nlp(chunk.content)
            embedded_chunks.append(
                CPMIDocPage(
                    content=chunk.content,
                    page=chunk.page,
                    embeddings=embeddings.vector.tolist()
                )
            )

        return embedded_chunks
