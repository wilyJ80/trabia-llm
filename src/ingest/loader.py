import pymupdf
from pymupdf import Document
from ingest.models import CPMIDocPage

class Loader:
    def load(self, filepath: str) -> list[CPMIDocPage]:
        doc: Document = pymupdf.open(filepath)
        return [
            CPMIDocPage(
                content=page.get_text('text'),
                page=page.number
            )
            for page in doc
        ]
