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

df_all = load_data()

if df_all is not None:
    # Get the last 24 reported rolling seasons
    df_recent = df_all.tail(24).copy()
    df_recent['Timeframe'] = df_recent['YR'].astype(str) + " (" + df_recent['Season'] + ")"

    # 3. Layout Key Metrics
    latest_val = df_recent['RONI'].iloc[-1]
    latest_time = df_recent['Timeframe'].iloc[-1]
    
    if latest_val >= 0.5:
        status = "🔴 El Niño (Warm Phase)"
        color = "inverse"
    elif latest_val <= -0.5:
        status = "🔵 La Niña (Cool Phase)"
        color = "normal"
    else:
        status = "⚪ ENSO-Neutral"
        color = "off"
        
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"Latest RONI Value ({latest_time})", value=f"{latest_val} °C")
    with col2:
        st.markdown(f"**Current Phase Status:** \n### {status}")

    st.write("---")

    # 4. Generate the Plot
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    # Plot line and dots
    ax.plot(df_recent['Timeframe'], df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Threshold Shading
    ax.axhspan(0.5, max(2.0, latest_val + 0.2), color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(min(-2.0, latest_val - 0.2), -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    # Baseline line
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    # Styling details
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 6 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Render plot to Streamlit
    st.pyplot(fig)

    # 5. Raw Data View Option
    with st.expander("Show raw data for last 6 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
