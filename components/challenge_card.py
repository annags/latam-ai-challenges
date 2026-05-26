import pandas as pd
import streamlit as st

CAT1_COLORS = {
    "Socio-technical": "#1D9E75",
    "Ethical":         "#D85A30",
    "Institutional":   "#7F77DD",
}

SPECIFICITY_STYLES = {
    "High":   "background:#27ae60;color:white",
    "Medium": "background:#f39c12;color:white",
    "Low":    "background:#95a5a6;color:white",
}


def _badge(label: str, style: str) -> str:
    return (
        f'<span style="border-radius:4px;padding:2px 8px;'
        f'font-size:0.72em;font-weight:600;{style}">{label}</span>'
    )


def render_challenge_card(row: pd.Series, col):
    cat1 = str(row.get("cat_1", "")).strip()
    cat_color = CAT1_COLORS.get(cat1, "#888888")
    spec = str(row.get("regional_specificity", "")).strip()
    spec_style = SPECIFICITY_STYLES.get(spec, "background:#ccc;color:#333")
    title = str(row.get("title_en", "")).strip()
    quick_ref = str(row.get("quick_ref_en", "")).strip()
    article_count = row.get("article_count", 0)
    row_id = str(row.get("id", "")).strip()

    with col:
        with st.container(border=True):
            st.markdown(
                f"""<div style="border-left:4px solid {cat_color};padding-left:10px;margin-bottom:4px;">
  {_badge(cat1, f"background:{cat_color};color:white")}
  <p style="margin:6px 0 4px 0;font-weight:600;font-size:0.97em;line-height:1.3">{title}</p>
  <p style="margin:0;font-size:0.82em;color:#555;line-height:1.4">{quick_ref}</p>
  <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
    {_badge(spec, spec_style)}
    <span style="font-size:0.78em;color:#777">{article_count} article{'s' if article_count != 1 else ''} &middot; ID&nbsp;{row_id}</span>
  </div>
</div>""",
                unsafe_allow_html=True,
            )

            with st.expander("Full detail"):
                desc = str(row.get("description_en", "")).strip()
                if desc and desc != "nan":
                    st.markdown("**Description**")
                    st.write(desc)

                rationale = str(row.get("regional_rationale", "")).strip()
                if rationale and rationale != "nan":
                    st.markdown("**Regional Rationale**")
                    st.write(rationale)

                wirtz = str(row.get("wirtz_mapping", "")).strip()
                if wirtz and wirtz != "nan":
                    st.markdown(f"**Wirtz Mapping:** {wirtz}")

                countries = str(row.get("countries_mentioned", "")).strip()
                if countries and countries != "nan":
                    st.markdown(f"**Countries mentioned:** {countries}")

                first_year = row.get("first_year_cited")
                if pd.notna(first_year):
                    st.markdown(f"**First cited:** {int(first_year)}")

                key_arts = str(row.get("key_articles", "")).strip()
                if key_arts and key_arts != "nan":
                    st.markdown("**Key articles (see Articles tab):**")
                    for art_id in key_arts.split(","):
                        art_id = art_id.strip()
                        if art_id:
                            st.markdown(f"- Article {art_id}")


def render_challenge_grid(df: pd.DataFrame):
    if df.empty:
        st.info("No challenges match the current filters.")
        return

    records = df.to_dict("records")
    for i in range(0, len(records), 3):
        cols = st.columns(3)
        for j, rec in enumerate(records[i : i + 3]):
            render_challenge_card(pd.Series(rec), cols[j])
