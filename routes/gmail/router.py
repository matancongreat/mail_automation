from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import json

from routes.gmail.service import GmailService
from routes.gmail.repo import GmailRepo
from fastapi import Depends
from dependencies.db import get_gmail_repo
from config.settings import settings

router = APIRouter(prefix="/gmail", tags=["gmail"])




@router.get("/authorize")
async def authorize(repo: GmailRepo = Depends(get_gmail_repo)):
    """
    Step 1: Redirect user to Google's OAuth consent screen
    """
    service = GmailService(repo=repo)
    urls = service.get_authorization_url(scopes=settings.GMAIL_SCOPES, redirect_uri=settings.GMAIL_REDIRECT_URI)
    return {**urls, "message": "Visit the authorization_url to grant permissions"}


@router.get("/callback")
async def oauth_callback(code: str, state: str, response: Response, scope: str = settings.GMAIL_SCOPES,
                         repo: GmailRepo = Depends(get_gmail_repo)):
    """
    Step 2: Handle OAuth callback and exchange code for tokens
    """
    try:
        service = GmailService(repo=repo)
        result = await service.exchange_code_for_credentials(code, scope, settings.GMAIL_REDIRECT_URI)
        user_id = result.get("user_id")
        user_info = result.get("user_info") or {}
        scope_val = result.get("scope")

        # Normalize scopes into a list for the response
        if isinstance(scope_val, str):
            scopes = scope_val.split() if scope_val else []
        elif isinstance(scope_val, (list, tuple)):
            scopes = list(scope_val)
        else:
            # fall back to the incoming scope param (which may be a str or list)
            if isinstance(scope, str):
                scopes = scope.split() if scope else []
            elif isinstance(scope, (list, tuple)):
                scopes = list(scope)
            else:
                scopes = []

        # Set user_info as an HTTPOnly cookie (JSON-encoded). In prod, set secure=True.
        response.set_cookie("user_info", json.dumps(user_info), httponly=True, secure=False,
                            domain=settings.FRONT_URL)

        return {"message": "Authorization successful! You can now read emails.", "user_id": user_id,
                "user_info": user_info,
                "scopes": scopes}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")


@router.get("/emails")
async def get_emails(user_id: str = "user_123", max_results: int = 10, repo: GmailRepo = Depends(get_gmail_repo)):
    """
    Step 3: Read user's emails using stored credentials
    """
    service = GmailService(repo=repo)
    if not await service.has_user(user_id):
        raise HTTPException(status_code=401, detail="User not authorized. Please visit /gmail/authorize first.")
    try:
        return await service.list_messages(user_id=user_id, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")


@router.get("/email/{message_id}")
async def get_email_content(message_id: str, user_id: str = "user_123", repo: GmailRepo = Depends(get_gmail_repo)):
    """
    Get full content of a specific email
    """
    service = GmailService(repo=repo)
    if not await service.has_user(user_id):
        raise HTTPException(status_code=401, detail="User not authorized")
    try:
        return await service.get_message(user_id=user_id, message_id=message_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")


@router.delete("/revoke")
async def revoke_access(user_id: str = "user_123", repo: GmailRepo = Depends(get_gmail_repo)):
    """
    Revoke access and delete stored credentials
    """
    service = GmailService(repo=repo)
    if await service.revoke(user_id):
        return {"message": "Access revoked successfully"}

    raise HTTPException(status_code=404, detail="User not found")