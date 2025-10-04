from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
import json

from routes.gmail.service import GmailService
from routes.gmail.repo import GmailRepo
from fastapi import Depends
from dependencies.db import get_gmail_repo
from config.settings import settings
from tools.oauth import handle_oauth_callback


router = APIRouter(prefix="/google", tags=["google-auth"])



@router.get("/authenticate")
async def authenticate(repo: GmailRepo = Depends(get_gmail_repo)):
    """Start Google's OAuth consent flow and return the authorization URL and state."""
    try:
        service = GmailService(repo=repo)
        urls = service.get_authorization_url(scopes=settings.GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI)
        # Return the URL and state so callers can redirect the user client-side.
        return {**urls, "message": "Visit the authorization_url to grant permissions"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create auth URL: {e}")


@router.get("/callback")
async def callback(code: str, state: str = None, response: Response = None, scope: str = settings.GOOGLE_SCOPES,
                   repo: GmailRepo = Depends(get_gmail_repo)):
    """Callback endpoint for Google's OAuth; exchanges code for tokens."""
    try:
        service = GmailService(repo=repo)
        return await handle_oauth_callback(service, code, scope, settings.GOOGLE_REDIRECT_URI, response,
                                           settings.FRONT_URL, message="Authorization successful")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")
