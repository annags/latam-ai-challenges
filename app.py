import pandas as pd
import streamlit as st

from data_loader import load_challenges, load_articles, load_by_paper, load_statistics_raw
from components.filters import (
    render_sidebar_filters,
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
)
from components.network_graph import render_network_graph, render_legend

st.set_page_config(
    page_title="LATAM AI Repository",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      footer { visibility: hidden; }
      [data-testid="stSidebar"] { min-width: 240px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("LATAM AI Governance Challenges Repository")
st.caption(
    "Systematic literature review of 38 peer-reviewed and grey-literature articles (2021–2026)"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Repository", "📄 By Paper", "📚 Articles", "📊 Statistics", "🕸️ Mapa de Relaciones"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Repository
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    df_challenges = load_challenges()
    selected_cat1, selected_spec, search_text = render_sidebar_filters(df_challenges)
    filtered = apply_challenge_filters(df_challenges, selected_cat1, selected_spec, search_text)

    st.caption(f"Showing **{len(filtered)}** of **{len(df_challenges)}** challenges")
    render_challenge_grid(filtered)

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
        for _, row in filtered_bp.iterrows():
            year_str = f"{int(row['year'])}" if pd.notna(row.get("year")) else "n.d."
            cat_label = f" [{row['cat_1']}]" if pd.notna(row.get("cat_1")) and str(row.get("cat_1")).strip() else ""
            header = (
                f"**{row.get('author_short', '')} ({year_str})** — "
                f"{row.get('title_short', '')}{cat_label}"
            )
            with st.expander(header):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(
                        f"**Challenge:** {row.get('title_en', '')}  \n"
                        f"*{row.get('quick_ref_en', '')}*"
                    )
                with c2:
                    spec = str(row.get("regional_specificity", "")).strip()
                    if spec and spec != "nan":
                        st.markdown(f"**Regional specificity:** {spec}")

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

    display_cols = [c for c in ["id", "author_short", "year", "title_short", "type", "language", "country_focus", "doi"] if c in filtered_art.columns]
    col_config = {}
    if "doi" in display_cols:
        col_config["doi"] = st.column_config.LinkColumn("DOI", display_text="Link")
    if "year" in display_cols:
        col_config["year"] = st.column_config.NumberColumn("Year", format="%d")

    st.dataframe(
        filtered_art[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
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

    most_cited = "N/A"
    if not df_c.empty and "article_count" in df_c.columns:
        idx = df_c["article_count"].idxmax()
        most_cited = str(df_c.loc[idx, "title_en"])

    # Key metrics row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Challenges", total_challenges)
    k2.metric("Total Articles",   total_articles)
    k3.metric("High Regional Specificity", f"{pct_high:.0f}%")
    label = most_cited[:32] + "…" if len(most_cited) > 32 else most_cited
    k4.metric("Most Cited Challenge", label)

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

    with st.expander("Raw Statistics sheet"):
        stats_df = load_statistics_raw()
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Mapa de Relaciones
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    df_net_c  = load_challenges()
    df_net_a  = load_articles()
    df_net_bp = load_by_paper()

    st.subheader("Mapa de relaciones: retos ↔ artículos")
    st.markdown(
        "Cada **círculo** es un reto — color = categoría, tamaño = nº artículos que lo citan. "
        "Cada **cuadrado azul** es un artículo. "
        "Los filtros, la leyenda y el botón de **pantalla completa** están dentro del grafo."
    )
    render_network_graph(
        df_by_paper=df_net_bp,
        df_challenges=df_net_c,
        df_articles=df_net_a,
    )

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Based on: García Sans, A. (2026). *AI governance challenges in Latin America.* "
    "Doctoral research, UOC."
)
