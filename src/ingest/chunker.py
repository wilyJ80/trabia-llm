from langchain_text_splitters import RecursiveCharacterTextSplitter
from domain.cpmidoc.models import CPMIDocPage
from tqdm import tqdm

class Chunker:
    def chunk(self, pages: list[CPMIDocPage]) -> list[CPMIDocPage]:
        splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks: list[CPMIDocPage] = []
        for page in tqdm(pages):
            splits: list[str] = splitter.split_text(page.content)
            paged_chunks = [
                CPMIDocPage(
                    content=split,
                    page=page.page,
                    embeddings=[]
                )
                for split in splits
            ]
            chunks.extend(paged_chunks)

        return chunks
