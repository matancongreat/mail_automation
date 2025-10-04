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
async def callback(code: str, state: str = None):
    """Callback endpoint for Google's OAuth; exchanges code for tokens."""
    try:
        user_id = gmail_service.exchange_code_for_credentials(code, settings.GOOGLE_SCOPES, settings.GOOGLE_REDIRECT_URI)
        # After exchanging tokens, you might want to redirect users to a UI route.
        return {"message": "Authorization successful", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
