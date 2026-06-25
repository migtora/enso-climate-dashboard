import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# 1. Page Configuration
st.set_page_config(page_title="Global Climate Dashboard: ENSO (RONI)", layout="wide")
st.title("🌊 ENSO Tracker: Relative Oceanic Niño Index (RONI)")
st.subheader("Monitoring El Niño and La Niña transitions over the last 24 months")

# 2. Fetch Data from Official NOAA Source
DATA_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

@st.cache_data(ttl=86400)
def load_data():
    try:
        response = requests.get(DATA_URL)
        if response.status_code != 200:
            st.error(f"Failed to pull data from NOAA server (Status code: {response.status_code})")
            return None
            
        # Use exact column character widths to bypass parsing errors entirely
        # YR (5 chars), then 12 seasons of 7 chars each
        col_widths = [5, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]
        col_names = ['YR', 'DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
        
        # Read fixed-width file, skipping the original misaligned header line entirely
        df = pd.read_fwf(
            io.StringIO(response.text),
            widths=col_widths,
            names=col_names,
            header=None,
            skiprows=1
        )
        
        # Melt and clean data structure
        seasons = col_names[1:]
        df_long = pd.melt(df, id_vars=['YR'], value_vars=seasons, var_name='Season', value_name='RONI')
        
        # Ensure correct sorting and drop missing/trailing entries
        df_long = df_long.sort_values(by=['YR', 'Season']).dropna().reset_index(drop=True)
        return df_long
    except Exception as e:
        st.error(f"Error parsing NOAA data feed: {e}")
        return None

df_all = load_data()

if df_all is not None:
    # 3. Grab the last 24 periods (2 years)
    df_recent = df_all.tail(24).copy()
    df_recent['Timeframe'] = df_recent['YR'].astype(str) + " (" + df_recent['Season'] + ")"

    # 4. Layout Key Metrics
    latest_val = df_recent['RONI'].iloc[-1]
    latest_time = df_recent['Timeframe'].iloc[-1]
    
    if latest_val >= 0.5:
        status = "🔴 El Niño (Warm Phase)"
    elif latest_val <= -0.5:
        status = "🔵 La Niña (Cool Phase)"
    else:
        status = "⚪ ENSO-Neutral"
        
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"Latest RONI Value ({latest_time})", value=f"{latest_val} °C")
    with col2:
        st.markdown(f"**Current Phase Status:** \n### {status}")

    st.write("---")

    # 5. Generate the Clean Visual Chart
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    ax.plot(df_recent['Timeframe'], df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Threshold Shading Zones
    ax.axhspan(0.5, max(2.0, latest_val + 0.2), color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(min(-2.0, latest_val - 0.2), -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 24 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Clean X-axis ticks (showing every 3rd label to avoid layout clutter)
    ticks_to_use = range(0, len(df_recent['Timeframe']), 3)
    labels_to_use = [df_recent['Timeframe'].iloc[i] for i in ticks_to_use]
    
    ax.set_xticks(ticks_to_use)
    ax.set_xticklabels(labels_to_use, rotation=45, ha='right', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)

    # 6. Raw Data View Option
    with st.expander("Show raw data for last 24 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
