from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from config.settings import settings
from typing import Dict, Any, List, Optional
from models.user_credentials import UserCredentials
from tools.google_api import build_authorization_url, exchange_code_for_credentials
from repositories.repo import MongoRepo
import asyncio
from functools import partial


class GmailService:
    """Async service layer for Gmail operations.

    Uses Motor (AsyncIOMotorClient) via `MongoRepo` for non-blocking DB access. Blocking
    Google API operations are executed in a thread using asyncio.to_thread.
    """

    def __init__(self):
        # Use MongoDB repository for persistence
        self._repo = MongoRepo()

    def get_flow(self, scopes, redirect_uri) -> Flow:
        """Create OAuth flow using provided scopes and redirect_uri."""
        from tools.google_api import create_flow
        return create_flow(settings.CLIENT_SECRETS_FILE, scopes, redirect_uri)

    def get_authorization_url(self, scopes, redirect_uri) -> Dict[str, str]:
        authorization_url, state = build_authorization_url(settings.CLIENT_SECRETS_FILE, scopes, redirect_uri)
        return {"authorization_url": authorization_url, "state": state}

    async def exchange_code_for_credentials(self, code: str, scopes, redirect_uri) -> dict:
        """Exchange OAuth code for credentials and store them in MongoDB.

        Returns a dict with user_id, user_info and scope (space-separated string).
        """
        # exchange_code_for_credentials in tools is sync; run it in a thread
        credentials: Credentials = await asyncio.to_thread(
            partial(exchange_code_for_credentials, settings.CLIENT_SECRETS_FILE, code, scopes, redirect_uri)
        )

        # Extract id_token if present and verify it to get user info
        id_token_val = getattr(credentials, "id_token", None)
        user_info = None
        if id_token_val:
            try:
                from google.oauth2 import id_token as google_id_token
                from google.auth.transport import requests as auth_requests

                request = auth_requests.Request()
                aud = credentials.client_id if hasattr(credentials, 'client_id') else None
                user_info = google_id_token.verify_oauth2_token(id_token_val, request, aud)
            except Exception:
                user_info = None

        if not user_info:
            raise ValueError("Unable to verify id_token and extract user identity")

        user_id = user_info['sub']
        scopes = credentials.scopes

        # Store core credentials in MongoDB
        creds_model = UserCredentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            scopes=list(scopes) if scopes else []
        )
        await self._repo.save_credentials(user_id, creds_model)

        if user_info:
            await self._repo.save_user_info(user_id, user_info)

        scope_str = " ".join(list(scopes)) if scopes else ""
        return {"user_id": user_id, "user_info": user_info, "scope": scope_str}

    async def has_user(self, user_id: str) -> bool:
        return await self._repo.get_credentials(user_id) is not None

    async def _build_credentials(self, user_id: str) -> Credentials:
        doc = await self._repo.get_credentials(user_id)
        if not doc:
            raise KeyError(f"No credentials found for user {user_id}")

        doc.pop('user_id', None)
        return Credentials(**doc)

    async def build_service(self, user_id: str):
        creds = await self._build_credentials(user_id)
        # build is blocking; run in a thread
        service = await asyncio.to_thread(partial(build, 'gmail', 'v1', credentials=creds))
        return service

    async def list_messages(self, user_id: str, max_results: int = 10) -> Dict[str, Any]:
        service = await self.build_service(user_id)

        def _list_and_fetch():
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                return {"total": 0, "emails": []}

            emails: List[Dict[str, Any]] = []
            for message in messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = msg.get('payload', {}).get('headers', [])
                email_data: Dict[str, Any] = {
                    'id': msg.get('id'),
                    'snippet': msg.get('snippet')
                }

                for header in headers:
                    name = header.get('name')
                    value = header.get('value')
                    if name == 'From':
                        email_data['from'] = value
                    elif name == 'Subject':
                        email_data['subject'] = value
                    elif name == 'Date':
                        email_data['date'] = value

                emails.append(email_data)

            return {"total": len(emails), "emails": emails}

        return await asyncio.to_thread(_list_and_fetch)

    async def get_message(self, user_id: str, message_id: str) -> Dict[str, Any]:
        service = await self.build_service(user_id)

        def _get_message():
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return {
                "id": message.get('id'),
                "threadId": message.get('threadId'),
                "snippet": message.get('snippet'),
                "payload": message.get('payload')
            }

        return await asyncio.to_thread(_get_message)

    async def revoke(self, user_id: str) -> bool:
        creds_deleted = await self._repo.delete_credentials(user_id)
        try:
            await self._repo.delete_user_info(user_id)
        except Exception:
            pass

        return creds_deleted

