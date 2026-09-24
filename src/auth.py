from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_CLIENT_SECRET_FILE, GMAIL_SCOPES, GMAIL_TOKEN_FILE


def get_gmail_service():
    creds = None
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GMAIL_CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {GMAIL_CLIENT_SECRET_FILE}. Download it from Google Cloud "
                    "Console (OAuth client, Desktop app type) and place it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GMAIL_CLIENT_SECRET_FILE), GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        GMAIL_TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)
