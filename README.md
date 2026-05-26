# LATAM AI Governance Challenges Repository

A browsable, searchable web app for exploring AI governance challenges in Latin America, derived from a systematic literature review of 38 peer-reviewed and grey-literature articles (2021–2026).

**Based on:** García Sans, A. (2026). *AI governance challenges in Latin America.* Doctoral research, UOC.

---

## Quick start (local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up credentials (see below)

# 3. Run the app
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Credentials setup

The app connects to Google Drive via a service account. Two options:

### Option A — `credentials.json` (simplest for local dev)

Place your service account JSON file at the project root as `credentials.json`. It is gitignored automatically.

### Option B — `.streamlit/secrets.toml` (required for Streamlit Cloud)

Edit `.streamlit/secrets.toml` (already created as a template) and fill in the fields from your service account JSON:

```toml
[gcp_service_account]
type = "service_account"
project_id = "gen-lang-client-0246752153"
private_key_id = "YOUR_KEY_ID"
private_key = "-----BEGIN RSA PRIVATE KEY-----\nYOUR_KEY\n-----END RSA PRIVATE KEY-----\n"
client_email = "ai-challenges-repo@gen-lang-client-0246752153.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
universe_domain = "googleapis.com"
```

> **Important:** The `private_key` value must keep literal `\n` characters (not real newlines). Copy-paste directly from the JSON file.

---

## Streamlit Cloud deployment

1. Push the repository to GitHub (`.streamlit/secrets.toml` and `credentials.json` are gitignored — do not commit them).
2. Connect the repo to [share.streamlit.io](https://share.streamlit.io).
3. In the app settings → **Secrets**, paste the `[gcp_service_account]` block from your secrets.toml.
4. Deploy.

---

## Local fallback (no Drive credentials)

If Drive credentials are not configured, the app falls back to a local file:

```
data/LATAM_AI_Challenges_Repository.xlsx
```

Place the Excel file there and the app will load it with a warning banner.

---

## Project structure

```
app.py                          # Main Streamlit app, tab routing
drive_connector.py              # Google Drive auth + download + fallback
data_loader.py                  # Excel parsing, per-sheet loaders, caching
components/
    __init__.py
    challenge_card.py           # Card + grid rendering
    filters.py                  # Sidebar and inline filter widgets
    charts.py                   # Plotly chart functions
requirements.txt
.streamlit/
    secrets.toml                # Local secrets (gitignored)
data/
    LATAM_AI_Challenges_Repository.xlsx   # Local fallback (optional)
```

---

## Data source

Google Drive Excel file — 4 sheets:

| Sheet | Rows | Description |
|---|---|---|
| Challenges Repository | 21 | Master challenge list |
| Challenges by Paper | 128 | Challenge–paper cross-references with verbatim excerpts |
| Articles Reference | 38 | Full article list |
| Statistics | — | Summary tables |

Data is cached for 1 hour (`ttl=3600`). Use the **Refresh data** button in the sidebar to force a reload.
