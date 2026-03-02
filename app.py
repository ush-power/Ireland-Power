import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
from google.oauth2 import service_account
from google.cloud import bigquery
import base64, os

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Ireland Power Terminal | Highfield Energy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# LOGO HELPER
# ============================================================================
def logo_b64() -> str:
    path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO = logo_b64()

# ============================================================================
# CSS — DARK TERMINAL THEME
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base — dark navy, not pitch black ── */
html, body, .stApp {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background-color: #0F1923 !important;
}
.stApp { background: #0F1923 !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* ── FUSE sidebar — always visible, hide collapse button ── */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: translateX(0) !important;
    min-width: 265px !important;
    max-width: 265px !important;
}
[data-testid="collapsedControl"] { display: none !important; }
button[data-testid="baseButton-header"] { display: none !important; }

/* ── Main content padding ── */
.block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1600px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #172032 !important;
    border-right: 1px solid #2D4A6B !important;
}
[data-testid="stSidebar"] hr {
    border-color: #2D4A6B !important;
    margin: 1rem 0 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption { color: #94A3B8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #E2E8F0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #172032 !important;
    border-bottom: 1px solid #2D4A6B !important;
    gap: 0 !important;
    padding: 0 !important;
    border-radius: 8px 8px 0 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    padding: 0 22px !important;
    height: 44px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
.stTabs [aria-selected="true"] {
    color: #F1F5F9 !important;
    border-bottom: 2px solid #FF4B4B !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 1.25rem !important;
}

/* ── Chart cards ── */
[data-testid="stPlotlyChart"] {
    background: #1E2D42 !important;
    border: 1px solid #2D4A6B !important;
    border-radius: 12px !important;
    padding: 4px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5) !important;
}

/* ── Dataframe cards ── */
[data-testid="stDataFrame"] {
    background: #1E2D42 !important;
    border: 1px solid #2D4A6B !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: transparent !important;
    color: #94A3B8 !important;
    border: 1px solid #2D4A6B !important;
    border-radius: 6px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    padding: 5px 14px !important;
    letter-spacing: 0.04em !important;
}
.stDownloadButton > button:hover {
    border-color: #94A3B8 !important;
    color: #E2E8F0 !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #FF4B4B !important; }

/* ── Divider ── */
hr { border-color: #2D4A6B !important; margin: 0.75rem 0 !important; }

/* ── Pulse animations ── */
@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 rgba(255,75,75,0.7); }
    70%  { box-shadow: 0 0 0 7px rgba(255,75,75,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,75,75,0); }
}
@keyframes pulse-cyan {
    0%   { box-shadow: 0 0 0 0 rgba(0,212,255,0.7); }
    70%  { box-shadow: 0 0 0 7px rgba(0,212,255,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,212,255,0); }
}
.dot-sbp {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: #FF4B4B;
    animation: pulse-red 1.8s infinite;
    margin-right: 7px; vertical-align: middle;
}
.dot-ssp {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: #00D4FF;
    animation: pulse-cyan 1.8s infinite;
    margin-right: 7px; vertical-align: middle;
}

/* ── Alert ── */
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# BIGQUERY
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
        SELECT StartTime,
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
        SELECT StartTime,
               CAST(Price AS FLOAT64) AS Price
        FROM `semo-price-automation.semo_data.dam_prices_hourly`
        WHERE DATE(TradeDate) BETWEEN '{start}' AND '{end}'
        ORDER BY StartTime
    """
    df = get_bq_client().query(query).to_dataframe()
    df["StartTime"] = pd.to_datetime(df["StartTime"])
    return df


# ============================================================================
# HELPERS
# ============================================================================
def system_state(niv: float):
    if niv < 0:
        return "SBP · SYSTEM SHORT", "#FF4B4B", "dot-sbp"
    elif niv > 0:
        return "SSP · SYSTEM LONG", "#00D4FF", "dot-ssp"
    return "BALANCED", "#C9D1D9", "dot-ssp"


def count_niv_flips(series) -> int:
    s = np.sign(pd.Series(series).dropna().values)
    s = s[s != 0]
    return int(np.sum(s[1:] != s[:-1])) if len(s) > 1 else 0


def generate_commentary(imb_df: pd.DataFrame, dam_df: pd.DataFrame = None) -> list:
    """Return list of {icon, color, text} analyst observations based on the selected data."""
    out = []
    prices = imb_df["ImbalancePrice"].dropna()
    niv    = imb_df["NetImbalanceVolume"].dropna()

    if prices.empty:
        return [{"icon": "⚠", "color": "#F59E0B",
                 "text": "Insufficient data to generate commentary for the selected period. Try widening the date range."}]

    avg  = prices.mean()
    std  = prices.std()
    peak = prices.max()
    low  = prices.min()

    # 1 — System direction bias
    pct_short = (niv < 0).mean() * 100
    pct_long  = 100 - pct_short
    if pct_short > 65:
        out.append({"icon": "↘", "color": "#FF4B4B",
                    "text": (f"The system was short in {pct_short:.0f}% of settlement periods — a persistent generation "
                             f"deficit. Parties with uncontracted positions were exposed to SBP for the majority of the "
                             f"period. This is a costly environment for any generator running below contracted output.")})
    elif pct_short < 35:
        out.append({"icon": "↗", "color": "#00D4FF",
                    "text": (f"The system was long in {pct_long:.0f}% of settlement periods, consistent with "
                             f"high renewable output or subdued demand. SSP applied for most intervals. Parties "
                             f"holding excess Day Ahead positions would have received a lower-than-expected settlement price.")})
    else:
        out.append({"icon": "⇄", "color": "#F59E0B",
                    "text": (f"Mixed system direction: {pct_short:.0f}% short / {pct_long:.0f}% long. "
                             f"The system alternated frequently between SBP and SSP regimes — a challenging environment "
                             f"for imbalance management, with no clear directional bias to position against.")})

    # 2 — Price volatility
    cv = std / avg if avg > 0 else 0
    if cv > 0.9:
        out.append({"icon": "⚡", "color": "#FF4B4B",
                    "text": (f"High price volatility: σ €{std:.2f}/MWh against a period mean of €{avg:.2f}/MWh "
                             f"(coefficient of variation {cv:.0%}). Intraday price swings are severe — "
                             f"likely reflecting tight wind-to-load margins or constrained thermal dispatch. "
                             f"Imbalance exposure carries significant cost risk in this environment.")})
    elif cv > 0.45:
        out.append({"icon": "〜", "color": "#F59E0B",
                    "text": (f"Moderate price dispersion: σ €{std:.2f}/MWh (CV {cv:.0%}). "
                             f"Some meaningful intraday spikes are present. Active positions should monitor "
                             f"imbalance exposure around morning and evening demand peaks.")})
    else:
        out.append({"icon": "≈", "color": "#00CC33",
                    "text": (f"Contained price dispersion: σ €{std:.2f}/MWh (CV {cv:.0%}). "
                             f"Stable dispatch conditions with predictable imbalance cost. "
                             f"Spread between peak and baseload is modest for this period.")})

    # 3 — Price spike analysis
    peak_idx  = prices.idxmax()
    peak_time = imb_df.loc[peak_idx, "StartTime"]
    peak_niv  = imb_df.loc[peak_idx, "NetImbalanceVolume"]
    ratio     = peak / avg if avg > 0 else 1
    if ratio > 3.0:
        niv_desc = "system was short (SBP event)" if peak_niv < 0 else "system was long (high SSP)"
        out.append({"icon": "▲", "color": "#FF4B4B",
                    "text": (f"Notable price spike: €{peak:.2f}/MWh at {peak_time.strftime('%d %b, %H:%M')} — "
                             f"{ratio:.1f}× the period average. The {niv_desc}. "
                             f"Spikes of this magnitude typically reflect scarcity pricing, a major unit outage, "
                             f"or a rapid drop in available renewable generation.")})
    elif ratio > 1.8:
        out.append({"icon": "△", "color": "#F59E0B",
                    "text": (f"Moderate price spike of €{peak:.2f}/MWh recorded at {peak_time.strftime('%d %b, %H:%M')} "
                             f"({ratio:.1f}× period average). Peak pricing is concentrated; "
                             f"well-timed positions around this window would have seen outsized settlement value.")})

    # 4 — NIV flip rate (system uncertainty)
    days  = max((imb_df["StartTime"].max() - imb_df["StartTime"].min()).total_seconds() / 86400, 1)
    flips = count_niv_flips(imb_df["NetImbalanceVolume"])
    fpd   = flips / days
    if fpd > 25:
        out.append({"icon": "⇅", "color": "#F59E0B",
                    "text": (f"High system instability: ~{fpd:.0f} NIV direction changes per day on average. "
                             f"Frequent SBP↔SSP transitions indicate volatile renewable dispatch or rapidly "
                             f"shifting demand patterns — increasing uncertainty for any party managing real-time imbalance.")})
    elif fpd > 12:
        out.append({"icon": "⇅", "color": "#94A3B8",
                    "text": (f"Moderate NIV flip rate: ~{fpd:.0f} direction changes per day. "
                             f"The system changed direction regularly, consistent with variable wind and mixed "
                             f"thermal/renewable dispatch across the period.")})

    # 5 — DAM vs imbalance spread (if DAM data available)
    if dam_df is not None and not dam_df.empty:
        dam_avg = dam_df["Price"].mean()
        spread  = avg - dam_avg
        if spread > 15:
            out.append({"icon": "↑", "color": "#FF4B4B",
                        "text": (f"Imbalance averaged €{spread:.2f}/MWh above the Day Ahead Market "
                                 f"(DAM: €{dam_avg:.2f} vs Imbalance: €{avg:.2f}/MWh). "
                                 f"Parties who were long in the DA market and short in real-time faced meaningful "
                                 f"value erosion. Forward procurement was cheaper than real-time settlement for this period.")})
        elif spread < -15:
            out.append({"icon": "↓", "color": "#00CC33",
                        "text": (f"Imbalance averaged €{abs(spread):.2f}/MWh below the Day Ahead Market "
                                 f"(DAM: €{dam_avg:.2f} vs Imbalance: €{avg:.2f}/MWh). "
                                 f"Excess DA positions settled at a premium to real-time — "
                                 f"the imbalance market was cheaper than forward procurement for this window.")})
        else:
            out.append({"icon": "≈", "color": "#94A3B8",
                        "text": (f"Imbalance and DAM prices tracked closely (€{abs(spread):.2f}/MWh average spread). "
                                 f"No significant arbitrage opportunity between day-ahead and real-time markets for this period.")})

    return out


# Shared Plotly layout for all charts
def dark_layout(title: str, height: int = 420) -> dict:
    axis = dict(
        gridcolor="rgba(255,255,255,0.04)",
        linecolor="#30363D",
        tickfont=dict(size=10, color="#8B949E"),
        zeroline=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor="#444",
        spikethickness=1,
    )
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#C9D1D9", size=11),
        title=dict(
            text=title,
            font=dict(size=12, color="#8B949E", family="Inter"),
            x=0.01, xanchor="left",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1E2D42", bordercolor="#444",
            font=dict(size=11, color="#E6EDF3",
                      family="'JetBrains Mono', monospace"),
        ),
        legend=dict(
            bgcolor="rgba(22,27,34,0.9)", bordercolor="#30363D",
            borderwidth=1, font=dict(size=11),
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ),
        margin=dict(t=44, b=8, l=8, r=8),
        height=height,
        xaxis={**axis},
        yaxis={**axis},
    )


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # Logo
    if LOGO:
        st.markdown(f"""
        <div style="background:#fff;border-radius:8px;padding:10px 14px;margin-bottom:16px">
            <img src="data:image/png;base64,{LOGO}" style="width:100%;max-width:200px;display:block;margin:auto">
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <p style="margin:0;font-size:10px;font-weight:600;color:#FF4B4B;
              text-transform:uppercase;letter-spacing:0.12em">Power Market Terminal</p>
    <p style="margin:4px 0 0;font-size:13px;color:#E6EDF3;font-weight:500">
        Ireland · SEMO / SEMOPX
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""<p style="margin:0 0 10px;font-size:10px;font-weight:600;
    color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Select Date Range</p>""",
    unsafe_allow_html=True)

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

    days_sel = (date_to - date_from).days + 1
    st.markdown(f"""
    <div style="background:#0D1117;border:1px solid #2D4A6B;border-radius:8px;
                padding:10px 14px;margin-top:10px">
        <p style="margin:0;font-size:11px;color:#8B949E;font-family:'JetBrains Mono',monospace">
            {date_from.strftime('%d %b %Y')} → {date_to.strftime('%d %b %Y')}
        </p>
        <p style="margin:4px 0 0;font-size:13px;font-weight:600;color:#E6EDF3">
            {days_sel} day{'s' if days_sel != 1 else ''}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="display:flex;flex-direction:column;gap:6px">
        <div style="display:flex;align-items:center;gap:8px">
            <span style="width:6px;height:6px;background:#FF4B4B;border-radius:50%;
                         display:inline-block;flex-shrink:0"></span>
            <span style="font-size:11px;color:#8B949E">SEMO · Imbalance</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
            <span style="width:6px;height:6px;background:#00D4FF;border-radius:50%;
                         display:inline-block;flex-shrink:0"></span>
            <span style="font-size:11px;color:#8B949E">SEMOPX · Day Ahead</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
            <span style="width:6px;height:6px;background:#30363D;border-radius:50%;
                         display:inline-block;flex-shrink:0"></span>
            <span style="font-size:11px;color:#444D56">Aurora · Coming Soon</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""<p style="margin:0;font-size:10px;color:#444D56;
    font-family:'JetBrains Mono',monospace">Updated daily · Cached 1h</p>""",
    unsafe_allow_html=True)


start_str = date_from.strftime("%Y-%m-%d")
end_str   = date_to.strftime("%Y-%m-%d")


# ============================================================================
# HEADER BAR
# ============================================================================
logo_html = (f'<img src="data:image/png;base64,{LOGO}" '
             f'style="height:32px;margin-right:14px;vertical-align:middle;'
             f'background:white;border-radius:4px;padding:3px 6px">')  if LOGO else ""

st.markdown(f"""
<div style="
    background:#172032;
    border:1px solid #2D4A6B;
    border-radius:10px;
    padding:14px 20px;
    margin-bottom:18px;
    display:flex;
    align-items:center;
    justify-content:space-between;
">
    <div style="display:flex;align-items:center">
        {logo_html}
        <div>
            <p style="margin:0;font-size:10px;font-weight:600;color:#FF4B4B;
                      text-transform:uppercase;letter-spacing:0.1em">
                Highfield Energy · Power Market Terminal
            </p>
            <p style="margin:3px 0 0;font-size:17px;font-weight:700;color:#E6EDF3;
                      letter-spacing:0.01em">
                Ireland Electricity Market
            </p>
        </div>
    </div>
    <div style="text-align:right">
        <p style="margin:0;font-size:10px;color:#8B949E;text-transform:uppercase;
                  letter-spacing:0.07em">Period</p>
        <p style="margin:4px 0 0;font-size:13px;font-weight:600;color:#E6EDF3;
                  font-family:'JetBrains Mono',monospace">
            {date_from.strftime('%d %b %Y')} → {date_to.strftime('%d %b %Y')}
        </p>
        <p style="margin:3px 0 0;font-size:11px;color:#8B949E">{days_sel} days · SEMO / SEMOPX</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# TABS
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "  Live Monitor  ",
    "  Historical Analysis  ",
    "  Statistical Edge  ",
    "  Aurora  ",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE MONITOR
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    with st.spinner("Loading…"):
        imb_df = fetch_imbalance(start_str, end_str)
        dam_df = fetch_dam(start_str, end_str)

    if imb_df.empty:
        st.warning("No imbalance data for the selected period.")
    else:
        latest       = imb_df.iloc[-1]
        latest_price = latest["ImbalancePrice"]
        latest_niv   = latest["NetImbalanceVolume"]
        state_label, state_color, dot_cls = system_state(latest_niv)

        # 24h comparison
        cutoff = imb_df["StartTime"].max() - pd.Timedelta(hours=24)
        prev_avg = imb_df[imb_df["StartTime"] <= cutoff]["ImbalancePrice"].mean()
        if prev_avg and prev_avg > 0:
            chg     = latest_price - prev_avg
            chg_pct = (chg / prev_avg) * 100
            chg_col = "#FF4B4B" if chg > 0 else "#00FF41"
            chg_str = f"{'+' if chg>0 else ''}€{chg:.2f} ({'+' if chg_pct>0 else ''}{chg_pct:.1f}%)"
        else:
            chg_str, chg_col = "—", "#8B949E"

        peak = imb_df["ImbalancePrice"].max()
        avg  = imb_df["ImbalancePrice"].mean()

        # ── KPI Ribbon ──
        def info_badge(tip: str) -> str:
            return (f'<span title="{tip}" style="cursor:help;font-size:9px;font-weight:700;'
                    f'color:#8B949E;border:1px solid #3D5A78;border-radius:50%;'
                    f'min-width:14px;height:14px;display:inline-flex;align-items:center;'
                    f'justify-content:center;margin-left:6px;flex-shrink:0;line-height:1">?</span>')

        tip_price = ("The real-time price paid or received to correct electricity supply/demand imbalances, "
                     "in Euro per MWh. High prices signal system stress or scarcity. "
                     "SBP applies when the system is short (needs more power); SSP applies when long (surplus).")
        tip_24h   = ("Compares the latest imbalance price to the average price over the past 24 hours. "
                     "A positive change means conditions are more expensive than recent history; negative means cheaper.")
        tip_peak  = ("The highest imbalance price recorded during the selected date range. "
                     "Price spikes indicate acute periods of system stress, often driven by low wind or unexpected plant outages.")
        tip_avg   = ("The mean imbalance price across all 5-minute intervals in the selected period. "
                     "A core benchmark for overall market conditions and portfolio cost assessment.")
        tip_niv   = ("Net Imbalance Volume: the gap between generation and demand across the system. "
                     "Positive (green) = system oversupplied — generators are long. "
                     "Negative (red) = system undersupplied — generators are short and must buy at SBP.")

        st.markdown(f"""
        <style>
        [title] {{ cursor: help; }}
        </style>
        <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap">

          <div style="flex:1.6;min-width:200px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid {state_color};
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span class="{dot_cls}"></span>
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">Live Imbalance Price</span>
              {info_badge(tip_price)}
            </div>
            <div style="font-size:34px;font-weight:700;color:{state_color};
                        font-family:'JetBrains Mono',monospace;line-height:1">
              €{latest_price:.2f}
            </div>
            <div style="margin-top:5px;font-size:11px;color:{state_color};
                        font-weight:600;letter-spacing:0.05em">{state_label}</div>
          </div>

          <div style="flex:1;min-width:140px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid #30363D;
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">24H Change</span>
              {info_badge(tip_24h)}
            </div>
            <p style="margin:0;font-size:22px;font-weight:700;color:{chg_col};
                      font-family:'JetBrains Mono',monospace">{chg_str}</p>
            <p style="margin:5px 0 0;font-size:10px;color:#8B949E">vs 24h avg</p>
          </div>

          <div style="flex:1;min-width:140px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid #FF4B4B;
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">Period Peak</span>
              {info_badge(tip_peak)}
            </div>
            <p style="margin:0;font-size:22px;font-weight:700;color:#FF4B4B;
                      font-family:'JetBrains Mono',monospace">€{peak:.2f}</p>
            <p style="margin:5px 0 0;font-size:10px;color:#8B949E">EUR / MWh</p>
          </div>

          <div style="flex:1;min-width:140px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid #00D4FF;
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">Period Average</span>
              {info_badge(tip_avg)}
            </div>
            <p style="margin:0;font-size:22px;font-weight:700;color:#00D4FF;
                      font-family:'JetBrains Mono',monospace">€{avg:.2f}</p>
            <p style="margin:5px 0 0;font-size:10px;color:#8B949E">EUR / MWh</p>
          </div>

          <div style="flex:1;min-width:140px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid #00CC33;
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">Latest NIV</span>
              {info_badge(tip_niv)}
            </div>
            <p style="margin:0;font-size:22px;font-weight:700;color:#00CC33;
                      font-family:'JetBrains Mono',monospace">{latest_niv:+.1f}</p>
            <p style="margin:5px 0 0;font-size:10px;color:#8B949E">MWh</p>
          </div>

        </div>
        """, unsafe_allow_html=True)

        # ── Synced Price + Volume chart (shared x-axis) ──
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.65, 0.35],
        )

        # Split by system state for colour
        for mask, name, col, fill in [
            (imb_df["NetImbalanceVolume"] < 0,  "SBP (Short)", "#FF4B4B", "rgba(255,75,75,0.07)"),
            (imb_df["NetImbalanceVolume"] >= 0, "SSP (Long)",  "#00D4FF", "rgba(0,212,255,0.07)"),
        ]:
            seg = imb_df.copy()
            seg.loc[~mask, "ImbalancePrice"] = None
            fig.add_trace(go.Scatter(
                x=seg["StartTime"], y=seg["ImbalancePrice"],
                mode="lines", name=name,
                line=dict(color=col, width=1.5),
                fill="tozeroy", fillcolor=fill,
                hovertemplate="<b>%{x|%d %b %H:%M}</b><br>€%{y:.2f}/MWh<extra>" + name + "</extra>",
            ), row=1, col=1)

        vol_colors = imb_df["NetImbalanceVolume"].apply(
            lambda v: "#00CC33" if v >= 0 else "#FF4B4B"
        ).tolist()
        fig.add_trace(go.Bar(
            x=imb_df["StartTime"], y=imb_df["NetImbalanceVolume"],
            name="NIV",
            marker=dict(color=vol_colors, opacity=0.9, line=dict(width=0)),
            hovertemplate="<b>%{x|%d %b %H:%M}</b><br>%{y:+.1f} MWh<extra>NIV</extra>",
        ), row=2, col=1)

        axis_style = dict(
            gridcolor="rgba(255,255,255,0.04)", linecolor="#30363D",
            tickfont=dict(size=10, color="#8B949E"), zeroline=False,
            showspikes=True, spikemode="across", spikesnap="cursor",
            spikedash="dot", spikecolor="#444", spikethickness=1,
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#C9D1D9", size=11),
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#1E2D42", bordercolor="#444",
                            font=dict(size=11, color="#E6EDF3",
                                      family="'JetBrains Mono',monospace")),
            legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor="#30363D",
                        borderwidth=1, font=dict(size=11),
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1),
            margin=dict(t=44, b=8, l=8, r=8),
            height=560,
            title=dict(text="IMBALANCE PRICE  ·  NET IMBALANCE VOLUME",
                       font=dict(size=12, color="#8B949E"), x=0.01),
            xaxis={**axis_style, "showticklabels": False},
            xaxis2={**axis_style,
                    "rangeslider": dict(visible=True, bgcolor="#0F1923", thickness=0.04)},
            yaxis={**axis_style,
                   "title": dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))},
            yaxis2={**axis_style,
                    "title": dict(text="NIV (MWh)", font=dict(size=10, color="#8B949E")),
                    "zeroline": True, "zerolinecolor": "#333"},
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Bahadir's Brain — Analyst Commentary ──
        commentary = generate_commentary(imb_df, dam_df if not dam_df.empty else None)

        obs_html = ""
        for obs in commentary:
            obs_html += f"""
            <div style="display:flex;gap:14px;align-items:flex-start;
                        padding:11px 0;border-bottom:1px solid rgba(45,74,107,0.5)">
              <span style="font-size:14px;color:{obs['color']};font-weight:700;
                           min-width:20px;text-align:center;margin-top:1px;
                           font-family:'JetBrains Mono',monospace">{obs['icon']}</span>
              <p style="margin:0;font-size:12.5px;color:#C9D1D9;line-height:1.6">{obs['text']}</p>
            </div>"""

        st.markdown(f"""
        <div style="background:#141F2E;border:1px solid #2D4A6B;border-top:2px solid #F59E0B;
                    border-radius:10px;padding:18px 22px;margin:18px 0">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
            <span style="font-size:22px;line-height:1">🧠</span>
            <div style="flex:1">
              <p style="margin:0;font-size:10px;font-weight:600;color:#F59E0B;
                        text-transform:uppercase;letter-spacing:0.12em">Commercial Analysis</p>
              <p style="margin:2px 0 0;font-size:14px;font-weight:700;color:#E6EDF3">
                Bahadir's Brain</p>
            </div>
            <div style="text-align:right">
              <p style="margin:0;font-size:10px;color:#8B949E;
                        font-family:'JetBrains Mono',monospace">
                {date_from.strftime('%d %b')} → {date_to.strftime('%d %b %Y')} · {days_sel}d</p>
              <p style="margin:3px 0 0;font-size:10px;color:#444D56">
                Based on {len(imb_df):,} settlement intervals</p>
            </div>
          </div>
          {obs_html}
          <p style="margin:12px 0 0;font-size:10px;color:#444D56;font-style:italic">
            Rule-based analysis. Observations update automatically with the selected date range.</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Latest readings data grid ──
        st.markdown("<p style='font-size:11px;font-weight:600;color:#8B949E;"
                    "text-transform:uppercase;letter-spacing:0.1em;"
                    "margin:16px 0 8px'>Latest Readings</p>",
                    unsafe_allow_html=True)

        recent = imb_df.tail(96).copy().iloc[::-1]
        recent["Direction"] = recent["NetImbalanceVolume"].apply(
            lambda v: "🔴  SBP · Short" if v < 0 else "🔵  SSP · Long"
        )
        grid_df = recent[["StartTime", "ImbalancePrice", "NetImbalanceVolume", "Direction"]].copy()
        grid_df.columns = ["Time", "Price (€/MWh)", "NIV (MWh)", "System State"]
        max_vol = float(grid_df["NIV (MWh)"].abs().max()) or 1.0

        st.dataframe(
            grid_df, use_container_width=True, hide_index=True, height=340,
            column_config={
                "Time": st.column_config.DatetimeColumn("Time", format="DD MMM HH:mm", width="small"),
                "Price (€/MWh)": st.column_config.NumberColumn("Price (€/MWh)", format="€%.2f", width="small"),
                "NIV (MWh)": st.column_config.ProgressColumn(
                    "NIV (MWh)", format="%.1f", min_value=-max_vol, max_value=max_vol, width="large",
                ),
                "System State": st.column_config.TextColumn("System State", width="medium"),
            },
        )
        st.download_button("↓  Export CSV", data=imb_df.to_csv(index=False),
                           file_name=f"imbalance_{start_str}_{end_str}.csv", mime="text/csv")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORICAL ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    with st.spinner("Loading…"):
        imb_h = fetch_imbalance(start_str, end_str)
        dam_h = fetch_dam(start_str, end_str)

    if imb_h.empty:
        st.warning("No data for the selected period.")
    else:
        col_a, col_b = st.columns([3, 2])

        with col_a:
            # Volatility + Price synced subplot
            hourly_p = imb_h.set_index("StartTime")["ImbalancePrice"].resample("1h").mean()
            roll_vol = hourly_p.rolling(24).std().reset_index()
            roll_vol.columns = ["t", "vol"]
            hourly_p = hourly_p.reset_index()
            hourly_p.columns = ["t", "p"]

            vfig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                 vertical_spacing=0.03, row_heights=[0.6, 0.4])
            vfig.add_trace(go.Scatter(
                x=hourly_p["t"], y=hourly_p["p"],
                mode="lines", name="Hourly Avg Price",
                line=dict(color="#00D4FF", width=1.5),
                fill="tozeroy", fillcolor="rgba(0,212,255,0.07)",
                hovertemplate="<b>%{x|%d %b %H:%M}</b><br>€%{y:.2f}/MWh<extra></extra>",
            ), row=1, col=1)
            if not dam_h.empty:
                vfig.add_trace(go.Scatter(
                    x=dam_h["StartTime"], y=dam_h["Price"],
                    mode="lines+markers", name="DAM Price",
                    line=dict(color="#7c3aed", width=1.5),
                    marker=dict(size=3),
                    hovertemplate="<b>%{x|%d %b %H:%M}</b><br>€%{y:.2f}/MWh<extra>DAM</extra>",
                ), row=1, col=1)
            vfig.add_trace(go.Scatter(
                x=roll_vol["t"], y=roll_vol["vol"],
                mode="lines", name="24h Volatility (σ)",
                line=dict(color="#FF4B4B", width=1.5),
                fill="tozeroy", fillcolor="rgba(255,75,75,0.1)",
                hovertemplate="<b>%{x|%d %b %H:%M}</b><br>σ €%{y:.2f}<extra></extra>",
            ), row=2, col=1)

            axis_s = dict(gridcolor="rgba(255,255,255,0.04)", linecolor="#30363D",
                          tickfont=dict(size=10, color="#8B949E"), zeroline=False,
                          showspikes=True, spikemode="across", spikesnap="cursor",
                          spikedash="dot", spikecolor="#444", spikethickness=1)
            vfig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#C9D1D9", size=11),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#1E2D42", bordercolor="#444",
                                font=dict(size=11, color="#E6EDF3",
                                          family="'JetBrains Mono',monospace")),
                legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor="#30363D",
                            borderwidth=1, font=dict(size=11),
                            orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1),
                margin=dict(t=44, b=8, l=8, r=8), height=480,
                title=dict(text="PRICE TREND  ·  24H ROLLING VOLATILITY",
                           font=dict(size=12, color="#8B949E"), x=0.01),
                xaxis={**axis_s, "showticklabels": False},
                xaxis2={**axis_s,
                        "rangeslider": dict(visible=True, bgcolor="#0F1923", thickness=0.04)},
                yaxis={**axis_s,
                       "title": dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))},
                yaxis2={**axis_s,
                        "title": dict(text="σ (EUR/MWh)", font=dict(size=10, color="#8B949E"))},
            )
            st.plotly_chart(vfig, use_container_width=True, config={"displayModeBar": False})

        with col_b:
            # Hour-of-day heatmap
            imb_h2 = imb_h.copy()
            imb_h2["hour"] = imb_h2["StartTime"].dt.hour
            imb_h2["day"]  = imb_h2["StartTime"].dt.strftime("%d %b")
            pivot = (imb_h2.groupby(["day", "hour"])["ImbalancePrice"]
                     .mean().reset_index()
                     .pivot(index="day", columns="hour", values="ImbalancePrice"))
            hfig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=[f"{h:02d}:00" for h in pivot.columns],
                y=list(pivot.index),
                colorscale="RdYlGn_r",
                colorbar=dict(title=dict(text="€/MWh", font=dict(color="#8B949E", size=10)),
                              tickfont=dict(color="#8B949E", size=9), thickness=10),
                hovertemplate="<b>%{y}  %{x}</b><br>€%{z:.2f}/MWh<extra></extra>",
            ))
            hfig.update_layout(**{
                **dark_layout("PRICE HEATMAP  ·  HOUR × DAY",
                              height=max(300, len(pivot) * 26 + 80)),
                "xaxis": {**dark_layout("")["xaxis"], "showspikes": False,
                          "tickangle": -45, "tickfont": dict(size=9, color="#8B949E")},
                "yaxis": {**dark_layout("")["yaxis"], "showspikes": False,
                          "tickfont": dict(size=9, color="#8B949E")},
            })
            st.plotly_chart(hfig, use_container_width=True, config={"displayModeBar": False})

        # Daily summary table with sparklines
        st.markdown("<p style='font-size:11px;font-weight:600;color:#8B949E;"
                    "text-transform:uppercase;letter-spacing:0.1em;"
                    "margin:16px 0 8px'>Daily Summary</p>", unsafe_allow_html=True)

        imb_h["Date"] = imb_h["StartTime"].dt.date
        daily = (imb_h.groupby("Date")
                 .agg(avg_price=("ImbalancePrice","mean"),
                      peak=("ImbalancePrice","max"),
                      low=("ImbalancePrice","min"),
                      avg_niv=("NetImbalanceVolume","mean"))
                 .reset_index())
        daily.columns = ["Date","Avg Price","Peak","Low","Avg NIV"]

        daily["NIV Flips"] = [
            count_niv_flips(imb_h[imb_h["Date"] == d]["NetImbalanceVolume"])
            for d in daily["Date"]
        ]
        daily["Price Trend"] = [
            imb_h[imb_h["Date"] == d]
            .set_index("StartTime")["ImbalancePrice"]
            .resample("1h").mean().tolist()
            for d in daily["Date"]
        ]

        max_flips = max(int(daily["NIV Flips"].max()), 1)
        st.dataframe(
            daily.sort_values("Date", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="DD MMM YYYY", width="small"),
                "Avg Price": st.column_config.NumberColumn("Avg (€/MWh)", format="€%.2f", width="small"),
                "Peak": st.column_config.NumberColumn("Peak (€/MWh)", format="€%.2f", width="small"),
                "Low": st.column_config.NumberColumn("Low (€/MWh)", format="€%.2f", width="small"),
                "NIV Flips": st.column_config.ProgressColumn(
                    "NIV Flips", format="%d", min_value=0, max_value=max_flips, width="medium"),
                "Avg NIV": st.column_config.NumberColumn("Avg NIV (MWh)", format="%.1f MWh", width="small"),
                "Price Trend": st.column_config.LineChartColumn(
                    "Price Trend (Hourly)", width="large"),
            },
        )
        st.download_button("↓  Export Daily Summary", data=daily.drop(columns=["Price Trend"]).to_csv(index=False),
                           file_name=f"daily_summary_{start_str}_{end_str}.csv", mime="text/csv")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — STATISTICAL EDGE
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    with st.spinner("Loading…"):
        imb_s = fetch_imbalance(start_str, end_str)

    if imb_s.empty:
        st.warning("No data for the selected period.")
    else:
        col1, col2 = st.columns(2)

        # ── Price Distribution Histogram ──
        with col1:
            prices = imb_s["ImbalancePrice"].dropna()
            mu, sigma = prices.mean(), prices.std()
            x_fit   = np.linspace(prices.min(), prices.max(), 200)
            y_fit   = ((1 / (sigma * np.sqrt(2 * np.pi)))
                       * np.exp(-0.5 * ((x_fit - mu) / sigma) ** 2))
            bin_w   = (prices.max() - prices.min()) / 50
            y_scale = y_fit * len(prices) * bin_w

            sbp_p = imb_s[imb_s["NetImbalanceVolume"] < 0]["ImbalancePrice"].dropna()
            ssp_p = imb_s[imb_s["NetImbalanceVolume"] >= 0]["ImbalancePrice"].dropna()

            hfig = go.Figure()
            if not sbp_p.empty:
                hfig.add_trace(go.Histogram(x=sbp_p, nbinsx=50, name="SBP (Short)",
                                            marker_color="#FF4B4B", opacity=0.7,
                                            hovertemplate="€%{x:.2f}<br>Count: %{y}<extra>SBP</extra>"))
            if not ssp_p.empty:
                hfig.add_trace(go.Histogram(x=ssp_p, nbinsx=50, name="SSP (Long)",
                                            marker_color="#00D4FF", opacity=0.7,
                                            hovertemplate="€%{x:.2f}<br>Count: %{y}<extra>SSP</extra>"))
            hfig.add_trace(go.Scatter(x=x_fit, y=y_scale, mode="lines",
                                      name=f"Normal (μ=€{mu:.1f})",
                                      line=dict(color="#00FF41", width=2, dash="dot")))
            hfig.add_vline(x=mu, line_width=1, line_dash="dash", line_color="#00FF41",
                           annotation_text=f"μ €{mu:.2f}",
                           annotation_font=dict(color="#00FF41", size=10))
            hfig.add_vline(x=float(np.median(prices)), line_width=1, line_dash="dot",
                           line_color="#f59e0b",
                           annotation_text=f"Med €{np.median(prices):.2f}",
                           annotation_font=dict(color="#f59e0b", size=10))
            layout_h = dark_layout("PRICE DISTRIBUTION  ·  SBP vs SSP", height=360)
            layout_h["barmode"] = "overlay"
            layout_h["xaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
            layout_h["yaxis"]["title"] = dict(text="Frequency", font=dict(size=10, color="#8B949E"))
            hfig.update_layout(**layout_h)
            st.plotly_chart(hfig, use_container_width=True, config={"displayModeBar": False})

        # ── NIV Flip Frequency ──
        with col2:
            imb_s["Date"] = imb_s["StartTime"].dt.date
            flip_data = pd.DataFrame({
                "Date": imb_s["Date"].unique(),
            })
            flip_data["NIV Flips"] = [
                count_niv_flips(imb_s[imb_s["Date"] == d]["NetImbalanceVolume"])
                for d in flip_data["Date"]
            ]
            flip_data = flip_data.sort_values("Date")
            med_flips = flip_data["NIV Flips"].median()

            q75 = flip_data["NIV Flips"].quantile(0.75)
            flip_colors = flip_data["NIV Flips"].apply(
                lambda v: "#FF4B4B" if v > q75 else
                          "#f59e0b" if v > med_flips else "#00D4FF"
            )
            ffig = go.Figure()
            ffig.add_trace(go.Bar(
                x=flip_data["Date"].astype(str),
                y=flip_data["NIV Flips"],
                marker_color=flip_colors,
                hovertemplate="<b>%{x}</b><br>%{y} NIV flips<extra></extra>",
                name="NIV Flips",
            ))
            ffig.add_hline(y=med_flips, line_width=1, line_dash="dash",
                           line_color="#8B949E",
                           annotation_text=f"Median {med_flips:.0f}",
                           annotation_font=dict(color="#8B949E", size=10))
            layout_f = dark_layout("NIV DIRECTION CHANGES / DAY  ·  System Uncertainty", height=360)
            layout_f["yaxis"]["title"] = dict(text="Flips", font=dict(size=10, color="#8B949E"))
            ffig.update_layout(**layout_f)
            st.plotly_chart(ffig, use_container_width=True, config={"displayModeBar": False})

        # ── Intraday Hourly Profile (Box plots) ──
        imb_s["Hour"] = imb_s["StartTime"].dt.hour
        bfig = go.Figure()
        for hr in range(24):
            d = imb_s[imb_s["Hour"] == hr]["ImbalancePrice"].dropna()
            if not d.empty:
                bfig.add_trace(go.Box(
                    y=d, name=f"{hr:02d}:00",
                    marker_color="#00D4FF", line=dict(color="#00D4FF"),
                    fillcolor="rgba(0,212,255,0.15)",
                    boxmean="sd", showlegend=False,
                    hovertemplate=f"<b>{hr:02d}:00</b><br>€%{{y:.2f}}/MWh<extra></extra>",
                ))
        layout_b = dark_layout("INTRADAY PRICE PROFILE  ·  HOURLY DISTRIBUTION", height=360)
        layout_b["xaxis"]["title"] = dict(text="Hour of Day", font=dict(size=10, color="#8B949E"))
        layout_b["yaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
        layout_b["xaxis"]["showspikes"] = False
        bfig.update_layout(**layout_b)
        st.plotly_chart(bfig, use_container_width=True, config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — AURORA
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    logo_part = (f'<img src="data:image/png;base64,{LOGO}" '
                 f'style="height:40px;background:white;border-radius:6px;'
                 f'padding:4px 8px;margin-bottom:16px">') if LOGO else ""
    st.markdown(f"""
    <div style="background:#1E2D42;border:1px solid #2D4A6B;border-radius:12px;
                padding:48px;text-align:center;margin-top:1rem">
        {logo_part}
        <p style="margin:0 0 6px;font-size:10px;font-weight:600;color:#8B949E;
                  text-transform:uppercase;letter-spacing:0.12em">Coming Soon</p>
        <h2 style="margin:0 0 10px;font-size:22px;font-weight:700;color:#E6EDF3">
            Aurora Energy Research
        </h2>
        <p style="margin:0 0 28px;font-size:13px;color:#8B949E;
                  max-width:480px;margin-left:auto;margin-right:auto">
            Merchant curve integration in development. Once connected, Aurora
            forward price curves will overlay directly on SEMO actuals for
            scenario analysis and model inputs.
        </p>
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
            {"".join(f'''<div style="background:#172032;border:1px solid #2D4A6B;border-radius:8px;
                padding:12px 20px;min-width:150px">
                <p style="margin:0;font-size:10px;color:#8B949E;font-weight:600;
                   text-transform:uppercase;letter-spacing:0.08em">Planned</p>
                <p style="margin:6px 0 0;font-size:12px;color:#C9D1D9;font-weight:500">{f}</p>
            </div>''' for f in ["Forward Price Curves","Forecast vs Actual","Scenario Analysis","Model Export"])}
        </div>
    </div>
    """, unsafe_allow_html=True)
