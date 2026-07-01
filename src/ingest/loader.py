import pymupdf
from pymupdf import Document
from domain.cpmidoc.models import CPMIDocPage
from tqdm import tqdm

class Loader:
    def load(self, filepath: str) -> list[CPMIDocPage]:
        doc: Document = pymupdf.open(filepath)
        return [
            CPMIDocPage(
                content=page.get_text('text'),
                page=page.number,
                embeddings=[]
            )
            for page in tqdm(doc)
        ]
