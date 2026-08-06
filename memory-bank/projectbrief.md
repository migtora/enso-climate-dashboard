# Project Brief: ENSO RONI Dashboard

## Project Overview
This project is an automated, real-time dashboard built to track and visualize the **Relative Oceanic Niño Index (RONI)**, which monitors the El Niño and La Niña climate phases. It fetches official, live data directly from NOAA's servers.

## Core Requirements
- **Data Source**: Fetches live ASCII text data from the Climate Prediction Center of NOAA (`https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt`).
- **Data Processing**: Parses the space-delimited text format directly (columns: `SEAS`, `YR`, `ANOM`) without unnecessary melt operations.
- **Visualization**: Shows the last 24 measurement periods (2 years) with visual thresholds shading El Niño (>= 0.5°C), La Niña (<= -0.5°C), and Neutral zones.
- **UI Framework**: Built using Streamlit for clean layouts and real-time responsiveness.
- **Automation/Caching**: Caches the NOAA data daily (`ttl=86400`) to optimize feed requests.
- **Clean Layout**: Features metrics on the current ENSO phase and an optimized plot with uncluttered X-axis labels (rotated and showing every 3rd step).
