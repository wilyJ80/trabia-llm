from pydantic import BaseModel


class CPMIDocPage(BaseModel):
    content: str
    page: int | None
    embeddings: list[float]


class CPMIDocResult(BaseModel):
    snippet: str
    page: int | None
    distance: float
