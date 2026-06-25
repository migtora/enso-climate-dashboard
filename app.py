import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# 1. Page Configuration
st.set_page_config(page_title="Global Climate Dashboard: ENSO (RONI)", layout="wide")
st.title("🌊 ENSO Tracker: Relative Oceanic Niño Index (RONI)")
st.subheader("Monitoring El Niño and La Niña transitions over the last 24 months")

# 2. Fetch Data from Official NOAA Source
# This URL points directly to the active ASCII text file updated by NOAA's Climate Prediction Center
DATA_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

@st.cache_data(ttl=86400) # Cache data for 24 hours (86,400 seconds) so it updates daily
def load_data():
    try:
        # Read the whitespace-delimited file directly from NOAA
        df = pd.read_csv(DATA_URL, sep=r'\s+', header=0)
        
        # Rename columns to match expected schema: SEAS -> Season, ANOM -> RONI
        df = df.rename(columns={'SEAS': 'Season', 'ANOM': 'RONI'})
        
        # Ensure correct datatypes and drop missing
        df['RONI'] = pd.to_numeric(df['RONI'], errors='coerce')
        df_clean = df.dropna(subset=['RONI']).reset_index(drop=True)
        return df_clean
    except Exception as e:
        st.error(f"Error connecting to NOAA data feed: {e}")
        return None
if df_all is not None:
    # 1. Grab the last 24 periods
    df_recent = df_all.tail(24).copy()
    df_recent['Timeframe'] = df_recent['YR'].astype(str) + " (" + df_recent['Season'] + ")"

    # 2. Layout Key Metrics
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

    # 3. Generate the Single Clean Plot
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    ax.plot(df_recent['Timeframe'], df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Threshold Shading
    ax.axhspan(0.5, max(2.0, latest_val + 0.2), color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(min(-2.0, latest_val - 0.2), -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 24 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Clean X-axis ticks (showing every 3rd label)
    ticks_to_use = range(0, len(df_recent['Timeframe']), 3)
    labels_to_use = [df_recent['Timeframe'].iloc[i] for i in ticks_to_use]
    
    ax.set_xticks(ticks_to_use)
    ax.set_xticklabels(labels_to_use, rotation=45, ha='right', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)

    # 4. Raw Data View Option (Updated footer to match the 24 periods)
    with st.expander("Show raw data for last 24 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
    plt.tight_layout()
    st.pyplot(fig)
