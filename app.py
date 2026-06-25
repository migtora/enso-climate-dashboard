import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="ENSO Climate Dashboard",
    layout="wide"
)

st.title("🌊 ENSO Dashboard")
st.caption("Relative Oceanic Niño Index (RONI) Monitor")

DATA_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

# --------------------------------------------------
# DATA LOADER
# --------------------------------------------------

@st.cache_data(ttl=86400)
def load_roni():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            DATA_URL,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        raw_text = response.text

        # Debug switch
        # st.code(raw_text[:2000])

        seasons = [
            'DJF','JFM','FMA','MAM',
            'AMJ','MJJ','JJA','JAS',
            'ASO','SON','OND','NDJ'
        ]

        rows = []

        for line in raw_text.splitlines():

            parts = line.split()

            if len(parts) >= 13:

                year = parts[0]

                if year.isdigit() and len(year) == 4:

                    rows.append(parts[:13])

        if len(rows) == 0:
            return None, raw_text

        df = pd.DataFrame(
            rows,
            columns=["YR"] + seasons
        )

        for col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df["YR"] = df["YR"].astype(int)

        df_long = pd.melt(
            df,
            id_vars=["YR"],
            value_vars=seasons,
            var_name="Season",
            value_name="RONI"
        )

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

        df_long["Season_Order"] = (
            df_long["Season"]
            .map(season_order)
        )

        df_long = (
            df_long
            .sort_values(
                ["YR","Season_Order"]
            )
            .dropna()
            .reset_index(drop=True)
        )

        return df_long, None

    except Exception as e:

        return None, str(e)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df, debug = load_roni()

# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

if df is None:

    st.error("Unable to load NOAA RONI dataset.")

    with st.expander("Debug Information"):

        st.write(debug)

    st.stop()

# --------------------------------------------------
# LAST 24 OBSERVATIONS
# --------------------------------------------------

recent = df.tail(24).copy()

recent["Period"] = (
    recent["YR"].astype(str)
    + "-"
    + recent["Season"]
)

latest = recent.iloc[-1]

latest_roni = latest["RONI"]

if latest_roni >= 0.5:
    phase = "🔴 El Niño"
elif latest_roni <= -0.5:
    phase = "🔵 La Niña"
else:
    phase = "⚪ Neutral"

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Latest RONI",
        round(float(latest_roni),2)
    )

with col2:

    st.metric(
        "Current Phase",
        phase
    )

with col3:

    st.metric(
        "Observation",
        latest["Period"]
    )

st.divider()

# --------------------------------------------------
# CHART
# --------------------------------------------------

fig, ax = plt.subplots(
    figsize=(14,6)
)

x = range(len(recent))

ax.axhspan(
    0.5,
    2.0,
    alpha=0.20
)

ax.axhspan(
    -0.5,
    0.5,
    alpha=0.08
)

ax.axhspan(
    -2.0,
    -0.5,
    alpha=0.20
)

ax.plot(
    x,
    recent["RONI"],
    marker="o",
    linewidth=2
)

ax.axhline(
    0,
    linestyle="--",
    linewidth=1
)

ax.set_title(
    "RONI (Last 24 Periods)"
)

ax.set_ylabel(
    "Temperature Anomaly (°C)"
)

ax.set_xticks(list(x))

ax.set_xticklabels(
    recent["Period"],
    rotation=45,
    ha="right"
)

ax.grid(
    alpha=0.3
)

plt.tight_layout()

st.pyplot(fig)

# --------------------------------------------------
# TABLE
# --------------------------------------------------

with st.expander("Raw Data"):

    st.dataframe(
        recent[
            [
                "YR",
                "Season",
                "RONI"
            ]
        ],
        use_container_width=True
    )
