import os
from typing import List, Union
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CLIENT_SECRETS_FILE: str = os.getenv("CLIENT_SECRETS_FILE")
    # Separate settings for Gmail vs Google (frontend) flows
    GMAIL_REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI")
    GMAIL_SCOPES: Union[str|List[str]] = [s for s in os.getenv("GMAIL_SCOPES")]

    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")
    GOOGLE_SCOPES: Union[str|List[str]] = [s for s in os.getenv("GOOGLE_SCOPES")]
    CORS_HOSTS: List[str] = ["http://localhost:8080", "http://localhost:8000"]
    FRONT_URL: str = os.getenv("FRONT_URL")
    # MongoDB settings for storing credentials and user info
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "mail_automation")


settings = Settings()
