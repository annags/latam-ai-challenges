import pandas as pd
import streamlit as st
from drive_connector import read_sheet

SPREADSHEET_ID = "1vjfeBiTcjn1m-gCoNmmBVUe-FJS-sjSUBXuYzGy47Y4"

SHEET_CHALLENGES = "Challenges Repository"
SHEET_ARTICLES   = "Articles Reference"
SHEET_STATS      = "Statistics"
SHEET_BY_PAPER   = "Challenges by Paper"


def _rows_to_df(rows: list[list]) -> pd.DataFrame:
    """Convert list-of-lists (first row = headers) to DataFrame."""
    if not rows:
        return pd.DataFrame()
    headers = rows[0]
    data = rows[1:]
    # Pad short rows so all rows have the same number of columns
    data = [r + [""] * (len(headers) - len(r)) for r in data]
    return pd.DataFrame(data, columns=headers)


@st.cache_data(ttl=3600)
def load_challenges() -> pd.DataFrame:
    rows = read_sheet(SPREADSHEET_ID, SHEET_CHALLENGES)
    df = _rows_to_df(rows)
    df["article_count"] = pd.to_numeric(df.get("article_count", 0), errors="coerce").fillna(0).astype(int)
    df["first_year_cited"] = pd.to_numeric(df.get("first_year_cited"), errors="coerce")
    for col in ("id", "cat_1", "cat_2", "regional_specificity"):
        if col in df.columns:
            df[col] = df[col].str.strip()
    return df


@st.cache_data(ttl=3600)
def load_articles() -> pd.DataFrame:
    rows = read_sheet(SPREADSHEET_ID, SHEET_ARTICLES)
    df = _rows_to_df(rows)
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    for col in ("id", "type", "language"):
        if col in df.columns:
            df[col] = df[col].str.strip()
    return df


@st.cache_data(ttl=3600)
def load_by_paper() -> pd.DataFrame:
    rows = read_sheet(SPREADSHEET_ID, SHEET_BY_PAPER)
    df = _rows_to_df(rows)
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    for col in ("paper_id", "cat_1", "regional_specificity"):
        if col in df.columns:
            df[col] = df[col].str.strip()
    return df


@st.cache_data(ttl=3600)
def load_statistics_raw() -> pd.DataFrame:
    rows = read_sheet(SPREADSHEET_ID, SHEET_STATS)
    if not rows:
        return pd.DataFrame()
    max_cols = max(len(r) for r in rows)
    padded = [r + [""] * (max_cols - len(r)) for r in rows]
    return pd.DataFrame(padded)
