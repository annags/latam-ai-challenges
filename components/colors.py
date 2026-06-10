CAT1_COLORS = {
    "Socio-technical": "#7F77DD",
    "Ethical":         "#00BF63",
    "Institutional":   "#004AAD",
}

SPECIFICITY_COLORS = {
    "High":   "#ff3131",
    "Medium": "#fa6767",
    "Low":    "#f69696",
}


def badge(label: str, bg: str, text_color: str = "white") -> str:
    return (
        f'<span style="border-radius:4px;padding:2px 8px;'
        f'font-size:0.72em;font-weight:600;background:{bg};color:{text_color}">{label}</span>'
    )


def to_doi_url(doi: str) -> str | None:
    """Returns a normalized https://doi.org/... URL, or None if doi is empty/placeholder."""
    doi = str(doi).strip()
    if not doi or doi == "nan" or not any(c.isalnum() for c in doi):
        return None
    if not doi.startswith("http"):
        doi = f"https://doi.org/{doi}"
    return doi
