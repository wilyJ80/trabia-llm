from pydantic import BaseModel
from numpy import ndarray

class CPMIDocPage(BaseModel):
    content: str
    page: int | None
    embeddings: list[float]
