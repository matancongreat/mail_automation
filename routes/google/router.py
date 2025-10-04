from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
import json

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
async def callback(code: str, state: str = None, response: Response = None, scope: str = settings.GOOGLE_SCOPES):
    """Callback endpoint for Google's OAuth; exchanges code for tokens."""
    try:
        result = gmail_service.exchange_code_for_credentials(code, scope, settings.GOOGLE_REDIRECT_URI)
        user_id = result.get("user_id")
        user_info = result.get("user_info") or {}

        # Set user_info cookie on the provided response (HTTPOnly). In prod, set secure=True.
        if response is not None:
            response.set_cookie("user_info", json.dumps(user_info), httponly=True, secure=False,
                                domain=settings.FRONT_URL)

        return {"message": "Authorization successful", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
