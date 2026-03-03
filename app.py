import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime, timezone
from google.oauth2 import service_account
from google.cloud import bigquery
import base64, os, re, requests
import xml.etree.ElementTree as ET

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
    """Fetch Ireland SEM day-ahead prices from ENTSO-E Transparency Platform."""
    api_key = st.secrets.get("ENTSOE_API_KEY", "")
    if not api_key:
        return pd.DataFrame(columns=["StartTime", "Price"])

    start_dt = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt   = datetime.strptime(end,   "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

    try:
        r = requests.get(
            "https://web-api.tp.entsoe.eu/api",
            params={
                "securityToken": api_key,
                "documentType":  "A44",
                "in_Domain":     "10Y1001A1001A59C",   # Ireland SEM
                "out_Domain":    "10Y1001A1001A59C",
                "periodStart":   start_dt.strftime("%Y%m%d%H%M"),
                "periodEnd":     end_dt.strftime("%Y%m%d%H%M"),
            },
            timeout=30,
        )
        r.raise_for_status()
    except Exception:
        return pd.DataFrame(columns=["StartTime", "Price"])

    root = ET.fromstring(r.content)
    ns_match = re.match(r"\{(.+?)\}", root.tag)
    ns  = {"n": ns_match.group(1)} if ns_match else {}
    pre = "n:" if ns else ""

    rows = []
    for ts in root.findall(f"{pre}TimeSeries", ns):
        for period in ts.findall(f"{pre}Period", ns):
            t_start_el = period.find(f"{pre}timeInterval/{pre}start", ns)
            res_el     = period.find(f"{pre}resolution", ns)
            if t_start_el is None or res_el is None:
                continue
            t_start = datetime.strptime(t_start_el.text, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
            res_min = 60 if "60M" in res_el.text else 30
            for point in period.findall(f"{pre}Point", ns):
                pos_el   = point.find(f"{pre}position", ns)
                price_el = point.find(f"{pre}price.amount", ns)
                if pos_el is None or price_el is None:
                    continue
                pos = int(pos_el.text) - 1
                rows.append({
                    "StartTime": t_start + timedelta(minutes=pos * res_min),
                    "Price":     float(price_el.text),
                })

    if not rows:
        return pd.DataFrame(columns=["StartTime", "Price"])

    df = pd.DataFrame(rows).sort_values("StartTime").reset_index(drop=True)
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
    """Return list of {icon, color, text} analyst observations from a renewable developer perspective."""
    out = []
    prices = imb_df["ImbalancePrice"].dropna()
    niv    = imb_df["NetImbalanceVolume"].dropna()

    if prices.empty:
        return [{"icon": "⚠", "color": "#F59E0B",
                 "text": "Insufficient data to generate commentary for the selected period. Try widening the date range."}]

    avg  = prices.mean()
    std  = prices.std()
    peak = prices.max()

    # 1 — System direction: what does it mean for asset revenue & imbalance exposure?
    pct_short = (niv < 0).mean() * 100
    pct_long  = 100 - pct_short
    if pct_short > 65:
        out.append({"icon": "↘", "color": "#FF4B4B",
                    "text": (f"The system was short in {pct_short:.0f}% of settlement intervals, indicating "
                             f"persistent demand exceeding available generation across the market. For Highfield's "
                             f"renewable assets, any underperformance against forecast during this period would "
                             f"attract SBP settlement — the more costly imbalance regime. Budget models should "
                             f"reflect an above-average imbalance cost assumption for periods with this directional bias.")})
    elif pct_short < 35:
        out.append({"icon": "↗", "color": "#00D4FF",
                    "text": (f"The system was long in {pct_long:.0f}% of settlement intervals, consistent with "
                             f"high renewable output across the market. Under SSP conditions, any surplus generation "
                             f"settles at a discounted rate below the Day Ahead price — a key driver of capture price "
                             f"discount for wind and solar assets. PPA valuations and budget revenue forecasts should "
                             f"account for the frequency of SSP periods, particularly during high-wind seasons.")})
    else:
        out.append({"icon": "⇄", "color": "#F59E0B",
                    "text": (f"Mixed system direction: {pct_short:.0f}% short / {pct_long:.0f}% long across the period. "
                             f"The blend of SBP and SSP regimes makes it difficult to assume a single price bias in "
                             f"budget modelling. For management account commentary, it is worth separating the "
                             f"short and long periods to understand what drove imbalance settlement costs in each direction.")})

    # 2 — Price volatility: impact on budget forecasting and PPA risk premium
    cv = std / avg if avg > 0 else 0
    if cv > 0.9:
        out.append({"icon": "⚡", "color": "#FF4B4B",
                    "text": (f"High price volatility: σ €{std:.2f}/MWh against a period mean of €{avg:.2f}/MWh "
                             f"(coefficient of variation {cv:.0%}). Large intraday swings create material uncertainty "
                             f"in imbalance budget forecasting for the portfolio. When pricing PPAs, this level of "
                             f"volatility typically requires a wider risk margin to be built into the strike price "
                             f"assumption. Revenue projections for management accounts should use a range rather "
                             f"than a single point estimate for the imbalance cost component.")})
    elif cv > 0.45:
        out.append({"icon": "〜", "color": "#F59E0B",
                    "text": (f"Moderate price dispersion: σ €{std:.2f}/MWh (CV {cv:.0%}). Some intraday variability "
                             f"is present, which will affect the accuracy of flat-rate imbalance assumptions in annual "
                             f"budgets. Consider stress-testing PPA revenue models against the observed spread between "
                             f"average and peak pricing when preparing management account forecasts.")})
    else:
        out.append({"icon": "≈", "color": "#00CC33",
                    "text": (f"Contained price dispersion: σ €{std:.2f}/MWh (CV {cv:.0%}). Stable market conditions "
                             f"support more reliable imbalance cost budgeting for this period. PPA pricing models "
                             f"built around a mean price assumption are well-supported by the data from this window.")})

    # 3 — Price spike: exposure for forecast errors at peak
    peak_idx  = prices.idxmax()
    peak_time = imb_df.loc[peak_idx, "StartTime"]
    peak_niv  = imb_df.loc[peak_idx, "NetImbalanceVolume"]
    ratio     = peak / avg if avg > 0 else 1
    if ratio > 3.0:
        regime = "SBP (system short — expensive for any asset underperforming forecast)" if peak_niv < 0 \
                 else "SSP (system long — revenue suppressed for over-generating assets)"
        out.append({"icon": "▲", "color": "#FF4B4B",
                    "text": (f"Significant price spike: €{peak:.2f}/MWh at {peak_time.strftime('%d %b, %H:%M')} — "
                             f"{ratio:.1f}× the period average. The prevailing regime was {regime}. "
                             f"Spikes of this magnitude can have an outsized impact on periodic imbalance settlement "
                             f"if forecast errors coincide with the event. It is worth cross-referencing whether "
                             f"Highfield assets were generating to forecast during this window.")})
    elif ratio > 1.8:
        out.append({"icon": "△", "color": "#F59E0B",
                    "text": (f"Elevated price spike of €{peak:.2f}/MWh recorded at {peak_time.strftime('%d %b, %H:%M')} "
                             f"({ratio:.1f}× period average). Concentrated peak pricing of this magnitude can distort "
                             f"periodic averages used in management account reporting. Flag this event in any "
                             f"commentary covering this period.")})

    # 4 — NIV flip rate: forecast uncertainty and budget risk
    days  = max((imb_df["StartTime"].max() - imb_df["StartTime"].min()).total_seconds() / 86400, 1)
    flips = count_niv_flips(imb_df["NetImbalanceVolume"])
    fpd   = flips / days
    if fpd > 25:
        out.append({"icon": "⇅", "color": "#F59E0B",
                    "text": (f"High system instability: ~{fpd:.0f} NIV direction changes per day on average. "
                             f"Frequent switching between SBP and SSP regimes increases forecast uncertainty and "
                             f"makes it harder to predict which imbalance price will apply at any given time. "
                             f"For budget purposes, a blended imbalance price assumption based on the SBP/SSP split "
                             f"is more appropriate than using either price alone for this type of period.")})
    elif fpd > 12:
        out.append({"icon": "⇅", "color": "#94A3B8",
                    "text": (f"Moderate NIV flip rate: ~{fpd:.0f} direction changes per day. Regular direction changes "
                             f"suggest variable renewable dispatch conditions across the market. Budget models should "
                             f"assume a mix of SBP and SSP settlement prices rather than a single imbalance price "
                             f"assumption for periods exhibiting this pattern.")})

    # 5 — DAM vs imbalance spread: PPA basis risk and budget impact
    if dam_df is not None and not dam_df.empty:
        dam_avg = dam_df["Price"].mean()
        spread  = avg - dam_avg
        if spread > 15:
            out.append({"icon": "↑", "color": "#FF4B4B",
                        "text": (f"Imbalance prices averaged €{spread:.2f}/MWh above the Day Ahead Market "
                                 f"(DAM: €{dam_avg:.2f} vs Imbalance: €{avg:.2f}/MWh). For PPA structures "
                                 f"where the reference price is linked to the Day Ahead index, this spread represents "
                                 f"the basis risk borne by the asset — real-time settlement was materially more "
                                 f"expensive than the contracted reference. This should be reflected in the risk "
                                 f"premium component of any upcoming PPA price review.")})
        elif spread < -15:
            out.append({"icon": "↓", "color": "#00CC33",
                        "text": (f"Imbalance prices averaged €{abs(spread):.2f}/MWh below the Day Ahead Market "
                                 f"(DAM: €{dam_avg:.2f} vs Imbalance: €{avg:.2f}/MWh). Real-time settlement was "
                                 f"cheaper than the day-ahead reference — a favourable outcome for assets with "
                                 f"DA-linked PPA contracts during this window. Worth noting in management account "
                                 f"commentary as a period where market conditions supported portfolio revenue.")})
        else:
            out.append({"icon": "≈", "color": "#94A3B8",
                        "text": (f"Imbalance and Day Ahead prices tracked closely (€{abs(spread):.2f}/MWh average spread). "
                                 f"The imbalance market closely reflected day-ahead pricing, minimising basis risk "
                                 f"for DA-referenced PPA structures. This period provides a useful benchmark for "
                                 f"PPA pricing discussions where low basis risk assumptions are being justified.")})

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
# DATE RANGE — session state (keeps slider + date inputs in sync)
# ============================================================================
_yesterday  = date.today() - timedelta(days=1)
_data_start = date(2025, 1, 1)

if "dr_from" not in st.session_state:
    st.session_state["dr_from"] = _yesterday - timedelta(days=6)
if "dr_to" not in st.session_state:
    st.session_state["dr_to"] = _yesterday


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

    st.markdown("""<p style="margin:0 0 8px;font-size:10px;font-weight:600;
    color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Select Date Range</p>""",
    unsafe_allow_html=True)

    yesterday  = _yesterday
    data_start = _data_start

    # ── Date input fields (precise entry) ──
    col_f, col_t = st.columns(2)
    inp_from = col_f.date_input(
        "From", value=st.session_state["dr_from"],
        min_value=data_start, max_value=yesterday,
    )
    inp_to = col_t.date_input(
        "To", value=st.session_state["dr_to"],
        min_value=data_start, max_value=yesterday,
    )
    if inp_from > inp_to:
        inp_to = inp_from
    if (inp_from, inp_to) != (st.session_state["dr_from"], st.session_state["dr_to"]):
        st.session_state["dr_from"] = inp_from
        st.session_state["dr_to"]   = inp_to
        st.rerun()

    # ── Slider (visual range selector) ──
    st.markdown("<p style='margin:8px 0 2px;font-size:10px;color:#8B949E'>or drag to select</p>",
                unsafe_allow_html=True)
    slid_from, slid_to = st.slider(
        "Date range",
        min_value=data_start,
        max_value=yesterday,
        value=(st.session_state["dr_from"], st.session_state["dr_to"]),
        format="DD MMM YYYY",
        label_visibility="collapsed",
    )
    if (slid_from, slid_to) != (st.session_state["dr_from"], st.session_state["dr_to"]):
        st.session_state["dr_from"] = slid_from
        st.session_state["dr_to"]   = slid_to
        st.rerun()

    date_from = st.session_state["dr_from"]
    date_to   = st.session_state["dr_to"]

    days_sel = (date_to - date_from).days + 1
    st.markdown(f"""
    <div style="background:#0D1117;border:1px solid #2D4A6B;border-radius:8px;
                padding:10px 14px;margin-top:6px">
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
    "  Market Monitor  ",
    "  Historical Analysis  ",
    "  Commercial Tools  ",
    "  Aurora  ",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET MONITOR
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

        # 24h high / low / range (last 24h of the selected period)
        cutoff_24h = imb_df["StartTime"].max() - pd.Timedelta(hours=24)
        last_24h   = imb_df[imb_df["StartTime"] >= cutoff_24h]["ImbalancePrice"].dropna()
        if not last_24h.empty:
            h24_high  = last_24h.max()
            h24_low   = last_24h.min()
            h24_range = h24_high - h24_low
            h24_avg   = last_24h.mean()
        else:
            h24_high = h24_low = h24_range = h24_avg = None

        peak = imb_df["ImbalancePrice"].max()
        avg  = imb_df["ImbalancePrice"].mean()

        # ── KPI Ribbon ──
        def info_badge(tip: str) -> str:
            return (f'<span title="{tip}" style="cursor:help;font-size:9px;font-weight:700;'
                    f'color:#8B949E;border:1px solid #3D5A78;border-radius:50%;'
                    f'min-width:14px;height:14px;display:inline-flex;align-items:center;'
                    f'justify-content:center;margin-left:6px;flex-shrink:0;line-height:1">?</span>')

        tip_price = ("The most recent imbalance settlement price in the dataset, in Euro per MWh. "
                     "Data is updated once daily — this is not a real-time feed. "
                     "SBP applies when the system is short (needs more power); SSP applies when long (surplus).")
        tip_24h   = ("The spread between the highest and lowest imbalance price in the last 24 hours of the selected period. "
                     "A wide range signals high price volatility — relevant when stress-testing budget assumptions or "
                     "assessing the risk of forecast errors coinciding with price extremes.")
        tip_peak  = ("The highest imbalance price recorded during the selected date range. "
                     "Price spikes indicate acute periods of system stress, often driven by low wind or unexpected plant outages.")
        tip_avg   = ("The mean imbalance price across all 5-minute intervals in the selected period. "
                     "A core benchmark for overall market conditions and portfolio cost assessment.")
        tip_niv   = ("Net Imbalance Volume: the gap between total generation and total demand across the Irish system. "
                     "LONG (positive, green): the system has more generation than demand — typically high wind or low load. "
                     "SSP (System Sell Price) applies; surplus generators receive a discounted settlement price. "
                     "SHORT (negative, red): demand exceeds available generation — the system is undersupplied. "
                     "SBP (System Buy Price) applies; any generator underperforming against its nominated output "
                     "must pay a premium to cover its shortfall. Short periods are the more costly imbalance regime.")

        st.markdown(f"""
        <style>
        [title] {{ cursor: help; }}
        </style>
        <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap">

          <div style="flex:1.6;min-width:200px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid {state_color};
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="width:7px;height:7px;background:{state_color};border-radius:50%;
                           display:inline-block;margin-right:7px;flex-shrink:0"></span>
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">Latest Imbalance Price</span>
              {info_badge(tip_price)}
            </div>
            <div style="font-size:34px;font-weight:700;color:{state_color};
                        font-family:'JetBrains Mono',monospace;line-height:1">
              €{latest_price:.2f}
            </div>
            <div style="margin-top:5px;font-size:11px;color:{state_color};
                        font-weight:600;letter-spacing:0.05em">{state_label}</div>
            <div style="margin-top:4px;font-size:10px;color:#8B949E;
                        font-family:'JetBrains Mono',monospace">
              {latest["StartTime"].strftime("%d %b %Y, %H:%M")}</div>
          </div>

          <div style="flex:1;min-width:140px;background:#1E2D42;
                      border:1px solid #2D4A6B;border-top:2px solid #94A3B8;
                      border-radius:10px;padding:14px 18px">
            <div style="display:flex;align-items:center;margin-bottom:5px">
              <span style="font-size:10px;font-weight:600;color:#8B949E;
                           text-transform:uppercase;letter-spacing:0.1em">24H Price Range</span>
              {info_badge(tip_24h)}
            </div>
            {'<p style="margin:0;font-size:22px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">€' + f"{h24_range:.2f}" + '</p><p style="margin:5px 0 0;font-size:10px;color:#8B949E;font-family:JetBrains Mono,monospace"><span style=\'color:#FF4B4B\'>H €' + f"{h24_high:.2f}" + '</span>  ·  <span style=\'color:#00CC33\'>L €' + f"{h24_low:.2f}" + '</span></p>' if h24_range is not None else '<p style="margin:0;font-size:22px;font-weight:700;color:#8B949E">—</p><p style="margin:5px 0 0;font-size:10px;color:#8B949E">No data</p>'}
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

        # ── SBP / SSP Reference Panel ──
        sbp_ivs   = imb_df[imb_df["NetImbalanceVolume"] < 0]["ImbalancePrice"]
        ssp_ivs   = imb_df[imb_df["NetImbalanceVolume"] >= 0]["ImbalancePrice"]
        pct_sbp_1 = (imb_df["NetImbalanceVolume"] < 0).mean() * 100
        pct_ssp_1 = 100 - pct_sbp_1
        sbp_avg_1 = float(sbp_ivs.mean()) if not sbp_ivs.empty else None
        ssp_avg_1 = float(ssp_ivs.mean()) if not ssp_ivs.empty else None
        dam_avg_1 = float(dam_df["Price"].mean()) if not dam_df.empty else None
        spread_1  = avg - dam_avg_1 if dam_avg_1 is not None else None
        sbp_avg_s = f"€{sbp_avg_1:.2f}/MWh" if sbp_avg_1 is not None else "—"
        ssp_avg_s = f"€{ssp_avg_1:.2f}/MWh" if ssp_avg_1 is not None else "—"
        dam_avg_s = f"€{dam_avg_1:.2f}" if dam_avg_1 is not None else "—"
        spread_s  = (f'{"+" if (spread_1 or 0) >= 0 else ""}€{spread_1:.2f}/MWh vs DAM' if spread_1 is not None else "")
        spread_col = "#FF4B4B" if (spread_1 or 0) > 5 else "#00CC33" if (spread_1 or 0) < -5 else "#94A3B8"
        dam_card = (
            f'<div style="flex:0.65;min-width:160px;background:#141F2E;border:1px solid #2D4A6B;border-left:3px solid #7c3aed;border-radius:8px;padding:11px 14px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:0.1em">DAM Reference · Period Avg</p>'
            f'<p style="margin:5px 0 0;font-size:22px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">{dam_avg_s}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:{spread_col};font-family:JetBrains Mono,monospace">{spread_s}</p>'
            f'<p style="margin:5px 0 0;font-size:11px;color:#8B949E">Day Ahead avg. Spread = basis risk for DA-linked PPA structures.</p>'
            f'</div>'
        ) if dam_avg_1 is not None else ""
        ref_html = (
            f'<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">'
            f'<div style="flex:1;min-width:210px;background:#1A0E0E;border:1px solid rgba(255,75,75,0.4);border-left:3px solid #FF4B4B;border-radius:8px;padding:11px 14px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#FF4B4B;text-transform:uppercase;letter-spacing:0.1em">SBP · System Short &nbsp;·&nbsp; {pct_sbp_1:.0f}% of period &nbsp;·&nbsp; avg {sbp_avg_s}</p>'
            f'<p style="margin:5px 0 0;font-size:11.5px;color:#94A3B8;line-height:1.55">Demand exceeds available generation. Assets producing <em>less</em> than nominated output settle at the System Buy Price. '
            f'This is the more costly regime — treat high-SBP periods as downside risk in budget models.</p>'
            f'</div>'
            f'<div style="flex:1;min-width:210px;background:#0A1A1A;border:1px solid rgba(0,212,255,0.4);border-left:3px solid #00D4FF;border-radius:8px;padding:11px 14px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#00D4FF;text-transform:uppercase;letter-spacing:0.1em">SSP · System Long &nbsp;·&nbsp; {pct_ssp_1:.0f}% of period &nbsp;·&nbsp; avg {ssp_avg_s}</p>'
            f'<p style="margin:5px 0 0;font-size:11.5px;color:#94A3B8;line-height:1.55">Generation exceeds demand — typically high wind or low load. Surplus output settles at the System Sell Price, '
            f'discounted below Day Ahead. This drives capture price discount for wind and solar portfolios.</p>'
            f'</div>'
            f'{dam_card}'
            f'</div>'
        )
        st.markdown(ref_html, unsafe_allow_html=True)

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

        if not dam_df.empty:
            fig.add_trace(go.Scatter(
                x=dam_df["StartTime"], y=dam_df["Price"],
                mode="lines", name="DAM (Hourly)",
                line=dict(color="#7c3aed", width=1.5, dash="dot"),
                hovertemplate="<b>%{x|%d %b %H:%M}</b><br>€%{y:.2f}/MWh<extra>DAM</extra>",
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
            c, ic, tx = obs["color"], obs["icon"], obs["text"]
            obs_html += (
                f'<div style="display:flex;gap:14px;align-items:flex-start;padding:11px 0;border-bottom:1px solid rgba(45,74,107,0.5)">'
                f'<span style="font-size:14px;color:{c};font-weight:700;min-width:20px;text-align:center;margin-top:2px;font-family:monospace">{ic}</span>'
                f'<p style="margin:0;font-size:12.5px;color:#C9D1D9;line-height:1.65">{tx}</p>'
                f'</div>'
            )

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
        daily["% Short"] = [
            round((imb_h[imb_h["Date"] == d]["NetImbalanceVolume"] < 0).mean() * 100, 1)
            for d in daily["Date"]
        ]
        daily["Price Trend"] = [
            imb_h[imb_h["Date"] == d]
            .set_index("StartTime")["ImbalancePrice"]
            .resample("1h").mean().tolist()
            for d in daily["Date"]
        ]

        if not dam_h.empty:
            dam_h["Date"] = dam_h["StartTime"].dt.date
            dam_daily = dam_h.groupby("Date")["Price"].mean().reset_index()
            dam_daily.columns = ["Date", "DAM Avg"]
            daily = daily.merge(dam_daily, on="Date", how="left")
            daily["Basis"] = daily["Avg Price"] - daily["DAM Avg"]

        max_flips = max(int(daily["NIV Flips"].max()), 1)
        col_cfg = {
            "Date": st.column_config.DateColumn("Date", format="DD MMM YYYY", width="small"),
            "Avg Price": st.column_config.NumberColumn("Imbalance Avg (€/MWh)", format="€%.2f", width="small"),
            "Peak": st.column_config.NumberColumn("Peak (€/MWh)", format="€%.2f", width="small"),
            "Low": st.column_config.NumberColumn("Low (€/MWh)", format="€%.2f", width="small"),
            "% Short": st.column_config.ProgressColumn(
                "% Short (SBP)", format="%.0f%%", min_value=0, max_value=100, width="small"),
            "NIV Flips": st.column_config.ProgressColumn(
                "NIV Flips", format="%d", min_value=0, max_value=max_flips, width="medium"),
            "Avg NIV": st.column_config.NumberColumn("Avg NIV (MWh)", format="%.1f MWh", width="small"),
            "Price Trend": st.column_config.LineChartColumn("Price Trend (Hourly)", width="large"),
        }
        if "DAM Avg" in daily.columns:
            col_cfg["DAM Avg"] = st.column_config.NumberColumn("DAM Avg (€/MWh)", format="€%.2f", width="small")
            col_cfg["Basis"] = st.column_config.NumberColumn("Basis vs DAM (€/MWh)", format="€%.2f", width="small")
        st.dataframe(
            daily.sort_values("Date", ascending=False),
            use_container_width=True, hide_index=True,
            column_config=col_cfg,
        )
        st.download_button("↓  Export Daily Summary", data=daily.drop(columns=["Price Trend"]).to_csv(index=False),
                           file_name=f"daily_summary_{start_str}_{end_str}.csv", mime="text/csv")

        # ── DAM vs Imbalance Basis Spread ──
        if not dam_h.empty and "DAM Avg" in daily.columns:
            basis_df = daily[daily["DAM Avg"].notna()].copy()
            basis_df["Date"] = pd.to_datetime(basis_df["Date"])
            b_colors = ["#00CC33" if b >= 0 else "#FF4B4B" for b in basis_df["Basis"]]

            bsfig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.04, row_heights=[0.58, 0.42],
            )
            bsfig.add_trace(go.Scatter(
                x=basis_df["Date"], y=basis_df["Avg Price"],
                mode="lines+markers", name="Imbalance Avg",
                line=dict(color="#00D4FF", width=2),
                marker=dict(size=4),
                hovertemplate="<b>%{x|%d %b}</b><br>Imbalance €%{y:.2f}/MWh<extra></extra>",
            ), row=1, col=1)
            bsfig.add_trace(go.Scatter(
                x=basis_df["Date"], y=basis_df["DAM Avg"],
                mode="lines+markers", name="DAM Avg",
                line=dict(color="#7c3aed", width=2),
                marker=dict(size=4),
                hovertemplate="<b>%{x|%d %b}</b><br>DAM €%{y:.2f}/MWh<extra>DAM</extra>",
            ), row=1, col=1)
            bsfig.add_trace(go.Bar(
                x=basis_df["Date"], y=basis_df["Basis"],
                name="Basis (Imb − DAM)",
                marker_color=b_colors,
                hovertemplate="<b>%{x|%d %b}</b><br>Basis %{y:+.2f} €/MWh<extra></extra>",
            ), row=2, col=1)
            bsfig.add_hline(y=0, line_width=1, line_color="#444D56", row=2, col=1)

            ax = dict(gridcolor="rgba(255,255,255,0.04)", linecolor="#30363D",
                      tickfont=dict(size=10, color="#8B949E"), zeroline=False,
                      showspikes=True, spikemode="across", spikesnap="cursor",
                      spikedash="dot", spikecolor="#444", spikethickness=1)
            bsfig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#C9D1D9", size=11),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#1E2D42", bordercolor="#444",
                                font=dict(size=11, color="#E6EDF3",
                                          family="'JetBrains Mono',monospace")),
                legend=dict(bgcolor="rgba(22,27,34,0.9)", bordercolor="#30363D",
                            borderwidth=1, font=dict(size=11),
                            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=44, b=8, l=8, r=8), height=420,
                title=dict(text="DAM vs IMBALANCE  ·  DAILY PRICES & BASIS SPREAD",
                           font=dict(size=12, color="#8B949E"), x=0.01),
                xaxis={**ax, "showticklabels": False},
                xaxis2={**ax, "rangeslider": dict(visible=True, bgcolor="#0F1923", thickness=0.04)},
                yaxis={**ax, "title": dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))},
                yaxis2={**ax, "title": dict(text="Basis (€/MWh)", font=dict(size=10, color="#8B949E")),
                        "zeroline": True, "zerolinecolor": "#333"},
            )
            st.plotly_chart(bsfig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                '<p style="margin:0 0 4px;font-size:10px;color:#444D56;font-style:italic">'
                'Green bars: imbalance settled above DAM (revenue upside vs DA-indexed PPA reference). '
                'Red bars: imbalance settled below DAM (revenue discount vs DA reference — key basis risk for DA-linked PPAs). '
                'Persistent red periods should be factored into PPA risk margin and management account commentary.</p>',
                unsafe_allow_html=True
            )


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMMERCIAL TOOLS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    with st.spinner("Loading…"):
        imb_s = fetch_imbalance(start_str, end_str)
        dam_s = fetch_dam(start_str, end_str)

    if imb_s.empty:
        st.warning("No data for the selected period.")
    else:
        prices   = imb_s["ImbalancePrice"].dropna()
        sbp_mask = imb_s["NetImbalanceVolume"] < 0
        sbp_p    = imb_s[sbp_mask]["ImbalancePrice"].dropna()
        ssp_p    = imb_s[~sbp_mask]["ImbalancePrice"].dropna()
        mu_s     = float(prices.mean())
        sig_s    = float(prices.std())
        p10_s    = float(prices.quantile(0.10))
        p25_s    = float(prices.quantile(0.25))
        p50_s    = float(prices.quantile(0.50))
        p75_s    = float(prices.quantile(0.75))
        p90_s    = float(prices.quantile(0.90))
        pct_sbp_s = sbp_mask.mean() * 100
        pct_ssp_s = 100 - pct_sbp_s
        sbp_avg_s2 = float(sbp_p.mean()) if not sbp_p.empty else None
        ssp_avg_s2 = float(ssp_p.mean()) if not ssp_p.empty else None
        dam_avg_s2 = float(dam_s["Price"].mean()) if not dam_s.empty else None
        basis_s2   = mu_s - dam_avg_s2 if dam_avg_s2 is not None else None

        # ── Section 0: DAM Price Summary ──
        if not dam_s.empty:
            dam_px       = dam_s["Price"].dropna()
            dam_avg_kpi  = float(dam_px.mean())
            dam_high_kpi = float(dam_px.max())
            dam_low_kpi  = float(dam_px.min())
            dam_std_kpi  = float(dam_px.std())
            dam_cv_kpi   = dam_std_kpi / dam_avg_kpi * 100 if dam_avg_kpi > 0 else 0
            pct_above_100 = float((dam_px > 100).mean() * 100)
            pct_below_50  = float((dam_px < 50).mean() * 100)

            dam_s_hr        = dam_s.copy()
            dam_s_hr["Hour"] = dam_s_hr["StartTime"].dt.hour
            peak_px   = dam_s_hr[(dam_s_hr["Hour"] >= 8) & (dam_s_hr["Hour"] < 20)]["Price"]
            offpk_px  = dam_s_hr[(dam_s_hr["Hour"] < 8) | (dam_s_hr["Hour"] >= 20)]["Price"]
            dam_peak  = float(peak_px.mean())  if not peak_px.empty  else None
            dam_offpk = float(offpk_px.mean()) if not offpk_px.empty else None
            pk_premium = ((dam_peak / dam_offpk) - 1) * 100 if (dam_peak and dam_offpk and dam_offpk > 0) else None

            pk_col  = "#00CC33" if pk_premium and pk_premium > 0 else "#8B949E"
            cv_col  = "#FF4B4B" if dam_cv_kpi > 60 else "#F59E0B" if dam_cv_kpi > 35 else "#00CC33"
            h100_col = "#FF4B4B" if pct_above_100 > 20 else "#F59E0B" if pct_above_100 > 5 else "#00CC33"

            st.markdown('<p style="margin:0 0 10px;font-size:10px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Day Ahead Market — Period Summary</p>', unsafe_allow_html=True)
            dam_kpi_html = (
                f'<div style="display:flex;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
                f'<div style="flex:1.3;min-width:130px;background:#1A1430;border:1px solid #3D2A6B;border-top:2px solid #7c3aed;border-radius:8px;padding:11px 13px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#7c3aed;text-transform:uppercase;letter-spacing:0.1em">DAM Period Avg</p>'
                f'<p style="margin:5px 0 0;font-size:24px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">€{dam_avg_kpi:.2f}</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">EUR / MWh</p></div>'
                f'<div style="flex:1;min-width:110px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #FF4B4B;border-radius:8px;padding:11px 13px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">DAM High</p>'
                f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#FF4B4B;font-family:JetBrains Mono,monospace">€{dam_high_kpi:.2f}</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">Period peak</p></div>'
                f'<div style="flex:1;min-width:110px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #00CC33;border-radius:8px;padding:11px 13px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">DAM Low</p>'
                f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#00CC33;font-family:JetBrains Mono,monospace">€{dam_low_kpi:.2f}</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">Period floor</p></div>'
                f'<div style="flex:1;min-width:110px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid {cv_col};border-radius:8px;padding:11px 13px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">DAM Volatility</p>'
                f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:{cv_col};font-family:JetBrains Mono,monospace">{dam_cv_kpi:.0f}%</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">CV (σ / avg)</p></div>'
                f'<div style="flex:1;min-width:110px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid {h100_col};border-radius:8px;padding:11px 13px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Hours &gt; €100</p>'
                f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:{h100_col};font-family:JetBrains Mono,monospace">{pct_above_100:.0f}%</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of DA hours</p></div>'
                f'</div>'
            )
            if dam_peak is not None and dam_offpk is not None:
                dam_kpi_html += (
                    f'<div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">'
                    f'<div style="flex:1;min-width:140px;background:#1E2D42;border:1px solid #2D4A6B;border-left:3px solid #7c3aed;border-radius:8px;padding:10px 13px">'
                    f'<p style="margin:0;font-size:9px;font-weight:600;color:#7c3aed;text-transform:uppercase;letter-spacing:0.1em">Peak Hours Avg &nbsp;·&nbsp; 08:00–20:00 UTC</p>'
                    f'<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">€{dam_peak:.2f}/MWh</p>'
                    f'</div>'
                    f'<div style="flex:1;min-width:140px;background:#1E2D42;border:1px solid #2D4A6B;border-left:3px solid #444D56;border-radius:8px;padding:10px 13px">'
                    f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Off-Peak Hours Avg &nbsp;·&nbsp; 20:00–08:00 UTC</p>'
                    f'<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">€{dam_offpk:.2f}/MWh</p>'
                    f'</div>'
                    f'<div style="flex:0.6;min-width:120px;background:#1E2D42;border:1px solid #2D4A6B;border-left:3px solid {pk_col};border-radius:8px;padding:10px 13px">'
                    f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Peak Premium</p>'
                    f'<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:{pk_col};font-family:JetBrains Mono,monospace">{pk_premium:+.1f}%</p>'
                    f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">over off-peak &nbsp;·&nbsp; {pct_below_50:.0f}% of DA hours below €50</p>'
                    f'</div>'
                    f'</div>'
                    f'<p style="margin:0 0 18px;font-size:10px;color:#444D56;font-style:italic">Peak/off-peak split based on 08:00–20:00 UTC. Peak premium reflects the shaped value vs flat-rate assumptions — relevant for PPA structuring (flat vs shaped/load-following contracts). High CV indicates wide intraday price swings; assets with flexible dispatch can capture more of the peak-hour premium.</p>'
                )
            st.markdown(dam_kpi_html, unsafe_allow_html=True)

        # ── Section 1: PPA & Budget Price Reference ──
        st.markdown('<p style="margin:0 0 10px;font-size:10px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">PPA &amp; Budget Price Reference — Period Percentiles</p>', unsafe_allow_html=True)
        ppa_html = (
            f'<div style="display:flex;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
            f'<div style="flex:1;min-width:100px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #FF4B4B;border-radius:8px;padding:11px 13px">'
            f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">P10 · Low Price</p>'
            f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#FF4B4B;font-family:JetBrains Mono,monospace">€{p10_s:.2f}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">Revenue downside — stress test</p></div>'
            f'<div style="flex:1;min-width:100px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #94A3B8;border-radius:8px;padding:11px 13px">'
            f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">P25</p>'
            f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#94A3B8;font-family:JetBrains Mono,monospace">€{p25_s:.2f}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">25th percentile</p></div>'
            f'<div style="flex:1.25;min-width:120px;background:#1A2438;border:2px solid #00D4FF;border-top:3px solid #00D4FF;border-radius:8px;padding:11px 13px">'
            f'<p style="margin:0;font-size:9px;font-weight:600;color:#00D4FF;text-transform:uppercase;letter-spacing:0.1em">P50 · Base Case</p>'
            f'<p style="margin:5px 0 0;font-size:23px;font-weight:700;color:#00D4FF;font-family:JetBrains Mono,monospace">€{p50_s:.2f}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">Median — budget midpoint</p></div>'
            f'<div style="flex:1;min-width:100px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #F59E0B;border-radius:8px;padding:11px 13px">'
            f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">P75</p>'
            f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#F59E0B;font-family:JetBrains Mono,monospace">€{p75_s:.2f}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">75th percentile</p></div>'
            f'<div style="flex:1;min-width:100px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid #00CC33;border-radius:8px;padding:11px 13px">'
            f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">P90 · High Price</p>'
            f'<p style="margin:5px 0 0;font-size:21px;font-weight:700;color:#00CC33;font-family:JetBrains Mono,monospace">€{p90_s:.2f}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">Revenue upside scenario</p></div>'
            f'</div>'
            f'<p style="margin:4px 0 16px;font-size:10px;color:#444D56;font-style:italic">Price percentiles across all settlement intervals in the selected period. As a seller, high prices are the revenue upside. Use P50 as the central budget estimate; P10 as the revenue downside / stress case for PPA floor pricing; P90 as the revenue upside for sensitivity analysis.</p>'
        )
        st.markdown(ppa_html, unsafe_allow_html=True)

        # ── Section 2: Regime Exposure ──
        st.markdown('<p style="margin:0 0 10px;font-size:10px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Imbalance Regime Exposure</p>', unsafe_allow_html=True)
        sbp_s2_str = f"€{sbp_avg_s2:.2f}/MWh" if sbp_avg_s2 is not None else "—"
        ssp_s2_str = f"€{ssp_avg_s2:.2f}/MWh" if ssp_avg_s2 is not None else "—"
        dam_s2_str = f"€{dam_avg_s2:.2f}" if dam_avg_s2 is not None else "—"
        basis_col  = "#FF4B4B" if (basis_s2 or 0) > 5 else "#00CC33" if (basis_s2 or 0) < -5 else "#8B949E"
        basis_str  = (f'{"+" if (basis_s2 or 0) >= 0 else ""}€{basis_s2:.2f}/MWh vs DAM' if basis_s2 is not None else "")
        dam_exp_card = (
            f'<div style="flex:0.75;min-width:180px;background:#141F2E;border:1px solid #2D4A6B;border-left:3px solid #7c3aed;border-radius:8px;padding:12px 15px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:0.1em">Day Ahead Market · Period Avg</p>'
            f'<p style="margin:5px 0 0;font-size:24px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">{dam_s2_str}</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:{basis_col};font-family:JetBrains Mono,monospace">{basis_str}</p>'
            f'<p style="margin:6px 0 0;font-size:11px;color:#8B949E">PPA basis risk: the spread between imbalance settlement and the DA reference price determines the cost or benefit of a DA-indexed PPA during this period.</p>'
            f'</div>'
        ) if dam_avg_s2 is not None else ""
        regime_html = (
            f'<div style="display:flex;gap:10px;margin-bottom:6px;flex-wrap:wrap">'
            f'<div style="flex:1;min-width:200px;background:#1A0E0E;border:1px solid rgba(255,75,75,0.35);border-left:3px solid #FF4B4B;border-radius:8px;padding:12px 15px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#FF4B4B;text-transform:uppercase;letter-spacing:0.1em">SBP · System Short</p>'
            f'<p style="margin:5px 0 0;font-size:28px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">{pct_sbp_s:.0f}%</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of intervals &nbsp;·&nbsp; avg {sbp_s2_str}</p>'
            f'<p style="margin:7px 0 0;font-size:11px;color:#94A3B8">Underperforming assets settle at SBP. High frequency signals elevated imbalance cost risk — factor into budget and PPA risk margin.</p>'
            f'</div>'
            f'<div style="flex:1;min-width:200px;background:#0A1A1A;border:1px solid rgba(0,212,255,0.35);border-left:3px solid #00D4FF;border-radius:8px;padding:12px 15px">'
            f'<p style="margin:0;font-size:9px;font-weight:700;color:#00D4FF;text-transform:uppercase;letter-spacing:0.1em">SSP · System Long</p>'
            f'<p style="margin:5px 0 0;font-size:28px;font-weight:700;color:#E6EDF3;font-family:JetBrains Mono,monospace">{pct_ssp_s:.0f}%</p>'
            f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of intervals &nbsp;·&nbsp; avg {ssp_s2_str}</p>'
            f'<p style="margin:7px 0 0;font-size:11px;color:#94A3B8">Surplus generation settles at SSP, discounted vs Day Ahead. High frequency = lower capture price for wind and solar. Key input for PPA revenue modelling.</p>'
            f'</div>'
            f'{dam_exp_card}'
            f'</div>'
        )
        st.markdown(regime_html, unsafe_allow_html=True)

        # ── Budget Guidance Card ──
        if basis_s2 is not None and basis_s2 > 10:
            bg_msg = (f"Imbalance prices averaged €{basis_s2:.2f}/MWh <strong>above</strong> the Day Ahead Market (DAM: {dam_s2_str} vs Imbalance: €{mu_s:.2f}/MWh). "
                      f"For DA-referenced PPAs, this spread represents the basis cost borne by the asset — real-time settlement was materially more expensive than the contracted reference. "
                      f"Build this spread into the risk premium for any upcoming PPA pricing or renewal discussion.")
            bg_col, bg_icon = "#FF4B4B", "⚠"
        elif basis_s2 is not None and basis_s2 < -10:
            bg_msg = (f"Imbalance prices averaged €{abs(basis_s2):.2f}/MWh <strong>below</strong> the Day Ahead Market (DAM: {dam_s2_str} vs Imbalance: €{mu_s:.2f}/MWh). "
                      f"Favourable for DA-referenced PPA structures — real-time settlement was cheaper than the day-ahead reference. "
                      f"Worth flagging in management account commentary as a period where market conditions supported portfolio revenue.")
            bg_col, bg_icon = "#00CC33", "✓"
        else:
            sbp_budget_rng = f"€{p10_s:.2f} (P10) to €{p90_s:.2f} (P90)"
            bg_msg = (f"Revenue price range for the period: {sbp_budget_rng}/MWh. "
                      f"With {pct_sbp_s:.0f}% of intervals in SBP (avg {sbp_s2_str}) and {pct_ssp_s:.0f}% in SSP (avg {ssp_s2_str}), "
                      f"a blended imbalance price of €{mu_s:.2f}/MWh is the appropriate central estimate for management account reporting. "
                      f"As a seller, use P10 (€{p10_s:.2f}/MWh) as the revenue downside / stress assumption for CFO sign-off scenarios, and P90 (€{p90_s:.2f}/MWh) as the revenue upside.")
            bg_col, bg_icon = "#F59E0B", "■"

        st.markdown(
            f'<div style="background:#141F2E;border:1px solid #2D4A6B;border-left:3px solid {bg_col};border-radius:8px;padding:13px 16px;margin:10px 0 18px;display:flex;gap:12px;align-items:flex-start">'
            f'<span style="font-size:14px;color:{bg_col};font-weight:700;margin-top:1px;flex-shrink:0">{bg_icon}</span>'
            f'<div><p style="margin:0;font-size:10px;font-weight:600;color:{bg_col};text-transform:uppercase;letter-spacing:0.1em">Budget &amp; PPA Guidance</p>'
            f'<p style="margin:4px 0 0;font-size:12.5px;color:#C9D1D9;line-height:1.65">{bg_msg}</p></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── Capture Price Analysis ──
        if dam_avg_s2 is not None and dam_avg_s2 > 0:
            capture_blend = mu_s     / dam_avg_s2 * 100
            ssp_capture   = (ssp_avg_s2 / dam_avg_s2 * 100) if ssp_avg_s2 else None
            sbp_premium   = (sbp_avg_s2 / dam_avg_s2 * 100) if sbp_avg_s2 else None

            def _cap_col(pct):
                return "#00CC33" if pct >= 95 else "#F59E0B" if pct >= 80 else "#FF4B4B"

            blend_col = _cap_col(capture_blend)
            ssp_col   = _cap_col(ssp_capture) if ssp_capture else "#8B949E"
            sbp_col   = "#00CC33" if sbp_premium and sbp_premium >= 100 else "#F59E0B"

            cap_html = (
                f'<p style="margin:0 0 10px;font-size:10px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Capture Price Analysis &nbsp;·&nbsp; Imbalance vs Day Ahead</p>'
                f'<div style="display:flex;gap:8px;margin-bottom:6px;flex-wrap:wrap">'
                f'<div style="flex:1;min-width:150px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid {blend_col};border-radius:8px;padding:12px 14px">'
                f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">Blended Capture Rate</p>'
                f'<p style="margin:5px 0 0;font-size:24px;font-weight:700;color:{blend_col};font-family:JetBrains Mono,monospace">{capture_blend:.1f}%</p>'
                f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of DAM avg &nbsp;·&nbsp; Imbalance €{mu_s:.2f} vs DAM €{dam_avg_s2:.2f}</p>'
                f'<p style="margin:7px 0 0;font-size:11px;color:#94A3B8">Blended settlement price as a % of the Day Ahead reference. For a seller, values above 100% mean imbalance revenue exceeded the DA benchmark.</p>'
                f'</div>'
            )
            if ssp_capture is not None:
                cap_html += (
                    f'<div style="flex:1;min-width:150px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid {ssp_col};border-radius:8px;padding:12px 14px">'
                    f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">SSP Capture Rate</p>'
                    f'<p style="margin:5px 0 0;font-size:24px;font-weight:700;color:{ssp_col};font-family:JetBrains Mono,monospace">{ssp_capture:.1f}%</p>'
                    f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of DAM avg &nbsp;·&nbsp; SSP €{ssp_avg_s2:.2f} vs DAM €{dam_avg_s2:.2f}</p>'
                    f'<p style="margin:7px 0 0;font-size:11px;color:#94A3B8">During system-long (SSP) intervals — common in high-wind periods — generation settles at a discount to DAM. This discount is the primary driver of capture price loss for wind and solar.</p>'
                    f'</div>'
                )
            if sbp_premium is not None:
                cap_html += (
                    f'<div style="flex:1;min-width:150px;background:#1E2D42;border:1px solid #2D4A6B;border-top:2px solid {sbp_col};border-radius:8px;padding:12px 14px">'
                    f'<p style="margin:0;font-size:9px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">SBP Premium Rate</p>'
                    f'<p style="margin:5px 0 0;font-size:24px;font-weight:700;color:{sbp_col};font-family:JetBrains Mono,monospace">{sbp_premium:.1f}%</p>'
                    f'<p style="margin:2px 0 0;font-size:10px;color:#8B949E">of DAM avg &nbsp;·&nbsp; SBP €{sbp_avg_s2:.2f} vs DAM €{dam_avg_s2:.2f}</p>'
                    f'<p style="margin:7px 0 0;font-size:11px;color:#94A3B8">During system-short (SBP) intervals, settlement prices typically exceed DAM. For assets overperforming forecast during these windows this is a revenue upside; for underperformers it is a cost.</p>'
                    f'</div>'
                )
            cap_html += f'</div><p style="margin:4px 0 18px;font-size:10px;color:#444D56;font-style:italic">Capture rates calculated using ENTSO-E Day Ahead prices for Ireland SEM vs SEMO imbalance settlement. Values below 100% indicate a discount to the DA reference; above 100% indicate a premium.</p>'
            st.markdown(cap_html, unsafe_allow_html=True)

        # ── Section 3: Charts ──
        col1, col2 = st.columns(2)

        with col1:
            # Price Distribution — SBP vs SSP
            x_fit   = np.linspace(prices.min(), prices.max(), 200)
            y_fit   = ((1 / (sig_s * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_fit - mu_s) / sig_s) ** 2))
            bin_w   = (prices.max() - prices.min()) / 50
            y_scale = y_fit * len(prices) * bin_w
            hfig = go.Figure()
            if not sbp_p.empty:
                hfig.add_trace(go.Histogram(x=sbp_p, nbinsx=50, name="SBP · Short",
                                            marker_color="#FF4B4B", opacity=0.7,
                                            hovertemplate="€%{x:.2f}<br>Count: %{y}<extra>SBP</extra>"))
            if not ssp_p.empty:
                hfig.add_trace(go.Histogram(x=ssp_p, nbinsx=50, name="SSP · Long",
                                            marker_color="#00D4FF", opacity=0.7,
                                            hovertemplate="€%{x:.2f}<br>Count: %{y}<extra>SSP</extra>"))
            hfig.add_trace(go.Scatter(x=x_fit, y=y_scale, mode="lines",
                                      name=f"Normal (μ=€{mu_s:.1f})",
                                      line=dict(color="#00FF41", width=2, dash="dot")))
            for pval, plabel, pcol in [
                (p10_s, "P10", "#FF4B4B"),
                (p50_s, "P50", "#00D4FF"),
                (p90_s, "P90", "#00CC33"),
            ]:
                hfig.add_vline(x=pval, line_width=1, line_dash="dash", line_color=pcol,
                               annotation_text=f"{plabel} €{pval:.2f}",
                               annotation_font=dict(color=pcol, size=10))
            if dam_avg_s2 is not None:
                hfig.add_vline(x=dam_avg_s2, line_width=1.5, line_dash="dot", line_color="#7c3aed",
                               annotation_text=f"DAM €{dam_avg_s2:.2f}",
                               annotation_font=dict(color="#7c3aed", size=10))
            layout_h = dark_layout("PRICE DISTRIBUTION  ·  SBP vs SSP  ·  PPA Risk Reference", height=360)
            layout_h["barmode"] = "overlay"
            layout_h["xaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
            layout_h["yaxis"]["title"] = dict(text="Frequency", font=dict(size=10, color="#8B949E"))
            hfig.update_layout(**layout_h)
            st.plotly_chart(hfig, use_container_width=True, config={"displayModeBar": False})

        with col2:
            # System Instability — NIV flip rate per day
            imb_s["Date"] = imb_s["StartTime"].dt.date
            flip_data = pd.DataFrame({"Date": sorted(imb_s["Date"].unique())})
            flip_data["NIV Flips"] = [
                count_niv_flips(imb_s[imb_s["Date"] == d]["NetImbalanceVolume"])
                for d in flip_data["Date"]
            ]
            med_flips = flip_data["NIV Flips"].median()
            q75_f = flip_data["NIV Flips"].quantile(0.75)
            flip_colors = flip_data["NIV Flips"].apply(
                lambda v: "#FF4B4B" if v > q75_f else "#f59e0b" if v > med_flips else "#00D4FF"
            ).tolist()
            ffig = go.Figure()
            ffig.add_trace(go.Bar(
                x=flip_data["Date"].astype(str), y=flip_data["NIV Flips"],
                marker_color=flip_colors,
                hovertemplate="<b>%{x}</b><br>%{y} NIV direction changes<extra></extra>",
                name="NIV Flips",
            ))
            ffig.add_hline(y=med_flips, line_width=1, line_dash="dash", line_color="#8B949E",
                           annotation_text=f"Median {med_flips:.0f}",
                           annotation_font=dict(color="#8B949E", size=10))
            layout_f = dark_layout("SYSTEM INSTABILITY  ·  NIV Direction Changes / Day", height=360)
            layout_f["yaxis"]["title"] = dict(text="Flips / Day", font=dict(size=10, color="#8B949E"))
            ffig.update_layout(**layout_f)
            st.plotly_chart(ffig, use_container_width=True, config={"displayModeBar": False})

        # ── DAM Distribution + DAM Hourly Profile ──
        if not dam_s.empty:
            col3, col4 = st.columns(2)
            with col3:
                dam_px_s = dam_s["Price"].dropna()
                dam_p10  = float(dam_px_s.quantile(0.10))
                dam_p50  = float(dam_px_s.quantile(0.50))
                dam_p90  = float(dam_px_s.quantile(0.90))
                dfig = go.Figure()
                dfig.add_trace(go.Histogram(
                    x=dam_px_s, nbinsx=40, name="DAM Price",
                    marker_color="#7c3aed", opacity=0.75,
                    hovertemplate="€%{x:.2f}<br>Count: %{y}<extra>DAM</extra>",
                ))
                for pval, plabel, pcol in [
                    (dam_p10, "P10", "#FF4B4B"),
                    (dam_p50, "P50", "#00D4FF"),
                    (dam_p90, "P90", "#00CC33"),
                ]:
                    dfig.add_vline(x=pval, line_width=1, line_dash="dash", line_color=pcol,
                                   annotation_text=f"{plabel} €{pval:.2f}",
                                   annotation_font=dict(color=pcol, size=10))
                layout_d = dark_layout("DAM PRICE DISTRIBUTION  ·  Period Percentiles", height=360)
                layout_d["xaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
                layout_d["yaxis"]["title"] = dict(text="Frequency", font=dict(size=10, color="#8B949E"))
                dfig.update_layout(**layout_d)
                st.plotly_chart(dfig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                    '<p style="margin:0 0 4px;font-size:10px;color:#444D56;font-style:italic">'
                    f'DAM price distribution for the period. P10 (€{dam_p10:.2f}) = revenue downside reference for DA-indexed contracts; '
                    f'P90 (€{dam_p90:.2f}) = upside. Use alongside the imbalance distribution to understand whether the basis widens or narrows at price extremes.</p>',
                    unsafe_allow_html=True
                )
            with col4:
                dam_hr_s = dam_s.copy()
                dam_hr_s["Hour"] = dam_hr_s["StartTime"].dt.hour
                dam_hr_avg = dam_hr_s.groupby("Hour")["Price"].mean()
                hr_colors = [
                    "#7c3aed" if (8 <= h < 20) else "#444D56"
                    for h in dam_hr_avg.index
                ]
                hrfig = go.Figure()
                hrfig.add_trace(go.Bar(
                    x=[f"{h:02d}:00" for h in dam_hr_avg.index],
                    y=dam_hr_avg.values,
                    marker_color=hr_colors,
                    name="DAM Hourly Avg",
                    hovertemplate="<b>%{x}</b><br>DAM €%{y:.2f}/MWh<extra></extra>",
                ))
                hrfig.add_hline(y=float(dam_px_s.mean()), line_width=1, line_dash="dash",
                                line_color="#8B949E",
                                annotation_text=f"Avg €{float(dam_px_s.mean()):.2f}",
                                annotation_font=dict(color="#8B949E", size=10))
                layout_hr = dark_layout("DAM HOURLY PROFILE  ·  Peak (purple) vs Off-Peak (grey)", height=360)
                layout_hr["xaxis"]["title"] = dict(text="Hour of Day (UTC)", font=dict(size=10, color="#8B949E"))
                layout_hr["yaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
                layout_hr["xaxis"]["showspikes"] = False
                hrfig.update_layout(**layout_hr)
                st.plotly_chart(hrfig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                    '<p style="margin:0 0 4px;font-size:10px;color:#444D56;font-style:italic">'
                    'Average DAM price by hour (UTC). Purple = peak hours (08:00–20:00), grey = off-peak. '
                    'Hours where DA prices are consistently high are the most valuable for assets with flexible dispatch. '
                    'Used to assess the shaped vs flat value difference when structuring PPAs.</p>',
                    unsafe_allow_html=True
                )

        # ── Intraday Capture Price Profile ──
        st.markdown(
            '<p style="margin:4px 0 6px;font-size:10px;font-weight:600;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em">'
            'Intraday Price Profile &nbsp;·&nbsp; Capture Price Risk by Hour of Day</p>',
            unsafe_allow_html=True
        )
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
        if not dam_s.empty:
            dam_s_hr = dam_s.copy()
            dam_s_hr["Hour"] = dam_s_hr["StartTime"].dt.hour
            dam_hourly = dam_s_hr.groupby("Hour")["Price"].mean()
            bfig.add_trace(go.Scatter(
                x=[f"{hr:02d}:00" for hr in dam_hourly.index],
                y=dam_hourly.values,
                mode="lines+markers",
                name="DAM Hourly Avg",
                line=dict(color="#7c3aed", width=2),
                marker=dict(size=5, color="#7c3aed"),
                hovertemplate="<b>%{x}</b><br>DAM €%{y:.2f}/MWh<extra>DAM</extra>",
            ))
        layout_b = dark_layout("INTRADAY PRICE PROFILE  ·  Imbalance vs DAM by Hour  ·  Boxplot with σ", height=380)
        layout_b["xaxis"]["title"] = dict(text="Hour of Day (UTC)", font=dict(size=10, color="#8B949E"))
        layout_b["yaxis"]["title"] = dict(text="EUR/MWh", font=dict(size=10, color="#8B949E"))
        layout_b["xaxis"]["showspikes"] = False
        bfig.update_layout(**layout_b)
        st.plotly_chart(bfig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            '<p style="margin:0 0 4px;font-size:10px;color:#444D56;font-style:italic">'
            'Imbalance settlement distribution by hour (box plots) vs Day Ahead hourly avg (purple line). '
            'Where imbalance boxes sit above the DAM line, real-time settlement exceeded the DA reference — a revenue upside for sellers. '
            'Hours with wide boxes and high prices are the most impactful for PPA capture price assumptions.</p>',
            unsafe_allow_html=True
        )


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
