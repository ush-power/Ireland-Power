import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from google.oauth2 import service_account
from google.cloud import bigquery

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="SEMO Ireland Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# BIGQUERY CONNECTION
# Uses credentials stored in .streamlit/secrets.toml (never committed to Git)
# ============================================================================
@st.cache_resource
def get_bq_client():
    """Create and cache a BigQuery client for the session."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return bigquery.Client(credentials=credentials, project="semo-price-automation")


# ============================================================================
# DATA FETCHING  (results cached for 1 hour to avoid redundant BigQuery calls)
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_imbalance(start: str, end: str) -> pd.DataFrame:
    """Fetch 5-minute imbalance pricing data from BigQuery."""
    query = f"""
        SELECT
            StartTime,
            CAST(ImbalancePrice      AS FLOAT64) AS ImbalancePrice,
            CAST(NetImbalanceVolume  AS FLOAT64) AS NetImbalanceVolume
        FROM `semo-price-automation.semo_data.imbalance_prices_5min`
        WHERE DATE(TradeDate) BETWEEN '{start}' AND '{end}'
        ORDER BY StartTime
    """
    df = get_bq_client().query(query).to_dataframe()
    # Strip timezone so Plotly renders cleanly
    df["StartTime"] = pd.to_datetime(df["StartTime"])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dam(start: str, end: str) -> pd.DataFrame:
    """Fetch hourly Day Ahead Market pricing data from BigQuery."""
    query = f"""
        SELECT
            StartTime,
            CAST(Price AS FLOAT64) AS Price
        FROM `semo-price-automation.semo_data.dam_prices_hourly`
        WHERE DATE(TradeDate) BETWEEN '{start}' AND '{end}'
        ORDER BY StartTime
    """
    df = get_bq_client().query(query).to_dataframe()
    df["StartTime"] = pd.to_datetime(df["StartTime"])
    return df


# ============================================================================
# HELPER: SUMMARY METRIC ROW
# ============================================================================
def show_metrics(series: pd.Series, label: str, unit: str = "EUR/MWh"):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Avg {label}", f"€{series.mean():.2f}/{unit.split('/')[-1]}")
    c2.metric(f"Peak {label}", f"€{series.max():.2f}/{unit.split('/')[-1]}")
    c3.metric(f"Min {label}", f"€{series.min():.2f}/{unit.split('/')[-1]}")
    c4.metric("Std Dev", f"€{series.std():.2f}/{unit.split('/')[-1]}")


# ============================================================================
# SIDEBAR – DATE RANGE PICKER
# ============================================================================
with st.sidebar:
    st.title("⚡ SEMO Dashboard")
    st.caption("Ireland Electricity Market")
    st.divider()

    st.subheader("Select Date Range")
    yesterday  = date.today() - timedelta(days=1)
    data_start = date(2025, 1, 1)   # Earliest date in BigQuery

    date_from, date_to = st.slider(
        "Date range",
        min_value=data_start,
        max_value=yesterday,
        value=(yesterday - timedelta(days=6), yesterday),
        format="DD MMM YYYY",
        label_visibility="collapsed",
    )

    days_selected = (date_to - date_from).days + 1
    st.caption(f"**{date_from.strftime('%d %b %Y')}** → **{date_to.strftime('%d %b %Y')}**  ({days_selected} days)")
    st.divider()
    st.caption("Query results cached for 1 hour.")
    st.caption("Data updated daily via automated pipeline.")

start_str = date_from.strftime("%Y-%m-%d")
end_str   = date_to.strftime("%Y-%m-%d")

# ============================================================================
# PAGE HEADER
# ============================================================================
st.title("Ireland Electricity Market Dashboard")
st.caption(
    f"Showing data from **{date_from.strftime('%d %b %Y')}** "
    f"to **{date_to.strftime('%d %b %Y')}**"
)

# ============================================================================
# TABS
# ============================================================================
tab_imb, tab_dam, tab_comp, tab_aurora = st.tabs([
    "⚡ Imbalance Prices",
    "📈 Day Ahead Prices",
    "🔄 Comparison",
    "🌐 Aurora",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — IMBALANCE PRICES
# ─────────────────────────────────────────────────────────────────────────────
with tab_imb:
    with st.spinner("Fetching imbalance data…"):
        imb_df = fetch_imbalance(start_str, end_str)

    if imb_df.empty:
        st.warning("No imbalance data found for the selected date range.")
    else:
        show_metrics(imb_df["ImbalancePrice"], "Price")
        st.divider()

        # Price chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=imb_df["StartTime"],
            y=imb_df["ImbalancePrice"],
            mode="lines",
            name="Imbalance Price",
            line=dict(color="#e85d04", width=1),
            hovertemplate="%{x|%d %b %H:%M}<br><b>€%{y:.2f}/MWh</b><extra></extra>",
        ))
        fig.update_layout(
            title="5-Minute Imbalance Price (EUR/MWh)",
            xaxis_title="Time",
            yaxis_title="Price (EUR/MWh)",
            hovermode="x unified",
            height=430,
            xaxis=dict(rangeslider=dict(visible=True)),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Net imbalance volume chart
        colours = imb_df["NetImbalanceVolume"].apply(
            lambda v: "#2d6a4f" if v >= 0 else "#d62828"
        )
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=imb_df["StartTime"],
            y=imb_df["NetImbalanceVolume"],
            name="Net Imbalance Volume",
            marker_color=colours,
            hovertemplate="%{x|%d %b %H:%M}<br><b>%{y:.1f} MWh</b><extra></extra>",
        ))
        fig2.update_layout(
            title="Net Imbalance Volume (MWh)  —  green = long, red = short",
            xaxis_title="Time",
            yaxis_title="Volume (MWh)",
            hovermode="x unified",
            height=300,
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.download_button(
            "⬇ Download as CSV",
            data=imb_df.to_csv(index=False),
            file_name=f"imbalance_{start_str}_to_{end_str}.csv",
            mime="text/csv",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — DAY AHEAD PRICES
# ─────────────────────────────────────────────────────────────────────────────
with tab_dam:
    with st.spinner("Fetching DAM data…"):
        dam_df = fetch_dam(start_str, end_str)

    if dam_df.empty:
        st.warning("No DAM data found for the selected date range.")
    else:
        show_metrics(dam_df["Price"], "Price")
        st.divider()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dam_df["StartTime"],
            y=dam_df["Price"],
            mode="lines+markers",
            name="DAM Price",
            line=dict(color="#0077b6", width=2),
            marker=dict(size=4),
            hovertemplate="%{x|%d %b %H:%M}<br><b>€%{y:.2f}/MWh</b><extra></extra>",
        ))
        fig.update_layout(
            title="Day Ahead Market — Harmonised Reference Price (EUR/MWh)",
            xaxis_title="Time",
            yaxis_title="Price (EUR/MWh)",
            hovermode="x unified",
            height=450,
            xaxis=dict(rangeslider=dict(visible=True)),
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "⬇ Download as CSV",
            data=dam_df.to_csv(index=False),
            file_name=f"dam_{start_str}_to_{end_str}.csv",
            mime="text/csv",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — COMPARISON
# ─────────────────────────────────────────────────────────────────────────────
with tab_comp:
    # Data already cached from tabs above — no extra BigQuery cost
    with st.spinner("Building comparison…"):
        imb_comp = fetch_imbalance(start_str, end_str)
        dam_comp  = fetch_dam(start_str, end_str)

    if imb_comp.empty and dam_comp.empty:
        st.warning("No data found for the selected date range.")
    else:
        fig = go.Figure()

        if not imb_comp.empty:
            # Resample 5-min imbalance to hourly average for a clean overlay
            imb_hourly = (
                imb_comp.set_index("StartTime")
                .resample("1h")["ImbalancePrice"]
                .mean()
                .reset_index()
            )
            fig.add_trace(go.Scatter(
                x=imb_hourly["StartTime"],
                y=imb_hourly["ImbalancePrice"],
                mode="lines",
                name="Imbalance Price (hourly avg)",
                line=dict(color="#e85d04", width=2),
                hovertemplate="%{x|%d %b %H:%M}<br><b>€%{y:.2f}/MWh</b><extra></extra>",
            ))

        if not dam_comp.empty:
            fig.add_trace(go.Scatter(
                x=dam_comp["StartTime"],
                y=dam_comp["Price"],
                mode="lines+markers",
                name="DAM Price",
                line=dict(color="#0077b6", width=2),
                marker=dict(size=4),
                hovertemplate="%{x|%d %b %H:%M}<br><b>€%{y:.2f}/MWh</b><extra></extra>",
            ))

        fig.update_layout(
            title="Imbalance vs Day Ahead Market Price (EUR/MWh)",
            xaxis_title="Time",
            yaxis_title="Price (EUR/MWh)",
            hovermode="x unified",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(rangeslider=dict(visible=True)),
            margin=dict(t=60, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Side-by-side summary stats
        if not imb_comp.empty and not dam_comp.empty:
            st.subheader("Summary Statistics")
            stats = pd.DataFrame({
                "Metric": ["Average", "Peak", "Minimum", "Std Dev"],
                "Imbalance Price (€/MWh)": [
                    f"{imb_comp['ImbalancePrice'].mean():.2f}",
                    f"{imb_comp['ImbalancePrice'].max():.2f}",
                    f"{imb_comp['ImbalancePrice'].min():.2f}",
                    f"{imb_comp['ImbalancePrice'].std():.2f}",
                ],
                "DAM Price (€/MWh)": [
                    f"{dam_comp['Price'].mean():.2f}",
                    f"{dam_comp['Price'].max():.2f}",
                    f"{dam_comp['Price'].min():.2f}",
                    f"{dam_comp['Price'].std():.2f}",
                ],
            })
            st.dataframe(stats, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — AURORA (PLACEHOLDER)
# ─────────────────────────────────────────────────────────────────────────────
with tab_aurora:
    st.info("**Aurora Energy Research — Merchant Curve Integration**  \nComing soon.")
    st.markdown("""
Once the Aurora API is configured, this tab will show:

- **Forward price curves** (baseload and peak, multiple horizons)
- **Aurora forecast vs SEMO actuals** — side-by-side comparison
- **Scenario analysis** — central, high, and low merchant curves
- **Downloadable curve data** for use in financial models

---
To set up the Aurora integration, share the API documentation and endpoint
details with your development team. Credentials will be stored securely in
the same Streamlit secrets vault as the BigQuery credentials.
    """)
