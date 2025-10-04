from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from models.user_credentials import UserCredentials


class MongoRepo:
    """Async MongoDB repository using Motor for asyncio compatibility.

    Collections:
    - credentials: stores { user_id, token, refresh_token, token_uri, client_id, scopes }
    - user_info: stores { user_id, info }
    """

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        uri = uri or settings.MONGO_URI
        db_name = db_name or settings.MONGO_DB
        if not uri:
            raise ValueError("MONGO_URI must be set in settings to use MongoRepo")

        self._client = AsyncIOMotorClient(uri)
        self._db = self._client[db_name]
        self._credentials = self._db.get_collection("credentials")
        self._user_info = self._db.get_collection("user_info")

    # Credentials CRUD
    async def save_credentials(self, user_id: str, creds: UserCredentials) -> None:
        doc = creds.dict()
        doc.update({"user_id": user_id})
        await self._credentials.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)

    async def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = await self._credentials.find_one({"user_id": user_id}, {'_id': 0})
        return doc

    async def delete_credentials(self, user_id: str) -> bool:
        res = await self._credentials.delete_one({"user_id": user_id})
        return res.deleted_count > 0

    # User info CRUD
    async def save_user_info(self, user_id: str, info: Dict[str, Any]) -> None:
        doc = {"user_id": user_id, "info": info}
        await self._user_info.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = await self._user_info.find_one({"user_id": user_id}, {'_id': 0})
        return doc.get('info') if doc else None

    async def delete_user_info(self, user_id: str) -> bool:
        res = await self._user_info.delete_one({"user_id": user_id})
        return res.deleted_count > 0

    async def list_user_ids(self) -> List[str]:
        cursor = self._credentials.find({}, {'user_id': 1, '_id': 0})
        ids = []
        async for d in cursor:
            ids.append(d['user_id'])
        return ids
