import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Authenticates, gets a list of messages, and prints the subject of each.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Build the Gmail service object
    service = build('gmail', 'v1', credentials=creds)
    return service


def list_messages(service):
    """Lists the user's email messages and prints their subjects."""
    try:
        # Call the Gmail API to list messages

        request = {
            'labelIds': ['INBOX'],
            'topicName': 'projects/trygmailapi-472714/topics/CongreatGmailDevTest',
            'labelFilterBehavior': 'INCLUDE'
        }
        results = service.users().watch(userId='me', body=request).execute()
        print(results)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    service = get_gmail_service()
    if service:
        list_messages(service)

