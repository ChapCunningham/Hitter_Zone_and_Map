import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Load CSV files and combine them
file_paths = ["Spring Intrasquads MASTER.csv"]  # Add more file paths if needed
dataframes = [pd.read_csv(fp, low_memory=False) for fp in file_paths]
data = pd.concat(dataframes, ignore_index=True)

# Standardize date format
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
data = data.dropna(subset=['Date'])
data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')

# Filter only "InPlay" pitch calls
data = data[data['PitchCall'] == 'InPlay']

# Define marker shapes based on pitch type
pitch_type_shapes = {
    'Fastball': 'circle',
    'Sinker': 'circle',
    'Cutter': 'triangle-up',
    'Slider': 'triangle-up',
    'Curveball': 'triangle-up',
    'Sweeper': 'triangle-up',
    'Splitter': 'square',
    'ChangeUp': 'square'
}

def get_marker_shape(pitch_type):
    return pitch_type_shapes.get(pitch_type, 'diamond')  # Default to diamond if not listed

# Streamlit UI
st.title("Hitting Summary Viewer (In-Play Data)")

# Date range selection
min_date, max_date = data['Date'].min(), data['Date'].max()
min_date, max_date = pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date()

date_range = st.slider(
    "Select Date Range:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

# Convert selected date range back to string format for filtering
start_date, end_date = date_range
start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')

# Apply the date filter
data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]

# Select batter
unique_batters = sorted(data['Batter'].unique())
selected_batter = st.selectbox("Select a Batter", options=unique_batters)

data = data[data['Batter'] == selected_batter]

# **Strike Zone Plot**
fig_strikezone = px.scatter(
    data,
    x='PlateLocSide', y='PlateLocHeight',
    color='TaggedPitchType',
    symbol='TaggedPitchType',
    symbol_map=pitch_type_shapes,
    hover_data={
        'Date': True,
        'Pitcher': True,
        'TaggedPitchType': True,
        'ExitSpeed': True,
        'Angle': True,
        'PlayResult': True,
    },
    title=f"Strike Zone Plot for {selected_batter}"
)

fig_strikezone.update_traces(marker=dict(size=10))
fig_strikezone.update_layout(
    xaxis_title="Plate Location Side",
    yaxis_title="Plate Location Height",
    xaxis=dict(range=[-1.5, 1.5]),
    yaxis=dict(range=[1, 4]),
)

st.plotly_chart(fig_strikezone)

# **Batted Ball Plot**
data['Bearing_rad'] = np.radians(data['Bearing'])
data['x'] = data['Distance'] * np.sin(data['Bearing_rad'])
data['y'] = data['Distance'] * np.cos(data['Bearing_rad'])

fig_batted_ball = px.scatter(
    data,
    x='x', y='y',
    color='PlayResult',
    symbol='PlayResult',
    hover_data={
        'Date': True,
        'Pitcher': True,
        'TaggedPitchType': True,
        'ExitSpeed': True,
        'Angle': True,
        'PlayResult': True,
    },
    title=f"Batted Ball Locations for {selected_batter}"
)

fig_batted_ball.update_traces(marker=dict(size=12))
fig_batted_ball.update_layout(
    xaxis_title="Field X Position",
    yaxis_title="Field Y Position",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    plot_bgcolor="white"
)

st.plotly_chart(fig_batted_ball)
