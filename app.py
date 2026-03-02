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
    page_title="Ireland Power Market | Highfield Energy",
    page_icon="assets/favicon.png" if False else "⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# STYLING
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #f0f4f8; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Main content area ── */
.block-container {
    padding: 2rem 2.5rem 2rem !important;
    max-width: 1440px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0c1f3d !important;
    border-right: none !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stMarkdown {
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1e3a5f !important;
    margin: 1.2rem 0 !important;
}
/* Slider track */
[data-testid="stSidebar"] [data-testid="stSlider"] div[data-baseweb="slider"] div {
    background: #1e3a5f !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e2e8f0 !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important;
    padding: 0 24px !important;
    height: 46px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    letter-spacing: 0.01em !important;
}
.stTabs [aria-selected="true"] {
    color: #1d4ed8 !important;
    border-bottom: 3px solid #1d4ed8 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
    background: transparent !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: white !important;
    color: #1d4ed8 !important;
    border: 1.5px solid #1d4ed8 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 6px 18px !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #eff6ff !important;
    box-shadow: 0 2px 8px rgba(29,78,216,0.15) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #1d4ed8 !important; }

/* ── Warning / info ── */
.stAlert {
    border-radius: 10px !important;
    font-size: 13px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# BIGQUERY CONNECTION
# ============================================================================
@st.cache_resource
def get_bq_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return bigquery.Client(credentials=credentials, project="semo-price-automation")


# ============================================================================
# DATA FETCHING
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_imbalance(start: str, end: str) -> pd.DataFrame:
    query = f"""
        SELECT
            StartTime,
            CAST(ImbalancePrice     AS FLOAT64) AS ImbalancePrice,
            CAST(NetImbalanceVolume AS FLOAT64) AS NetImbalanceVolume
        FROM `semo-price-automation.semo_data.imbalance_prices_5min`
        WHERE DATE(TradeDate) BETWEEN '{start}' AND '{end}'
        ORDER BY StartTime
    """
    df = get_bq_client().query(query).to_dataframe()
    df["StartTime"] = pd.to_datetime(df["StartTime"])
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dam(start: str, end: str) -> pd.DataFrame:
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
# UI COMPONENTS
# ============================================================================
def kpi_card(label: str, value: str, sub: str = "", accent: str = "#1d4ed8") -> str:
    return f"""
    <div style="
        background:#ffffff;
        border:1px solid #e2e8f0;
        border-top:3px solid {accent};
        border-radius:10px;
        padding:20px 22px 16px;
        box-shadow:0 1px 4px rgba(15,23,42,0.06);
        height:100%;
    ">
        <p style="margin:0;font-size:11px;font-weight:600;color:#94a3b8;
                  text-transform:uppercase;letter-spacing:0.07em">{label}</p>
        <p style="margin:10px 0 0;font-size:26px;font-weight:700;
                  color:#0f172a;line-height:1.1;font-variant-numeric:tabular-nums">{value}</p>
        <p style="margin:6px 0 0;font-size:12px;color:#64748b">{sub}</p>
    </div>"""


def kpi_row(series: pd.Series, label: str):
    avg  = series.mean()
    peak = series.max()
    low  = series.min()
    std  = series.std()
    cols = st.columns(4)
    cols[0].markdown(kpi_card("Average Price",    f"€{avg:.2f}", "EUR / MWh", "#1d4ed8"), unsafe_allow_html=True)
    cols[1].markdown(kpi_card("Peak Price",       f"€{peak:.2f}", "EUR / MWh", "#7c3aed"), unsafe_allow_html=True)
    cols[2].markdown(kpi_card("Minimum Price",    f"€{low:.2f}", "EUR / MWh", "#0d9488"), unsafe_allow_html=True)
    cols[3].markdown(kpi_card("Std Deviation",    f"€{std:.2f}", "EUR / MWh", "#f59e0b"), unsafe_allow_html=True)


def chart_layout(title: str, y_label: str, height: int = 420, rangeslider: bool = True) -> dict:
    """Returns a consistent professional Plotly layout."""
    return dict(
        title=dict(text=title, font=dict(size=14, color="#0f172a", family="Inter"), x=0, xanchor="left"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, -apple-system, sans-serif", color="#374151", size=12),
        xaxis=dict(
            gridcolor="#f1f5f9", gridwidth=1,
            linecolor="#e2e8f0", tickcolor="#cbd5e1",
            tickfont=dict(size=11, color="#64748b"),
            title_text="",
            zeroline=False,
            rangeslider=dict(visible=rangeslider, thickness=0.04, bgcolor="#f8fafc"),
        ),
        yaxis=dict(
            gridcolor="#f1f5f9", gridwidth=1,
            linecolor="#e2e8f0", tickcolor="#cbd5e1",
            tickfont=dict(size=11, color="#64748b"),
            title_text=y_label,
            title_font=dict(size=11, color="#94a3b8"),
            zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white", bordercolor="#e2e8f0",
            font=dict(size=12, color="#0f172a", family="Inter"),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0)", borderwidth=0,
            font=dict(size=12),
        ),
        margin=dict(t=50, b=10, l=10, r=10),
        height=height,
    )


def section_divider():
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:0 0 8px">
        <p style="margin:0;font-size:11px;font-weight:600;color:#4a6fa5;
                  text-transform:uppercase;letter-spacing:0.1em">Highfield Energy</p>
        <h2 style="margin:6px 0 0;font-size:20px;font-weight:700;color:#ffffff;line-height:1.2">
            Ireland Power<br>Market
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("<p style='margin:0 0 10px;font-size:12px;font-weight:600;color:#cbd5e1;text-transform:uppercase;letter-spacing:0.07em'>Date Range</p>", unsafe_allow_html=True)

    yesterday  = date.today() - timedelta(days=1)
    data_start = date(2025, 1, 1)

    date_from, date_to = st.slider(
        "Date range",
        min_value=data_start,
        max_value=yesterday,
        value=(yesterday - timedelta(days=6), yesterday),
        format="DD MMM YYYY",
        label_visibility="collapsed",
    )

    days_selected = (date_to - date_from).days + 1
    st.markdown(f"""
    <div style="background:#1e3a5f;border-radius:8px;padding:10px 14px;margin-top:10px">
        <p style="margin:0;font-size:12px;color:#94a3b8">{date_from.strftime('%d %b %Y')} → {date_to.strftime('%d %b %Y')}</p>
        <p style="margin:4px 0 0;font-size:13px;font-weight:600;color:#ffffff">{days_selected} day{'s' if days_selected != 1 else ''} selected</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="padding:0 0 4px">
        <p style="margin:0 0 6px;font-size:11px;color:#64748b">Data Sources</p>
        <p style="margin:0 0 4px;font-size:12px;color:#94a3b8">⚡ SEMO — Imbalance Pricing</p>
        <p style="margin:0 0 4px;font-size:12px;color:#94a3b8">📈 SEMOPX — Day Ahead Market</p>
        <p style="margin:0;font-size:12px;color:#4a6fa5">🌐 Aurora — Coming Soon</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<p style='margin:0;font-size:11px;color:#334155'>Updated daily · Queries cached 1 hr</p>", unsafe_allow_html=True)


start_str = date_from.strftime("%Y-%m-%d")
end_str   = date_to.strftime("%Y-%m-%d")


# ============================================================================
# PAGE HEADER
# ============================================================================
st.markdown(f"""
<div style="
    background:white;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:24px 28px;
    margin-bottom:24px;
    box-shadow:0 1px 4px rgba(15,23,42,0.05);
    display:flex;
    align-items:center;
    justify-content:space-between;
">
    <div>
        <p style="margin:0;font-size:11px;font-weight:600;color:#94a3b8;
                  text-transform:uppercase;letter-spacing:0.1em">Highfield Energy</p>
        <h1 style="margin:6px 0 4px;font-size:22px;font-weight:700;color:#0f172a">
            Ireland Power Market Dashboard
        </h1>
        <p style="margin:0;font-size:13px;color:#64748b">
            SEMO Imbalance Pricing &amp; Day Ahead Market — Ireland
        </p>
    </div>
    <div style="text-align:right">
        <p style="margin:0;font-size:11px;color:#94a3b8;text-transform:uppercase;
                  letter-spacing:0.07em;font-weight:600">Selected Period</p>
        <p style="margin:6px 0 0;font-size:16px;font-weight:700;color:#0f172a">
            {date_from.strftime('%d %b %Y')} &nbsp;→&nbsp; {date_to.strftime('%d %b %Y')}
        </p>
        <p style="margin:4px 0 0;font-size:12px;color:#64748b">{days_selected} day{'s' if days_selected != 1 else ''}</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# TABS
# ============================================================================
tab_imb, tab_dam, tab_comp, tab_aurora = st.tabs([
    "  Imbalance Prices  ",
    "  Day Ahead Prices  ",
    "  Comparison  ",
    "  Aurora  ",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — IMBALANCE PRICES
# ─────────────────────────────────────────────────────────────────────────────
with tab_imb:
    with st.spinner("Loading imbalance data…"):
        imb_df = fetch_imbalance(start_str, end_str)

    if imb_df.empty:
        st.warning("No imbalance data found for the selected date range.")
    else:
        kpi_row(imb_df["ImbalancePrice"], "Imbalance Price")
        section_divider()

        # Price chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=imb_df["StartTime"],
            y=imb_df["ImbalancePrice"],
            mode="lines",
            name="Imbalance Price",
            line=dict(color="#1d4ed8", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(29,78,216,0.05)",
            hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>€%{y:.2f} / MWh<extra></extra>",
        ))
        fig.update_layout(**chart_layout("5-Minute Imbalance Price", "EUR / MWh", height=420))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        section_divider()

        # Volume chart
        vol_colours = imb_df["NetImbalanceVolume"].apply(
            lambda v: "#0d9488" if v >= 0 else "#dc2626"
        )
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=imb_df["StartTime"],
            y=imb_df["NetImbalanceVolume"],
            name="Net Imbalance Volume",
            marker_color=vol_colours,
            hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>%{y:.1f} MWh<extra></extra>",
        ))
        fig2.update_layout(**chart_layout(
            "Net Imbalance Volume  —  Teal = System Long  ·  Red = System Short",
            "MWh", height=280, rangeslider=False,
        ))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        section_divider()
        st.download_button(
            "↓  Export Imbalance Data (CSV)",
            data=imb_df.to_csv(index=False),
            file_name=f"imbalance_{start_str}_to_{end_str}.csv",
            mime="text/csv",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — DAY AHEAD PRICES
# ─────────────────────────────────────────────────────────────────────────────
with tab_dam:
    with st.spinner("Loading DAM data…"):
        dam_df = fetch_dam(start_str, end_str)

    if dam_df.empty:
        st.warning("No DAM data found for the selected date range.")
    else:
        kpi_row(dam_df["Price"], "DAM Price")
        section_divider()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dam_df["StartTime"],
            y=dam_df["Price"],
            mode="lines+markers",
            name="DAM Price",
            line=dict(color="#0d9488", width=2),
            marker=dict(size=4, color="#0d9488"),
            fill="tozeroy",
            fillcolor="rgba(13,148,136,0.06)",
            hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>€%{y:.2f} / MWh<extra></extra>",
        ))
        fig.update_layout(**chart_layout(
            "Day Ahead Market — Harmonised Reference Price", "EUR / MWh", height=450,
        ))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        section_divider()
        st.download_button(
            "↓  Export DAM Data (CSV)",
            data=dam_df.to_csv(index=False),
            file_name=f"dam_{start_str}_to_{end_str}.csv",
            mime="text/csv",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — COMPARISON
# ─────────────────────────────────────────────────────────────────────────────
with tab_comp:
    with st.spinner("Building comparison…"):
        imb_comp = fetch_imbalance(start_str, end_str)
        dam_comp  = fetch_dam(start_str, end_str)

    if imb_comp.empty and dam_comp.empty:
        st.warning("No data found for the selected date range.")
    else:
        fig = go.Figure()

        if not imb_comp.empty:
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
                name="Imbalance (hourly avg)",
                line=dict(color="#1d4ed8", width=2),
                hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>€%{y:.2f} / MWh<extra></extra>",
            ))

        if not dam_comp.empty:
            fig.add_trace(go.Scatter(
                x=dam_comp["StartTime"],
                y=dam_comp["Price"],
                mode="lines+markers",
                name="Day Ahead Market",
                line=dict(color="#0d9488", width=2),
                marker=dict(size=4),
                hovertemplate="<b>%{x|%d %b %Y %H:%M}</b><br>€%{y:.2f} / MWh<extra></extra>",
            ))

        fig.update_layout(**chart_layout(
            "Imbalance Price vs Day Ahead Market", "EUR / MWh", height=480,
        ))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if not imb_comp.empty and not dam_comp.empty:
            section_divider()
            st.markdown("<p style='font-size:13px;font-weight:600;color:#0f172a;margin-bottom:12px'>Summary Statistics</p>", unsafe_allow_html=True)
            stats = pd.DataFrame({
                "": ["Average", "Peak", "Minimum", "Std Deviation"],
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
# TAB 4 — AURORA
# ─────────────────────────────────────────────────────────────────────────────
with tab_aurora:
    st.markdown("""
    <div style="
        background:white;
        border:1px solid #e2e8f0;
        border-radius:12px;
        padding:40px 48px;
        text-align:center;
        box-shadow:0 1px 4px rgba(15,23,42,0.05);
        margin-top:1rem;
    ">
        <div style="
            width:56px;height:56px;border-radius:14px;
            background:linear-gradient(135deg,#7c3aed,#4f46e5);
            display:inline-flex;align-items:center;justify-content:center;
            font-size:26px;margin-bottom:20px;
        ">🌐</div>
        <h2 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#0f172a">
            Aurora Energy Research
        </h2>
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;max-width:480px;margin-left:auto;margin-right:auto">
            Merchant curve integration in development. Once connected, this tab will
            display forward price curves, scenario analysis, and Aurora forecasts
            alongside SEMO actuals.
        </p>
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 20px;min-width:160px">
                <p style="margin:0;font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Planned</p>
                <p style="margin:6px 0 0;font-size:13px;color:#0f172a;font-weight:500">Forward Price Curves</p>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 20px;min-width:160px">
                <p style="margin:0;font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Planned</p>
                <p style="margin:6px 0 0;font-size:13px;color:#0f172a;font-weight:500">Forecast vs Actual</p>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 20px;min-width:160px">
                <p style="margin:0;font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Planned</p>
                <p style="margin:6px 0 0;font-size:13px;color:#0f172a;font-weight:500">Scenario Analysis</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
