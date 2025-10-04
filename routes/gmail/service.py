from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config.settings import settings
from typing import Dict, Any, List, Optional


class GmailService:
    """Service layer for Gmail operations.

    Responsibilities moved out of the FastAPI router to keep handlers thin.
    """

    def __init__(self):
        # In-memory store for user credentials. Replace with DB in production.
        self._user_credentials: Dict[str, Dict[str, Any]] = {}

    def get_flow(self) -> Flow:
        """Create OAuth flow"""
        return Flow.from_client_secrets_file(
            settings.CLIENT_SECRETS_FILE,
            scopes=settings.SCOPES,
            redirect_uri=settings.REDIRECT_URI
        )

    def get_authorization_url(self) -> Dict[str, str]:
        flow = self.get_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return {"authorization_url": authorization_url, "state": state}

    def exchange_code_for_credentials(self, code: str) -> str:
        """Exchange OAuth code for credentials and store them.

        Returns a generated user_id. Currently a static placeholder; in
        production this should be tied to an authenticated user/session.
        """
        flow = self.get_flow()
        flow.fetch_token(code=code)
        credentials: Credentials = flow.credentials

        # TODO: use real user id from session/JWT
        user_id = "user_123"
        self._user_credentials[user_id] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else []
        }

        return user_id

    def has_user(self, user_id: str) -> bool:
        return user_id in self._user_credentials

    def _build_credentials(self, user_id: str) -> Credentials:
        creds_data = self._user_credentials[user_id]
        return Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

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

