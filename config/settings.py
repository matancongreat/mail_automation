import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CLIENT_SECRETS_FILE: str = os.getenv("CLIENT_SECRETS_FILE")
    REDIRECT_URI: str = os.getenv("REDIRECT_URI")
    SCOPES: str = [scope for scope in os.getenv("SCOPES").split(",")]
    CORS_HOSTS: List[str] = ["http://localhost:8080", "http://localhost:8000"]


settings = Settings()
