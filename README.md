# SEMO Ireland Electricity Dashboard

A Streamlit web app for visualising Irish electricity market data:
- **5-minute Imbalance Prices** (from SEMO)
- **Hourly Day Ahead Market Prices** (from SEMOPX)
- **Aurora Merchant Curves** *(coming soon)*

---

## How to Deploy (Step-by-Step)

### Step 1 — Push this folder to a private GitHub repo

1. Go to [github.com](https://github.com) and create a **new private repository**
   (name it something like `semo-dashboard`)
2. On your computer, open **Git Bash** or a terminal inside this folder and run:
   ```
   git init
   git add .
   git commit -m "Initial dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/semo-dashboard.git
   git push -u origin main
   ```
   Replace `YOUR-USERNAME` with your GitHub username.

---

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **"New app"**
3. Select your `semo-dashboard` repository, branch `main`, file `app.py`
4. Click **"Deploy"** — the app will build automatically

---

### Step 3 — Add your BigQuery credentials (IMPORTANT)

The app needs your Google Cloud service account to read from BigQuery.
**Never put credentials in the code or commit them to GitHub.**

1. In Streamlit Cloud, go to your app → **Settings → Secrets**
2. Open your existing `service_account.json` file (in the SEMO_Scraper2 folder)
3. Paste the following into the Secrets box, filling in each value from `service_account.json`:

```toml
[gcp_service_account]
type                        = "service_account"
project_id                  = "semo-price-automation"
private_key_id              = "..."
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email                = "semo-bot@semo-price-automation.iam.gserviceaccount.com"
client_id                   = "..."
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "..."
```

4. Click **Save** — the app will restart with credentials loaded

---

### Step 4 — Share with your team

Once deployed, Streamlit gives you a URL like:
`https://your-app-name.streamlit.app`

Share this URL with your team. They can access it in any browser — no install needed.

To restrict access to specific email addresses (optional), go to **Settings → Sharing** in Streamlit Cloud and enable viewer authentication.

---

## Running Locally (Optional)

If you want to test the app on your own machine before deploying:

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create `.streamlit/secrets.toml` (copy from `secrets.toml.example` and fill in your credentials)

3. Run the app:
   ```
   streamlit run app.py
   ```

---

## Data Pipeline

The dashboard reads from your existing BigQuery tables. Your automated pipeline
(`semo_to_bigquery.py`) continues to run on its normal schedule — no changes needed.

| Table | Source | Granularity |
|---|---|---|
| `imbalance_prices_5min` | SEMO reports | 5-minute |
| `dam_prices_hourly` | SEMOPX | 1-hour |

---

## Adding Aurora (Future)

When you have the Aurora API details, the `tab_aurora` section in `app.py` is
ready to be filled in. Aurora credentials will be added to the Streamlit Secrets
in the same way as the BigQuery credentials.
