from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingest.models import CPMIDocPage

class Chunker:
    def chunk(self, pages: list[CPMIDocPage]) -> list[CPMIDocPage]:
        splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks: list[CPMIDocPage] = []
        for page in pages:
            splits: list[str] = splitter.split_text(page.content)
            paged_chunks = [
                CPMIDocPage(
                    content=split,
                    page=page.page
                )
                for split in splits
            ]
            chunks.extend(paged_chunks)

        return chunks
