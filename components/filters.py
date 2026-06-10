import streamlit as st
import pandas as pd
from typing import Tuple

from components.colors import CAT1_COLORS, SPECIFICITY_COLORS


def _pills_color_css(scope_class: str, colors: list) -> str:
    """
    CSS that colors each pill option in a st.pills widget, scoped to a
    st.container(key=scope_class) wrapper, by DOM order (one color per
    option, in the same order as the `options` list passed to st.pills).
    Selected = filled background + white text. Unselected = outlined.
    """
    rules = []
    for i, color in enumerate(colors, start=1):
        rules.append(f"""
        .st-key-{scope_class} [data-testid="stBaseButton-pills"]:nth-of-type({i}) {{
            border-color: {color} !important;
            color: {color} !important;
            background-color: transparent !important;
        }}
        .st-key-{scope_class} [data-testid="stBaseButton-pillsActive"]:nth-of-type({i}) {{
            background-color: {color} !important;
            border-color: {color} !important;
            color: white !important;
        }}
        """)
    return "\n".join(rules)


def render_repository_filters(df: pd.DataFrame) -> Tuple[list, list, str]:
    """
    Renders inline filter widgets for the Repository tab, in the main body.
    Returns (selected_cat1, selected_specificity, search_text).
    """
    cat1_options = sorted(df["cat_1"].dropna().unique().tolist())
    cat1_colors = [CAT1_COLORS.get(opt, "#888888") for opt in cat1_options]

    spec_options = [s for s in ["High", "Medium", "Low"] if s in df["regional_specificity"].values]
    spec_colors = [SPECIFICITY_COLORS.get(opt, "#888888") for opt in spec_options]

    st.markdown(
        f"<style>{_pills_color_css('cat1_pills', cat1_colors)}"
        f"{_pills_color_css('spec_pills', spec_colors)}</style>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        with st.container(key="cat1_pills"):
            selected_cat1 = st.pills(
                "AI challenges category",
                options=cat1_options,
                selection_mode="multi",
                default=[],
            ) or []

    with col2:
        with st.container(key="spec_pills"):
            selected_specificity = st.pills(
                "Regional specificity",
                options=spec_options,
                selection_mode="multi",
                default=[],
            ) or []

    with col3:
        search_text = st.text_input("Search", placeholder="Title, description, quick ref…")

    with col4:
        st.markdown("&nbsp;")
        if st.button("Refresh data", help="Clear cache and reload from Google Drive"):
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
        search_cols = ["cat_2_en", "cat_2_es", "description_en", "description_es"]
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
        quick_refs = ["All"] + sorted(df["quick_ref"].dropna().unique().tolist()) if "quick_ref" in df.columns else ["All"]
        sel_paper = st.selectbox("Paper (Quick Ref)", quick_refs, key="bp_paper")

    with col2:
        cat1_opts = ["All"] + sorted(df["cat_1"].dropna().unique().tolist())
        sel_cat1 = st.selectbox("Category", cat1_opts, key="bp_cat1")

    with col3:
        spec_opts = ["All"] + [s for s in ["High", "Medium", "Low"] if s in df["regional_specificity"].values]
        sel_spec = st.selectbox("Regional Specificity", spec_opts, key="bp_spec")

    result = df.copy()
    if sel_paper != "All":
        filter_col = "quick_ref" if "quick_ref" in result.columns else "paper_id"
        result = result[result[filter_col] == sel_paper]
    if sel_cat1 != "All":
        result = result[result["cat_1"] == sel_cat1]
    if sel_spec != "All":
        result = result[result["regional_specificity"] == sel_spec]
    return result.reset_index(drop=True)


def render_article_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Inline filters for the Articles tab. Returns filtered DataFrame."""
    col1, col2 = st.columns(2)

    with col1:
        langs = ["All"] + sorted(df["language"].dropna().unique().tolist())
        sel_lang = st.selectbox("Language", langs, key="art_lang")

    with col2:
        years = df["year"].dropna()
        min_y = int(years.min()) if not years.empty else 2000
        max_y = int(years.max()) if not years.empty else 2026
        year_range = st.slider("Year range", min_y, max_y, (min_y, max_y), key="art_year")

    result = df.copy()
    if sel_lang != "All":
        result = result[result["language"] == sel_lang]
    result = result[result["year"].between(year_range[0], year_range[1])]
    return result.reset_index(drop=True)
