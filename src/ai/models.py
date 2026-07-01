from pydantic import BaseModel

class AIAnswer(BaseModel):
    content: str
