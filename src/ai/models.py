from pydantic import BaseModel, Field

class AIAnswer(BaseModel):
    content: str = Field(description="Sua resposta")
    sources: str = Field(description="Todas as fontes para embasar a resposta")
