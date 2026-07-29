"""
One-time Google Calendar auth setup.

Run this file by itself once:  python google_auth.py
It will open a browser window, ask you to log into Google, and save a
token.json file so companion.py can read your calendar without you
logging in again.

Requires credentials.json in this same folder (see README.md for how
to get that from Google Cloud Console — it's free).
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


def _get_credentials():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    "credentials.json not found. See README.md for how "
                    "to download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_calendar_service():
    return build("calendar", "v3", credentials=_get_credentials())


def get_tasks_service():
    return build("tasks", "v1", credentials=_get_credentials())


def get_gmail_service():
    return build("gmail", "v1", credentials=_get_credentials())


if __name__ == "__main__":
    print("Opening browser to connect your Google account...")
    print("(This grants access to Calendar, Tasks, and Gmail in one go.)")
    _get_credentials()
    print("Done — token.json created. You won't need to log in again.")