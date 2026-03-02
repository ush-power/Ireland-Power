"""
Daily SEMO data update — runs in GitHub Actions every morning.
Fetches yesterday's imbalance and DAM price data from SEMO/SEMOPX
and loads it into BigQuery. Safe to re-run: deletes then reinserts
data for the target date range to prevent duplicates.
"""

import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from google.cloud import bigquery
from google.oauth2 import service_account
import json

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ID   = "semo-price-automation"
DATASET_ID   = "semo_data"
IMB_TABLE_ID = "imbalance_prices_5min"
DAM_TABLE_ID = "dam_prices_hourly"

SEMO_BASE_URL   = "https://reports.sem-o.com/documents/"
SEMOPX_BASE_URL = "https://www.semopx.com/market-data/reports/static-reports/"

# Fetch the last 2 days to handle any gaps (safe to re-run)
today     = datetime.utcnow()
yesterday = today - timedelta(days=1)
two_days  = today - timedelta(days=2)

START_DATE = two_days.strftime("%Y-%m-%d")
END_DATE   = yesterday.strftime("%Y-%m-%d")

print(f"Running daily update: {START_DATE} to {END_DATE}")


# ============================================================================
# BIGQUERY CLIENT
# Credentials come from GOOGLE_APPLICATION_CREDENTIALS env var (set by
# GitHub Actions from the GCP_SERVICE_ACCOUNT secret).
# ============================================================================
def get_client():
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
    else:
        # Fallback: read JSON directly from env var
        creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json)
        )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


# ============================================================================
# HELPERS
# ============================================================================
def generate_time_codes():
    return [
        f"{h:02d}{m:02d}"
        for h in range(24)
        for m in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    ]


def fetch_xml(url, session):
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except Exception:
        pass
    return None


# ============================================================================
# DATA FETCHING (in-memory, no local file cache needed in CI)
# ============================================================================
def fetch_data(start_date, end_date):
    session   = requests.Session()
    imb_records = []
    dam_records = []

    current = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt  = datetime.strptime(end_date,   "%Y-%m-%d")

    while current <= end_dt:
        date_str     = current.strftime("%Y-%m-%d")
        date_nodash  = current.strftime("%Y%m%d")
        tomorrow     = (current + timedelta(days=1)).strftime("%Y%m%d")

        # --- DAM (T+1 file for this trade date) ---
        dam_filename = f"DAM_60MinHarmonisedReferencePrice_{tomorrow}.xml"
        dam_xml = fetch_xml(f"{SEMOPX_BASE_URL}{dam_filename}", session) or \
                  fetch_xml(f"{SEMOPX_BASE_URL}archive/{dam_filename}", session)

        if dam_xml:
            try:
                root = ET.fromstring(dam_xml)
                for elem in root:
                    dam_records.append(elem.attrib.copy())
            except Exception:
                pass

        # --- Imbalance (288 × 5-min files) ---
        for code in generate_time_codes():
            url = f"{SEMO_BASE_URL}PUB_5MinImbalPrc_{date_nodash}{code}.xml"
            xml = fetch_xml(url, session)
            if xml:
                try:
                    root = ET.fromstring(xml)
                    for elem in root:
                        imb_records.append(elem.attrib.copy())
                except Exception:
                    continue

        print(f"  Fetched {date_str}")
        current += timedelta(days=1)

    return pd.DataFrame(imb_records), pd.DataFrame(dam_records)


# ============================================================================
# BIGQUERY LOAD  (delete then insert to prevent duplicates)
# ============================================================================
def delete_date_range(client, table_id, start, end):
    full_id = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    client.query(f"""
        DELETE FROM `{full_id}`
        WHERE DATE(TradeDate) BETWEEN '{start}' AND '{end}'
    """).result()
    print(f"  Cleared {start} → {end} in {table_id}")


def upload(df, table_id, client):
    if df.empty:
        print(f"  No data for {table_id}")
        return

    for col in ["TradeDate", "StartTime", "EndTime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    for col in ["Price", "ImbalancePrice", "NetImbalanceVolume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    full_id    = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )
    client.load_table_from_dataframe(df, full_id, job_config=job_config).result()
    print(f"  Uploaded {len(df):,} rows to {table_id}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    client = get_client()

    imb_df, dam_df = fetch_data(START_DATE, END_DATE)

    # Remove existing rows for this period before inserting fresh data
    delete_date_range(client, IMB_TABLE_ID, START_DATE, END_DATE)
    delete_date_range(client, DAM_TABLE_ID, START_DATE, END_DATE)

    upload(imb_df, IMB_TABLE_ID, client)
    upload(dam_df, DAM_TABLE_ID, client)

    print("Daily update complete.")


if __name__ == "__main__":
    main()
