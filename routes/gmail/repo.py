from typing import Optional, Dict, Any, List
from models.user_credentials import UserCredentials
from db.mongo_connector import MongoConnector


class GmailRepo:
    """Repository for Gmail-related persistence operations.

    Uses the shared MongoConnector to obtain the DB instance.
    """

    def __init__(self):
        self._db = MongoConnector().get_db()
        self._credentials = self._db.get_collection("gmail_credentials")
        self._user_info = self._db.get_collection("gmail_user_info")

    async def save_credentials(self, user_id: str, creds: UserCredentials) -> None:
        doc = creds.dict()
        doc.update({"user_id": user_id})
        await self._credentials.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)

    async def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self._credentials.find_one({"user_id": user_id}, {'_id': 0})

    async def delete_credentials(self, user_id: str) -> bool:
        res = await self._credentials.delete_one({"user_id": user_id})
        return res.deleted_count > 0

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
