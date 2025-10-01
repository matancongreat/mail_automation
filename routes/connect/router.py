from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from pathlib import Path

from routes.gmail.service import GmailService

router = APIRouter(prefix="/gmail", tags=["gmail"])


user_credentials = {}
gmail_service = GmailService()


@router.get("/authorize")
async def authorize():
    """
    Step 1: Redirect user to Google's OAuth consent screen
    """
    flow = gmail_service.get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # Store state for verification (use session/database in production)
    return {
        "authorization_url": authorization_url,
        "state": state,
        "message": "Visit the authorization_url to grant permissions"
    }


@router.get("/callback")
async def oauth_callback(code: str, state: str):
    """
    Step 2: Handle OAuth callback and exchange code for tokens
    """
    try:
        flow = gmail_service.get_flow()
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Store credentials (use proper database with encryption in production)
        user_id = "user_123"  # Get from session/JWT in production
        user_credentials[user_id] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        return {
            "message": "Authorization successful! You can now read emails.",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {str(e)}")


@router.get("/emails")
async def get_emails(user_id: str = "user_123", max_results: int = 10):
    """
    Step 3: Read user's emails using stored credentials
    """
    if user_id not in user_credentials:
        raise HTTPException(
            status_code=401,
            detail="User not authorized. Please visit /gmail/authorize first."
        )

    try:
        # Reconstruct credentials from stored data
        creds_data = user_credentials[user_id]
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        # Build Gmail API service
        service = build('gmail', 'v1', credentials=credentials)

        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return {"emails": [], "message": "No emails found"}

        # Fetch email details
        emails = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = msg['payload']['headers']
            email_data = {
                'id': msg['id'],
                'snippet': msg['snippet'],
            }

            for header in headers:
                if header['name'] == 'From':
                    email_data['from'] = header['value']
                elif header['name'] == 'Subject':
                    email_data['subject'] = header['value']
                elif header['name'] == 'Date':
                    email_data['date'] = header['value']

            emails.append(email_data)

        return {
            "total": len(emails),
            "emails": emails
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")


@router.get("/email/{message_id}")
async def get_email_content(message_id: str, user_id: str = "user_123"):
    """
    Get full content of a specific email
    """
    if user_id not in user_credentials:
        raise HTTPException(status_code=401, detail="User not authorized")

    try:
        creds_data = user_credentials[user_id]
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        service = build('gmail', 'v1', credentials=credentials)

        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        return {
            "id": message['id'],
            "threadId": message['threadId'],
            "snippet": message['snippet'],
            "payload": message['payload']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")


@router.delete("/revoke")
async def revoke_access(user_id: str = "user_123"):
    """
    Revoke access and delete stored credentials
    """
    if user_id in user_credentials:
        del user_credentials[user_id]
        return {"message": "Access revoked successfully"}

    raise HTTPException(status_code=404, detail="User not found")