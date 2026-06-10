import re

import pandas as pd
import streamlit as st

from components.colors import CAT1_COLORS, SPECIFICITY_COLORS, badge as _badge


def _normalize_article_id(ref: str) -> str:
    """Zero-pads the numeric part of an article ref, e.g. 'A3' -> 'A03'."""
    m = re.match(r"^([A-Za-z]+)(\d+)$", ref)
    if m:
        return f"{m.group(1)}{int(m.group(2)):02d}"
    return ref


@st.dialog("Challenge detail", width="large")
def _show_detail(row: pd.Series, df_articles: pd.DataFrame):
    cat1 = str(row.get("cat_1", "")).strip()
    cat_color = CAT1_COLORS.get(cat1, "#888888")
    spec = str(row.get("regional_specificity", "")).strip()
    spec_color = SPECIFICITY_COLORS.get(spec, "#888888")

    st.markdown(
        f'{_badge(cat1, cat_color)}&nbsp;&nbsp;{_badge(spec, spec_color)}',
        unsafe_allow_html=True,
    )
    st.markdown(f"### {str(row.get('cat_2_en', '')).strip()}")

    desc = str(row.get("description_en", "")).strip()
    if desc and desc != "nan":
        st.markdown("**Description**")
        st.write(desc)

    rationale = str(row.get("regional_rationale", "")).strip()
    if rationale and rationale != "nan":
        st.markdown("**Regional rationale**")
        st.write(rationale)

    wirtz = str(row.get("wirtz_mapping", "")).strip()
    if wirtz and wirtz != "nan":
        st.markdown(f"**Wirtz (2020) mapping:** {wirtz}")

    countries = str(row.get("countries_mentioned", "")).strip()
    if countries and countries != "nan":
        st.markdown(f"**Countries mentioned:** {countries}")

    first_year = row.get("first_year_cited")
    if pd.notna(first_year):
        st.markdown(f"**First cited:** {int(first_year)}")

    key_arts = str(row.get("key_articles", "")).strip()
    if key_arts and key_arts != "nan":
        st.markdown("**Key articles:**")
        for art_ref in key_arts.split(","):
            art_ref = art_ref.strip()
            if not art_ref:
                continue
            if not df_articles.empty and "id" in df_articles.columns:
                match = df_articles[df_articles["id"] == _normalize_article_id(art_ref)]
                if not match.empty:
                    qref = str(match.iloc[0].get("quick_ref", art_ref)).strip()
                    doi = str(match.iloc[0].get("doi", "")).strip()
                    if doi and doi != "nan" and any(c.isalnum() for c in doi):
                        if not doi.startswith("http"):
                            doi = f"https://doi.org/{doi}"
                        st.markdown(f"- [{qref}]({doi})")
                    else:
                        st.markdown(f"- {qref}")
                else:
                    st.markdown(f"- {art_ref}")
            else:
                st.markdown(f"- {art_ref}")


def render_challenge_card(row: pd.Series, col, df_articles: pd.DataFrame):
    cat1 = str(row.get("cat_1", "")).strip()
    cat_color = CAT1_COLORS.get(cat1, "#888888")
    spec = str(row.get("regional_specificity", "")).strip()
    spec_color = SPECIFICITY_COLORS.get(spec, "#888888")
    title = str(row.get("cat_2_en", "")).strip()
    article_count = row.get("article_count", 0)
    row_id = str(row.get("id", "")).strip()

    with col:
        with st.container(border=True):
            st.markdown(
                f"""<div style="border-left:4px solid {cat_color};padding-left:10px;margin-bottom:4px;">
  {_badge(cat1, cat_color)}
  <p style="margin:6px 0 4px 0;font-weight:600;font-size:0.97em;line-height:1.3">{title}</p>
  <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
    {_badge(spec, spec_color)}
    <span style="font-size:0.78em;color:#777">{article_count} article{'s' if article_count != 1 else ''} &middot; ID&nbsp;{row_id}</span>
  </div>
</div>""",
                unsafe_allow_html=True,
            )

            if st.button("View detail", key=f"detail_{row_id}", use_container_width=True):
                _show_detail(row, df_articles)


def render_challenge_grid(df: pd.DataFrame, df_articles: pd.DataFrame):
    if df.empty:
        st.info("No challenges match the current filters.")
        return

    records = df.to_dict("records")
    for i in range(0, len(records), 3):
        cols = st.columns(3)
        for j, rec in enumerate(records[i : i + 3]):
            render_challenge_card(pd.Series(rec), cols[j], df_articles)
