from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.settings import settings


class SingletonMeta(type):
    """A thread-safe implementation of Singleton using a metaclass."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MongoConnector(metaclass=SingletonMeta):
    """Connector for Motor AsyncIOMotorClient implemented as a singleton.

    Use MongoConnector().get_db() to obtain the AsyncIOMotorDatabase instance.
    """

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self._uri = uri or settings.MONGO_URI
        if not self._uri:
            raise ValueError("MONGO_URI not configured in settings")
        self._db_name = db_name or settings.MONGO_DB
        self._client: Optional[AsyncIOMotorClient] = None

    def get_client(self) -> AsyncIOMotorClient:
        if self._client is None:
            self._client = AsyncIOMotorClient(self._uri)
        return self._client

    def get_db(self, db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
        client = self.get_client()
        return client[db_name or self._db_name]
