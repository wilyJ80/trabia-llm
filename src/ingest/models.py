from pydantic import BaseModel

class CPMIDocPage(BaseModel):
    content: str
    page: int
