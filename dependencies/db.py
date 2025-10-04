from typing import AsyncGenerator
from fastapi import Depends
from db.mongo_connector import MongoConnector
from routes.gmail.repo import GmailRepo


async def get_db():
    """Dependency that yields the MongoDB database (singleton client under the hood).

    This is primarily a DI hook for tests (app.dependency_overrides).
    """
    db = MongoConnector().get_db()
    try:
        yield db
    finally:
        # nothing to close per-request when using a shared client
        pass


def get_gmail_repo(db=Depends(get_db)) -> GmailRepo:
    """Return a GmailRepo instance bound to the provided db.

    GmailRepo currently uses the connector internally; this factory keeps the DI
    surface in place for tests or future constructor-based injection.
    """
    return GmailRepo()
