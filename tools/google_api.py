import json
from pathlib import Path
from typing import Any, Tuple

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials


def create_flow(client_secrets_file: str, scopes: Any, redirect_uri: str) -> Flow:
    """Create an OAuth Flow for the given client secrets, scopes and redirect URI.

    Tries to use the 'web' section in client_secrets if present, otherwise
    falls back to the helper that reads the file.
    """
    try:
        cs_path = Path(client_secrets_file)
        if cs_path.exists():
            data = json.loads(cs_path.read_text())
            if 'web' in data:
                return Flow.from_client_config(data, scopes=scopes, redirect_uri=redirect_uri)
    except Exception:
        # If parsing fails, fallback to from_client_secrets_file below
        pass

    return Flow.from_client_secrets_file(client_secrets_file, scopes=scopes, redirect_uri=redirect_uri)


def build_authorization_url(client_secrets_file: str, scopes: Any, redirect_uri: str) -> Tuple[str, str]:
    """Return (authorization_url, state) for given client secrets and scopes."""
    flow = create_flow(client_secrets_file, scopes, redirect_uri)
    return flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')


def exchange_code_for_credentials(client_secrets_file: str, code: str, scopes: Any, redirect_uri: str) -> Credentials:
    """Exchange authorization code for Credentials object."""
    flow = create_flow(client_secrets_file, scopes, redirect_uri)
    flow.fetch_token(code=code)
    return flow.credentials
