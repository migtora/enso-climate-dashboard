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
            
        # Split raw text purely by whitespace chunks to break through formatting alignment shifts
        tokens = response.text.split()
        
        # The table has 13 columns: YR + 12 seasons
        seasons = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
        
        # Find where the data actually starts by locating the first valid 4-digit year token
        start_idx = None
        for i, token in enumerate(tokens):
            if token.isdigit() and len(token) == 4 and int(token) >= 1900:
                # Double check if there are numeric values following it to confirm it's the table start
                start_idx = i
                break
                
        if start_idx == None:
            st.error("Could not locate the historical dataset sequence within the source file.")
            return None
            
        # Extract only the data chunks from that starting position onward
        data_tokens = tokens[start_idx:]
        
        # Group into rows of exactly 13 columns
        rows = []
        for i in range(0, len(data_tokens) - len(data_tokens) % 13, 13):
            rows.append(data_tokens[i:i+13])
            
        # Construct DataFrame cleanly
        df = pd.DataFrame(rows, columns=['YR'] + seasons)
        
        # Convert all values to floats, handling missing marker data gracefully
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df = df.dropna(subset=['YR'])
        df['YR'] = df['YR'].astype(int)
        
        # Melt to deep time series format
        df_long = pd.melt(df, id_vars=['YR'], value_vars=seasons, var_name='Season', value_name='RONI')
        
        # Establish chronologically stable sequence order sorting
        season_order = {s: i for i, s in enumerate(seasons)}
        df_long['Season_Order'] = df_long['Season'].map(season_order)
        df_long = df_long.sort_values(by=['YR', 'Season_Order']).dropna().reset_index(drop=True)
        
        return df_long
    except Exception as e:
        st.error(f"Error parsing NOAA data feed: {e}")
        return None

df_all = load_data()

if df_all is not None and not df_all.empty:
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

    # 5. Generate the Single Clean Plot
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    # Use exact integer step ranges for horizontal coordinates to stop point grouping overlap anomalies
    x_positions = list(range(len(df_recent)))
    ax.plot(x_positions, df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Threshold Shading
    ax.axhspan(0.5, max(2.0, latest_val + 0.2), color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(min(-2.0, latest_val - 0.2), -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 24 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Map label frames distinctly onto layout indexes
    ax.set_xticks(x_positions)
    ax.set_xticklabels(df_recent['Timeframe'], rotation=45, ha='right', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)

    # 6. Raw Data View Option
    with st.expander("Show raw data for last 24 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
else:
    st.warning("No clean historical data loaded. Check parsing rules.")
