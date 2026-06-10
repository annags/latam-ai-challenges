import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.colors import CAT1_COLORS, SPECIFICITY_COLORS

SPEC_CHART_COLORS = SPECIFICITY_COLORS

_LAYOUT = dict(plot_bgcolor="white", paper_bgcolor="white", font_family="sans-serif")

LATAM_COUNTRIES = {
    "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica",
    "Cuba", "Dominican Republic", "Ecuador", "El Salvador", "Guatemala",
    "Honduras", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru",
    "Uruguay", "Venezuela",
}


def chart_challenges_by_cat1(df: pd.DataFrame) -> go.Figure:
    counts = df["cat_1"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    fig = px.pie(
        counts,
        names="Category",
        values="Count",
        color="Category",
        color_discrete_map=CAT1_COLORS,
        title="Challenges by Category",
    )
    fig.update_traces(textinfo="percent+label", textposition="inside")
    fig.update_layout(**_LAYOUT)
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
    fig = px.pie(
        counts,
        names="Specificity",
        values="Count",
        color="Specificity",
        color_discrete_map=SPEC_CHART_COLORS,
        title="Challenges by Regional Specificity",
        category_orders={"Specificity": order},
    )
    fig.update_traces(textinfo="percent+label", textposition="inside")
    fig.update_layout(**_LAYOUT)
    return fig


def chart_top_challenges_by_articles(df: pd.DataFrame) -> go.Figure:
    top = df.nlargest(10, "article_count").sort_values("article_count")
    top = top.copy()
    top["label"] = top["cat_2_en"].str[:55] + top["cat_2_en"].str[55:].apply(
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
        legend=dict(
            title="Category",
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        yaxis={"categoryorder": "total ascending"},
        margin=dict(b=90),
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
        color_discrete_sequence=["#004AAD"],
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(dtick=1, tickangle=-45, gridcolor="#eeeeee")
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig


def _latam_country_counts(df_articles: pd.DataFrame) -> pd.DataFrame:
    """Counts mentions of LATAM countries in `country_focus`, dropping
    continent-level entries (e.g. 'Latin America', 'South America') and
    non-LATAM countries (e.g. 'Canada', 'USA')."""
    if "country_focus" not in df_articles.columns:
        return pd.DataFrame(columns=["Country", "Count"])
    all_countries = []
    for val in df_articles["country_focus"].dropna():
        for c in str(val).split(","):
            c = c.strip()
            if c in LATAM_COUNTRIES:
                all_countries.append(c)
    if not all_countries:
        return pd.DataFrame(columns=["Country", "Count"])
    counts = pd.Series(all_countries).value_counts().reset_index()
    counts.columns = ["Country", "Count"]
    return counts


def chart_countries_cited(df_articles: pd.DataFrame) -> go.Figure:
    counts = _latam_country_counts(df_articles)
    if counts.empty:
        return go.Figure()
    fig = px.bar(
        counts, x="Country", y="Count",
        title="LATAM countries cited in the corpus",
        color_discrete_sequence=["#004AAD"],
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(tickangle=-45, gridcolor="#eeeeee")
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig


def map_countries_cited(df_articles: pd.DataFrame) -> go.Figure:
    counts = _latam_country_counts(df_articles)
    if counts.empty:
        return go.Figure()
    fig = px.choropleth(
        counts,
        locations="Country",
        locationmode="country names",
        color="Count",
        color_continuous_scale=["#eef2fb", "#004AAD"],
        title="LATAM countries cited — map",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(**_LAYOUT)
    return fig
