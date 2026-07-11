from pydantic import BaseModel, Field

class Sources(BaseModel):
    claim: str = Field(description="Informação encontrada")
    page: int = Field(description="Página associada")

class AIAnswer(BaseModel):
    content: str = Field(description="Sua resposta")
    sources: list[Sources] = Field(description="Fontes da resposta encontradas")
