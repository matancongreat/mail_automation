import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CLIENT_SECRETS_FILE: str = os.getenv("CLIENT_SECRETS_FILE")
    # Separate settings for Gmail vs Google (frontend) flows
    GMAIL_REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI") or REDIRECT_URI
    GMAIL_SCOPES: List[str] = [s for s in (os.getenv("GMAIL_SCOPES") or ",".join(SCOPES)).split(",")]

    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI") or REDIRECT_URI
    GOOGLE_SCOPES: List[str] = [s for s in (os.getenv("GOOGLE_SCOPES") or ",".join(SCOPES)).split(",")]
    CORS_HOSTS: List[str] = ["http://localhost:8080", "http://localhost:8000"]


settings = Settings()
