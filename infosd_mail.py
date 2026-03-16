"""
infosd 메일 발송 모듈
Gmail OAuth2 기반 이메일 발송
"""
import os
import base64
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_APP_DIR = Path(__file__).parent.resolve()
_CREDENTIALS_PATH = str(_APP_DIR / 'credentials.json')
_TOKEN_PATH = str(_APP_DIR / 'token.pickle')


def get_gmail_credentials():
    """Gmail OAuth2 인증 토큰 획득"""
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    if os.path.exists(_TOKEN_PATH):
        with open(_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def send_gmail(to, subject, body):
    """텍스트 메일 발송"""
    if os.getenv('MOCK_MAIL') == 'True':
        print(f"[MOCK_MAIL] To: {to}, Subject: {subject}\n{body}")
        return True

    creds = get_gmail_credentials()
    service = build('gmail', 'v1', credentials=creds)

    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain', 'utf-8'))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': raw}).execute()
    return True
