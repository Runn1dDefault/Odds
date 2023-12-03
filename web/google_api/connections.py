from apiclient import discovery
from google.oauth2 import service_account

from config import SCOPES, CREDENTIALS_JSON


def spreadsheets_service(api_version: str) -> discovery.build:
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_JSON, scopes=SCOPES)
    return discovery.build('sheets', api_version, credentials=credentials)
