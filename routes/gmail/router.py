from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from routes.gmail.service import GmailService
from config.settings import settings

router = APIRouter(prefix="/gmail", tags=["gmail"])


gmail_service = GmailService()


@router.get("/authorize")
async def authorize():
    """
    Step 1: Redirect user to Google's OAuth consent screen
    """
    urls = gmail_service.get_authorization_url(scopes=settings.GMAIL_SCOPES, redirect_uri=settings.GMAIL_REDIRECT_URI)
    return {**urls, "message": "Visit the authorization_url to grant permissions"}


@router.get("/callback")
async def oauth_callback(code: str, state: str):
    """
    Step 2: Handle OAuth callback and exchange code for tokens
    """
    try:
        user_id = gmail_service.exchange_code_for_credentials(code, settings.GMAIL_SCOPES, settings.GMAIL_REDIRECT_URI)
        return {"message": "Authorization successful! You can now read emails.", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")


@router.get("/emails")
async def get_emails(user_id: str = "user_123", max_results: int = 10):
    """
    Step 3: Read user's emails using stored credentials
    """
    if not gmail_service.has_user(user_id):
        raise HTTPException(status_code=401, detail="User not authorized. Please visit /gmail/authorize first.")

    try:
        return gmail_service.list_messages(user_id=user_id, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")


@router.get("/email/{message_id}")
async def get_email_content(message_id: str, user_id: str = "user_123"):
    """
    Get full content of a specific email
    """
    if not gmail_service.has_user(user_id):
        raise HTTPException(status_code=401, detail="User not authorized")

    try:
        return gmail_service.get_message(user_id=user_id, message_id=message_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")


@router.delete("/revoke")
async def revoke_access(user_id: str = "user_123"):
    """
    Revoke access and delete stored credentials
    """
    if gmail_service.revoke(user_id):
        return {"message": "Access revoked successfully"}

    raise HTTPException(status_code=404, detail="User not found")