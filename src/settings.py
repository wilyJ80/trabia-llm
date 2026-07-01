from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)

    PG_HOST: str = Field(...)
    PG_PORT: str = Field(...)

    K: int = Field(...)

    def MIGRATION_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.POSTGRES_DB}"

    def DAO_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file='.env')
