from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from config.settings import settings
from typing import Dict, Any, List, Optional
from models.user_credentials import UserCredentials
from tools.google_api import build_authorization_url, exchange_code_for_credentials


class GmailService:
    """Service layer for Gmail operations.

    Responsibilities moved out of the FastAPI router to keep handlers thin.
    """

    def __init__(self):
        # In-memory store for user credentials. Replace with DB in production.
        self._user_credentials: Dict[str, UserCredentials] = {}
        # Store decoded id_token payloads by user_id
        self._user_info: Dict[str, Dict[str, Any]] = {}

    def get_flow(self, scopes, redirect_uri) -> Flow:
        """Create OAuth flow using provided scopes and redirect_uri."""
        # Delegated to tools.google_api if callers need a Flow instance.
        # Keep this method for backward compatibility if code expects it.
        from tools.google_api import create_flow
        return create_flow(settings.CLIENT_SECRETS_FILE, scopes, redirect_uri)

    def get_authorization_url(self, scopes, redirect_uri) -> Dict[str, str]:
        # scopes and redirect_uri are required — caller must pass them explicitly.
        authorization_url, state = build_authorization_url(settings.CLIENT_SECRETS_FILE, scopes, redirect_uri)
        return {"authorization_url": authorization_url, "state": state}

    def exchange_code_for_credentials(self, code: str, scopes, redirect_uri) -> dict[str, list[Any] | None | Any]:
        """Exchange OAuth code for credentials and store them.

        Returns a generated user_id. Currently a static placeholder; in
        production this should be tied to an authenticated user/session.
        """
        credentials: Credentials = exchange_code_for_credentials(settings.CLIENT_SECRETS_FILE, code, scopes, redirect_uri)

        # Extract id_token if present and verify it to get user info
        id_token_val = getattr(credentials, "id_token", None)
        user_info = None
        if id_token_val:
            try:
                from google.oauth2 import id_token as google_id_token
                from google.auth.transport import requests as auth_requests

                request = auth_requests.Request()
                # Verify token; audience is the client_id
                aud = credentials.client_id if hasattr(credentials, 'client_id') else None
                user_info = google_id_token.verify_oauth2_token(id_token_val, request, aud)
            except Exception:
                user_info = None

        user_id = user_info['sub']
        scopes = credentials.scopes
        # Store core credentials (not storing id_token on the model to keep model simple)
        self._user_credentials[user_id] = UserCredentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            scopes=list(scopes) if scopes else []
        )

        if user_info:
            self._user_info[user_id] = user_info

        return {"user_id": user_id, "user_info": user_info, "scope": scopes.split(" ")}

    def has_user(self, user_id: str) -> bool:
        return user_id in self._user_credentials

    def _build_credentials(self, user_id: str) -> Credentials:
        user_creds = self._user_credentials[user_id]
        # Use model dict unpacking to avoid repeating field names
        creds_data = user_creds.dict(exclude_none=True)
        return Credentials(**creds_data)

    def build_service(self, user_id: str):
        creds = self._build_credentials(user_id)
        return build('gmail', 'v1', credentials=creds)

    def list_messages(self, user_id: str, max_results: int = 10) -> Dict[str, Any]:
        service = self.build_service(user_id)
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

    def get_message(self, user_id: str, message_id: str) -> Dict[str, Any]:
        service = self.build_service(user_id)
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

    def revoke(self, user_id: str) -> bool:
        if user_id in self._user_credentials:
            del self._user_credentials[user_id]
            return True
        return False

