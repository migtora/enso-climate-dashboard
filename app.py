import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="ENSO Dashboard",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 ENSO Dashboard")
st.subheader("Relative Oceanic Niño Index (RONI)")

# =====================================================
# NOAA DATA SOURCE
# =====================================================

DATA_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data(ttl=86400)
def load_roni():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        DATA_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    text = response.text

    # NOAA format:
    # SEAS YR ANOM
    # DJF 1950 -1.47

    df = pd.read_csv(
        StringIO(text),
        sep=r"\s+"
    )

    df.columns = [
        "Season",
        "Year",
        "RONI"
    ]

    df["Year"] = pd.to_numeric(df["Year"])
    df["RONI"] = pd.to_numeric(df["RONI"])

    season_order = {
        "DJF":0,
        "JFM":1,
        "FMA":2,
        "MAM":3,
        "AMJ":4,
        "MJJ":5,
        "JJA":6,
        "JAS":7,
        "ASO":8,
        "SON":9,
        "OND":10,
        "NDJ":11
    }

    df["Season_Order"] = df["Season"].map(season_order)

    df = (
        df.sort_values(
            ["Year", "Season_Order"]
        )
        .reset_index(drop=True)
    )

    return df

# =====================================================
# GET DATA
# =====================================================

try:

    df = load_roni()

except Exception as e:

    st.error(f"NOAA Data Error: {e}")
    st.stop()

# =====================================================
# LAST 24 PERIODS
# =====================================================

recent = df.tail(24).copy()

recent["Period"] = (
    recent["Year"].astype(str)
    + "-"
    + recent["Season"]
)

# =====================================================
# CURRENT STATUS
# =====================================================

latest = recent.iloc[-1]

latest_value = float(latest["RONI"])

if latest_value >= 0.5:
    phase = "🔴 El Niño"

elif latest_value <= -0.5:
    phase = "🔵 La Niña"

else:
    phase = "⚪ Neutral"

# =====================================================
# KPI SECTION
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Latest RONI",
        f"{latest_value:.2f} °C"
    )

with col2:
    st.metric(
        "Current Phase",
        phase
    )

with col3:
    st.metric(
        "Latest Period",
        latest["Period"]
    )

st.divider()

# =====================================================
# CHART
# =====================================================

fig, ax = plt.subplots(
    figsize=(14,6)
)

x = list(range(len(recent)))

# El Niño Zone
ax.axhspan(
    0.5,
    3,
    alpha=0.15
)

# Neutral Zone
ax.axhspan(
    -0.5,
    0.5,
    alpha=0.08
)

# La Niña Zone
ax.axhspan(
    -3,
    -0.5,
    alpha=0.15
)

ax.plot(
    x,
    recent["RONI"],
    marker="o",
    linewidth=2
)

ax.axhline(
    0,
    linestyle="--"
)

ax.axhline(
    0.5,
    linestyle=":"
)

ax.axhline(
    -0.5,
    linestyle=":"
)

margin = 0.25

ax.set_ylim(
    recent["RONI"].min() - margin,
    recent["RONI"].max() + margin
)

ax.set_title(
    "RONI - Last 24 Periods"
)

ax.set_ylabel(
    "Temperature Anomaly (°C)"
)

ax.set_xticks(x)

ax.set_xticklabels(
    recent["Period"],
    rotation=45,
    ha="right"
)

ax.grid(alpha=0.3)

plt.tight_layout()

st.pyplot(fig)

# =====================================================
# RAW DATA
# =====================================================

with st.expander("Raw Data"):

    st.dataframe(
        recent[
            [
                "Year",
                "Season",
                "RONI"
            ]
        ],
        use_container_width=True
    )

# =====================================================
# FULL DATA
# =====================================================

with st.expander("Full NOAA Dataset"):

    st.dataframe(
        df,
        use_container_width=True
    )
