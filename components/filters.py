import streamlit as st
import pandas as pd
from typing import Tuple

CAT1_COLORS = {
    "Socio-technical": "#1D9E75",
    "Ethical":         "#D85A30",
    "Institutional":   "#7F77DD",
}

SPECIFICITY_COLORS = {
    "High":   "#27ae60",
    "Medium": "#f39c12",
    "Low":    "#95a5a6",
}


def render_sidebar_filters(df: pd.DataFrame) -> Tuple[list, list, str]:
    """
    Renders sidebar filter widgets for the Repository tab.
    Returns (selected_cat1, selected_specificity, search_text).
    """
    st.sidebar.header("Filters")

    cat1_options = sorted(df["cat_1"].dropna().unique().tolist())
    selected_cat1 = st.sidebar.multiselect(
        "Category (cat_1)", options=cat1_options, default=[]
    )

    spec_options = [s for s in ["High", "Medium", "Low"] if s in df["regional_specificity"].values]
    selected_specificity = st.sidebar.multiselect(
        "Regional Specificity", options=spec_options, default=[]
    )

    search_text = st.sidebar.text_input(
        "Search", placeholder="Title, description, quick ref…"
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh data", help="Clear cache and reload from Google Drive"):
        st.cache_data.clear()
        st.rerun()

    return selected_cat1, selected_specificity, search_text


def apply_challenge_filters(
    df: pd.DataFrame,
    selected_cat1: list,
    selected_specificity: list,
    search_text: str,
) -> pd.DataFrame:
    """
    Sequential AND-chain filter: cat_1 → regional_specificity → full-text search.
    Empty selection on any dimension = no filter on that dimension.
    """
    result = df.copy()

    if selected_cat1:
        result = result[result["cat_1"].isin(selected_cat1)]

    if selected_specificity:
        result = result[result["regional_specificity"].isin(selected_specificity)]

    if search_text.strip():
        q = search_text.strip().lower()
        search_cols = ["title_en", "title_es", "quick_ref_en", "description_en"]
        mask = pd.Series(False, index=result.index)
        for col in search_cols:
            if col in result.columns:
                mask = mask | result[col].str.lower().str.contains(q, na=False)
        result = result[mask]

    return result.reset_index(drop=True)


def render_paper_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Inline filters for the By Paper tab. Returns filtered DataFrame."""
    col1, col2, col3 = st.columns(3)

    with col1:
        paper_ids = ["All"] + sorted(df["paper_id"].dropna().unique().tolist())
        sel_paper = st.selectbox("Paper ID", paper_ids, key="bp_paper")

    with col2:
        cat1_opts = ["All"] + sorted(df["cat_1"].dropna().unique().tolist())
        sel_cat1 = st.selectbox("Category", cat1_opts, key="bp_cat1")

    with col3:
        spec_opts = ["All"] + [s for s in ["High", "Medium", "Low"] if s in df["regional_specificity"].values]
        sel_spec = st.selectbox("Regional Specificity", spec_opts, key="bp_spec")

    result = df.copy()
    if sel_paper != "All":
        result = result[result["paper_id"] == sel_paper]
    if sel_cat1 != "All":
        result = result[result["cat_1"] == sel_cat1]
    if sel_spec != "All":
        result = result[result["regional_specificity"] == sel_spec]
    return result.reset_index(drop=True)


def render_article_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Inline filters for the Articles tab. Returns filtered DataFrame."""
    col1, col2, col3 = st.columns(3)

    with col1:
        types = ["All"] + sorted(df["type"].dropna().unique().tolist())
        sel_type = st.selectbox("Type", types, key="art_type")

    with col2:
        langs = ["All"] + sorted(df["language"].dropna().unique().tolist())
        sel_lang = st.selectbox("Language", langs, key="art_lang")

    with col3:
        years = df["year"].dropna()
        min_y = int(years.min()) if not years.empty else 2000
        max_y = int(years.max()) if not years.empty else 2026
        year_range = st.slider("Year range", min_y, max_y, (min_y, max_y), key="art_year")

    result = df.copy()
    if sel_type != "All":
        result = result[result["type"] == sel_type]
    if sel_lang != "All":
        result = result[result["language"] == sel_lang]
    result = result[result["year"].between(year_range[0], year_range[1])]
    return result.reset_index(drop=True)
