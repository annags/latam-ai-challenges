import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CAT1_COLORS = {
    "Socio-technical": "#1D9E75",
    "Ethical":         "#D85A30",
    "Institutional":   "#7F77DD",
}

SPEC_COLORS = {
    "High":   "#27ae60",
    "Medium": "#f39c12",
    "Low":    "#95a5a6",
}

_LAYOUT = dict(plot_bgcolor="white", paper_bgcolor="white", font_family="sans-serif")


def chart_challenges_by_cat1(df: pd.DataFrame) -> go.Figure:
    counts = df["cat_1"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    fig = px.bar(
        counts, x="Category", y="Count",
        color="Category",
        color_discrete_map=CAT1_COLORS,
        title="Challenges by Category",
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, **_LAYOUT)
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig


def chart_challenges_by_specificity(df: pd.DataFrame) -> go.Figure:
    order = ["High", "Medium", "Low"]
    counts = (
        df["regional_specificity"]
        .value_counts()
        .reindex(order, fill_value=0)
        .reset_index()
    )
    counts.columns = ["Specificity", "Count"]
    fig = px.bar(
        counts, x="Specificity", y="Count",
        color="Specificity",
        color_discrete_map=SPEC_COLORS,
        title="Challenges by Regional Specificity",
        category_orders={"Specificity": order},
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, **_LAYOUT)
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig


def chart_top_challenges_by_articles(df: pd.DataFrame) -> go.Figure:
    top = df.nlargest(10, "article_count").sort_values("article_count")
    # Truncate long titles for readability
    top = top.copy()
    top["label"] = top["title_en"].str[:55] + top["title_en"].str[55:].apply(
        lambda s: "…" if s else ""
    )
    fig = px.bar(
        top,
        x="article_count", y="label",
        orientation="h",
        color="cat_1",
        color_discrete_map=CAT1_COLORS,
        title="Top 10 Challenges by Article Count",
        labels={"article_count": "Articles", "label": "Challenge"},
        text="article_count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=True,
        legend_title="Category",
        yaxis={"categoryorder": "total ascending"},
        **_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#eeeeee")
    return fig


def chart_articles_by_year(df_articles: pd.DataFrame) -> go.Figure:
    years = df_articles["year"].dropna().astype(int)
    counts = years.value_counts().sort_index().reset_index()
    counts.columns = ["Year", "Count"]
    fig = px.bar(
        counts, x="Year", y="Count",
        title="Articles by Publication Year",
        color_discrete_sequence=["#1D9E75"],
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(dtick=1, tickangle=-45, gridcolor="#eeeeee")
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig
