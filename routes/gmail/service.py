from google_auth_oauthlib.flow import Flow
from config.settings import settings


class GmailService:
    @staticmethod
    def get_flow():
        """Create OAuth flow"""
        return Flow.from_client_secrets_file(
            settings.CLIENT_SECRETS_FILE,
            scopes=settings.SCOPES,
            redirect_uri=settings.REDIRECT_URI
        )
