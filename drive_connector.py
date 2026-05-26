import os
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_credentials():
    """
    Priority: credentials.json in cwd → GOOGLE_APPLICATION_CREDENTIALS env var
    """
    if os.path.exists("credentials.json"):
        return service_account.Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )

    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        return service_account.Credentials.from_service_account_file(
            env_path, scopes=SCOPES
        )

    raise RuntimeError(
        "credentials.json not found. "
        "Place the service account JSON at the project root."
    )


@st.cache_resource
def get_sheets_service():
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def read_sheet(spreadsheet_id: str, sheet_name: str) -> list[list]:
    """Returns all rows (including header) from a named sheet as list-of-lists."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"'{sheet_name}'")
        .execute()
    )
    return result.get("values", [])
