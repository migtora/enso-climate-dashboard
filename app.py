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
            
        # Read using standard whitespace splitting
        df = pd.read_csv(io.StringIO(response.text), sep=r'\s+', header=0)
        
        # Standardize column headers and strip hidden characters
        df.columns = df.columns.str.strip()
        
        # Expected column list
        seasons = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ']
        
        # Safety fallback: If standard headers fail due to top-line shift, enforce names directly
        if not all(col in df.columns for col in seasons):
            df = pd.read_csv(io.StringIO(response.text), sep=r'\s+', names=['YR'] + seasons, header=None, skiprows=1)
        
        # Drop any row that accidentally parsed header strings into data
        df = df[pd.to_numeric(df['YR'], errors='coerce').notnull()]
        df['YR'] = df['YR'].astype(int)
        
        # Melt data into a long, clean time series format
        df_long = pd.melt(df, id_vars=['YR'], value_vars=seasons, var_name='Season', value_name='RONI')
        
        # Map seasons to chronological order numbers so they sort properly
        season_order = {s: i for i, s in enumerate(seasons)}
        df_long['Season_Order'] = df_long['Season'].map(season_order)
        
        # Sort chronologically by Year, then by Season sequence
        df_long = df_long.sort_values(by=['YR', 'Season_Order']).dropna().reset_index(drop=True)
        
        # Convert RONI column to true numeric floats
        df_long['RONI'] = pd.to_numeric(df_long['RONI'], errors='coerce')
        df_long = df_long.dropna(subset=['RONI'])
        
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

    # 5. Generate the Clean Visual Chart
    fig, ax = plt.subplots(figsize=(12, 5.5))
    
    # Notice we use standard sequence index numbers for the X positions to ensure spacing layout
    x_positions = range(len(df_recent))
    ax.plot(x_positions, df_recent['RONI'], marker='o', color='#333333', linewidth=2, zorder=3)
    
    # Threshold Shading Zones
    ax.axhspan(0.5, max(2.0, latest_val + 0.2), color='#ffcccc', alpha=0.5, label='El Niño Threshold (≥ 0.5°C)')
    ax.axhspan(-0.5, 0.5, color='#f0f0f0', alpha=0.5, label='Neutral Zone')
    ax.axhspan(min(-2.0, latest_val - 0.2), -0.5, color='#cce6ff', alpha=0.5, label='La Niña Threshold (≤ -0.5°C)')
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_ylabel("SST Anomaly Delta (°C)")
    ax.set_title("Relative Oceanic Niño Index — Last 24 Measurement Periods")
    ax.legend(loc="upper left")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    
    # Map the true unique timeframe names exactly to each positional tick index
    ax.set_xticks(x_positions)
    ax.set_xticklabels(df_recent['Timeframe'], rotation=45, ha='right', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)

    # 6. Raw Data View Option
    with st.expander("Show raw data for last 24 periods"):
        st.dataframe(df_recent[['YR', 'Season', 'RONI']])
else:
    st.warning("No clean historical data loaded. Check parsing rules.")
