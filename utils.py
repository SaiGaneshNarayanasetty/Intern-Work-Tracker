from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

EXPECTED_HEADER = [
    "date",
    "intern_name",
    "role",
    "update_text",
    "tags",
    "created_at",
    "created_by",
]

def _load_creds_from_streamlit_secrets() -> Optional[Dict[str, Any]]:
    if "GCP_SERVICE_ACCOUNT" not in st.secrets:
        return None
    raw = st.secrets["GCP_SERVICE_ACCOUNT"]
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        try:
            import base64
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception:
            raise RuntimeError("Unable to parse GCP_SERVICE_ACCOUNT from st.secrets")

def load_service_account_credentials() -> Dict[str, Any]:
    creds_dict = _load_creds_from_streamlit_secrets()
    if creds_dict:
        return creds_dict
    local_path = os.path.join(os.getcwd(), "service_account.json")
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    raise RuntimeError(
        "Google service account credentials not found. Set st.secrets['GCP_SERVICE_ACCOUNT'] or place service_account.json locally."
    )

def _gspread_client_from_creds_dict(creds_dict: Dict[str, Any]) -> gspread.Client:
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def df_from_sheet(sheet_id: str, credentials: Dict[str, Any]) -> pd.DataFrame:
    client = _gspread_client_from_creds_dict(credentials)
    sh = client.open_by_key(sheet_id)
    worksheet = sh.sheet1

    # Ensure header is correct
    header = worksheet.row_values(1)
    if header != EXPECTED_HEADER:
        worksheet.update([EXPECTED_HEADER], "A1")  # replace header row

    records = worksheet.get_all_records(expected_headers=EXPECTED_HEADER)
    df = pd.DataFrame(records)
    return df

def parse_sheet_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()

    for col in EXPECTED_HEADER:
        if col not in df.columns:
            df[col] = None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    df = df.sort_values(by=["date", "created_at"], ascending=[False, False])
    df = df.reset_index(drop=True)
    return df

def append_update_to_sheet(sheet_id: str, credentials: Dict[str, Any], row: Dict[str, Any]) -> None:
    client = _gspread_client_from_creds_dict(credentials)
    sh = client.open_by_key(sheet_id)
    worksheet = sh.sheet1

    header = worksheet.row_values(1)
    if header != EXPECTED_HEADER:
        worksheet.update([EXPECTED_HEADER], "A1")

    ordered = [row.get(col, "") for col in EXPECTED_HEADER]
    worksheet.append_row(ordered, value_input_option="USER_ENTERED")
