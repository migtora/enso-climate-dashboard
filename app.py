import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

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
            
        seasons = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
        rows = []
        
        # Parse line by line to skip introduction texts and trailing notes smoothly
        for line in response.text.split('\n'):
            parts = line.split()
            # Valid data rows must have a 4-digit year and cover all 12 seasonal values
            if parts and parts[0].isdigit() and len(parts[0]) == 4 and len(parts) >= 13:
                rows.append(parts[:13])
                
        if not rows:
            st.error("Could not parse the data grid. Check if the source file format changed.")
            return None
            
        df = pd.DataFrame(rows, columns=['YR'] + seasons)
        
        # Convert values to numeric types
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df['YR'] = df['YR'].astype(int)
        
        # Restructure to long time series format
        df_long = pd.melt(df, id_vars=['YR'], value_vars=seasons, var_name='Season', value_name='RONI')
        
        # Sort chronologically by calendar sequence
        season_order = {s: i for i, s in enumerate(seasons)}
        df_long['Season_Order'] = df_long['Season'].map(season_order)
        df_long = df_long.sort_values(by=['YR', 'Season_Order']).dropna().reset_index(drop=True)
        
        return df_long
    except Exception as e:
        st.error(f"Error parsing NOAA data feed: {e}")
        return None

df_all = load_data()

if df_all is not None and not df_all.empty:
    # 3. Filter for the last 24 intervals
    df_recent = df_all.tail(24).copy()
    df_recent['Timeframe'] = df_recent['YR'].astype(str) + " (" + df_recent['Season'] + ")"

    # 4. Metrics Display
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

    # 5. Clean Data Plotting
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    # Plot using index-based tracking to avoid date scattering issues
    x_positions = list(range(len(df_recent)))
    ax.plot(x_positions, df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Normal boundaries for threshold blocks
    ax.axhspan(0.5, 2.5, color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(-2.5, -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_ylim(-2.0, 2.0)
    
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 24 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Force ticks to map perfectly over the 24 intervals
    ax.set_xticks(x_positions)
    ax.set_xticklabels(df_recent['Timeframe'], rotation=45, ha='right', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)

    # 6. Debug / Raw Data View
    with st.expander("Show raw data for last 24 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
