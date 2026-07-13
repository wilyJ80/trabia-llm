"""PDF text loader using PyMuPDF."""

import pymupdf
from pymupdf import Document
from tqdm import tqdm

from core.models import Chunk


class PDFLoader:
    """Load text content from a PDF file, one page at a time."""

    def load(self, filepath: str) -> list[Chunk]:
        """Extract text from each page of the PDF.

        Returns a list of Chunk objects (one per page, no embeddings yet).
        """
        doc: Document = pymupdf.open(filepath)
        pages: list[Chunk] = []
        for page in tqdm(doc, desc="Loading PDF pages"):
            text = page.get_text("text")
            if text.strip():  # Skip empty pages
                pages.append(Chunk(content=text, page=page.number + 1, embeddings=[]))
        return pages
