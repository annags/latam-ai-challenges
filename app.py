from pathlib import Path

import pandas as pd
import streamlit as st

from data_loader import load_challenges, load_articles, load_by_paper, load_statistics_raw
from components.filters import (
    render_repository_filters,
    apply_challenge_filters,
    render_paper_filters,
    render_article_filters,
)
from components.challenge_card import render_challenge_grid
from components.charts import (
    chart_challenges_by_cat1,
    chart_challenges_by_specificity,
    chart_top_challenges_by_articles,
    chart_articles_by_year,
    chart_countries_cited,
    map_countries_cited,
)
from components.colors import CAT1_COLORS, SPECIFICITY_COLORS, badge, to_doi_url

st.set_page_config(
    page_title="LATAM AI Repository",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("LATAM AI Governance Challenges Repository")
st.caption(
    "A repository of AI governance challenges in Latin America based on a systematic literature review (2021-2026)"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Repository", "📄 By Paper", "📚 Articles", "📊 Statistics", "ℹ️ About"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Repository
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    df_challenges = load_challenges()
    selected_cat1, selected_spec, search_text = render_repository_filters(df_challenges)
    filtered = apply_challenge_filters(df_challenges, selected_cat1, selected_spec, search_text)

    st.caption(f"Showing **{len(filtered)}** of **{len(df_challenges)}** challenges")
    render_challenge_grid(filtered, df_articles=load_articles())

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — By Paper
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    df_by_paper = load_by_paper()
    st.subheader("Challenges by Paper")
    filtered_bp = render_paper_filters(df_by_paper)

    st.caption(f"Showing **{len(filtered_bp)}** of **{len(df_by_paper)}** entries")

    if filtered_bp.empty:
        st.info("No entries match the current filters.")
    else:
        df_articles_lookup = load_articles()[["quick_ref", "title", "doi"]].rename(
            columns={"title": "title_full"}
        )
        filtered_bp = filtered_bp.merge(df_articles_lookup, on="quick_ref", how="left")

        for _, row in filtered_bp.iterrows():
            year_str = f"{int(row['year'])}" if pd.notna(row.get("year")) else "n.d."
            challenge = str(row.get("cat_2_en", "")).strip()

            cat1 = str(row.get("cat_1", "")).strip()
            spec = str(row.get("regional_specificity", "")).strip()

            with st.container(border=True):
                st.markdown(f"**{row.get('author_short', '')} ({year_str})** — {challenge}")

                badges = []
                if cat1 and cat1 != "nan":
                    badges.append(badge(cat1, CAT1_COLORS.get(cat1, "#888888")))
                if spec and spec != "nan":
                    badges.append(badge(spec, SPECIFICITY_COLORS.get(spec, "#888888")))
                if badges:
                    st.markdown("&nbsp;&nbsp;".join(badges), unsafe_allow_html=True)

                with st.expander("Full citation"):
                    title_full = str(row.get("title_full", "")).strip()
                    citation = f"{row.get('author_short', '')} ({year_str}). *{title_full}*."
                    doi_url = to_doi_url(row.get("doi", ""))
                    if doi_url:
                        citation += f" [DOI]({doi_url})"
                    st.markdown(citation)

                    verbatim = str(row.get("verbatim_from_paper", "")).strip()
                    if verbatim and verbatim != "nan":
                        st.markdown("**Verbatim from paper:**")
                        for line in verbatim.replace("\r\n", "\n").split("\n"):
                            if line.strip():
                                st.markdown(f"> {line}")
                    else:
                        st.caption("No verbatim excerpt available.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Articles
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    df_articles = load_articles()
    st.subheader(f"Articles Reference ({len(df_articles)} articles)")
    filtered_art = render_article_filters(df_articles)

    st.caption(f"Showing **{len(filtered_art)}** of **{len(df_articles)}** articles")

    display_cols = [c for c in ["id", "quick_ref", "author_short", "year", "title", "language", "country_focus", "doi"] if c in filtered_art.columns]
    col_config = {}
    if "doi" in display_cols:
        # Normalize DOI values to full URLs
        if "doi" in filtered_art.columns:
            filtered_art = filtered_art.copy()
            filtered_art["doi"] = filtered_art["doi"].apply(
                lambda v: ("https://doi.org/" + str(v).strip()) if pd.notna(v) and str(v).strip() and not str(v).strip().startswith("http") else (str(v).strip() if pd.notna(v) and str(v).strip() else None)
            )
        col_config["doi"] = st.column_config.LinkColumn("DOI", display_text="↗")
    if "year" in display_cols:
        col_config["year"] = st.column_config.NumberColumn("Year", format="%d")
    if "title" in display_cols:
        col_config["title"] = st.column_config.TextColumn("Title", width="large")

    st.dataframe(
        filtered_art[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
        row_height=80,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Statistics
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    df_c = load_challenges()
    df_a = load_articles()

    total_challenges = len(df_c)
    total_articles   = len(df_a)

    pct_high = 0.0
    if total_challenges:
        pct_high = (df_c["regional_specificity"] == "High").sum() / total_challenges * 100

    # Key metrics row
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Challenges", total_challenges)
    k2.metric("Total Articles",   total_articles)
    k3.metric("High Regional Specificity", f"{pct_high:.0f}%")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_challenges_by_cat1(df_c), use_container_width=True)
    with c2:
        st.plotly_chart(chart_challenges_by_specificity(df_c), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(chart_top_challenges_by_articles(df_c), use_container_width=True)
    with c4:
        st.plotly_chart(chart_articles_by_year(df_a), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(chart_countries_cited(df_a), use_container_width=True)
    with c6:
        st.plotly_chart(map_countries_cited(df_a), use_container_width=True)

    with st.expander("Raw Statistics sheet"):
        stats_df = load_statistics_raw()
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — About
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    about_path = Path(__file__).parent / "content" / "about.md"
    st.markdown(about_path.read_text(encoding="utf-8"))

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")

st.caption(
    "Based on: García Sans, A. (2026). *AI governance challenges in Latin America.* "
    "Doctoral research, Universitat Oberta de Catalunya (UOC)."
)

st.markdown(
    "Contact: <agarcians@uoc.edu> · "
    "[ORCID](https://orcid.org/0009-0005-0652-7772) · "
    "[LinkedIn](https://www.linkedin.com/in/annagarciasans/)"
)
