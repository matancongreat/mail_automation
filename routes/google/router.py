from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from routes.gmail.service import GmailService
from config.settings import settings


router = APIRouter(prefix="/google", tags=["google-auth"])


gmail_service = GmailService()


@router.get("/authenticate")
async def authenticate():
    """Start Google's OAuth consent flow and return the authorization URL and state."""
    try:
        urls = gmail_service.get_authorization_url(scopes=settings.GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI)
        # Return the URL and state so callers can redirect the user client-side.
        return {**urls, "message": "Visit the authorization_url to grant permissions"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create auth URL: {e}")


@router.get("/callback")
async def callback(code: str, state: str = None, scope: str = settings.GOOGLE_SCOPES):
    """Callback endpoint for Google's OAuth; exchanges code for tokens."""
    try:
        result = gmail_service.exchange_code_for_credentials(code, scope, settings.GOOGLE_REDIRECT_URI)
        user_id = result.get("user_id")
        user_info = result.get("user_info")
        # After exchanging tokens, you might want to redirect users to a UI route.
        return {"message": "Authorization successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
