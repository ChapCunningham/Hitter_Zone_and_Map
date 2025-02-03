import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Load CSV files and combine them
file_paths = ["Spring Intrasquads MASTER.csv", "filtered_fall_trackman.csv", "WINTER_ALL_trackman.csv"]
dataframes = [pd.read_csv(fp, low_memory=False) for fp in file_paths]
data = pd.concat(dataframes, ignore_index=True)

# Standardize date format
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
data = data.dropna(subset=['Date'])
data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')

# Filter only "InPlay" pitch calls
data = data[data['PitchCall'] == 'InPlay']

# Define consistent pitch type colors
pitch_type_colors = {
    'Fastball': 'red', 'Sinker': 'darkred', 'Cutter': 'blue',
    'Slider': 'darkblue', 'Curveball': 'purple', 'Sweeper': 'darkpurple',
    'Splitter': 'green', 'ChangeUp': 'darkgreen'
}

# Define marker shapes for pitch types
pitch_type_shapes = {
    'Fastball': 'circle', 'Sinker': 'circle', 'Cutter': 'triangle-up',
    'Slider': 'triangle-up', 'Curveball': 'triangle-up', 'Sweeper': 'triangle-up',
    'Splitter': 'square', 'ChangeUp': 'square'
}

# Define play result symbols
play_result_shapes = {
    'Out': 'x', 'Sacrifice': 'cross', 'Single': 'circle',
    'Double': 'square', 'Triple': 'triangle-up', 'HomeRun': 'diamond'
}

# Ensure categorical order for consistency
pitch_type_order = list(pitch_type_colors.keys())
play_result_order = ['Single', 'Double', 'Triple', 'HomeRun', 'Out']

# Streamlit UI
st.title("Hitting Summary Viewer (In-Play Data)")

# Date range selection
min_date, max_date = data['Date'].min(), data['Date'].max()
min_date, max_date = pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date()

date_range = st.slider(
    "Select Date Range:", min_value=min_date, max_value=max_date, value=(min_date, max_date)
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

# Track user selection using session state
if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = []

# Convert selected points to a highlighted boolean column
data['highlight'] = data.index.isin(st.session_state.selected_indices)

# **Strike Zone Plot with Clickable Points**
fig_strikezone = px.scatter(
    data, x='PlateLocSide', y='PlateLocHeight', color='TaggedPitchType',
    color_discrete_map=pitch_type_colors, symbol='TaggedPitchType',
    symbol_map=pitch_type_shapes, category_orders={'TaggedPitchType': pitch_type_order},
    hover_data={'Date': True, 'Pitcher': True, 'TaggedPitchType': True,
                'ExitSpeed': True, 'Angle': True, 'PlayResult': True},
    title=f"Strike Zone Plot for {selected_batter}"
)

# Strike zone box
fig_strikezone.add_shape(go.layout.Shape(type="rect", x0=-0.83, x1=0.83, y0=1.5, y1=3.3775,
                                         line=dict(color="black", width=2)))

# Update marker size based on selection
fig_strikezone.update_traces(
    marker=dict(size=data['highlight'].apply(lambda x: 14 if x else 10))
)

st.plotly_chart(fig_strikezone, use_container_width=True)

# **Batted Ball Plot with Clickable Points**
data['Bearing_rad'] = np.radians(data['Bearing'])
data['x'] = data['Distance'] * np.sin(data['Bearing_rad'])
data['y'] = data['Distance'] * np.cos(data['Bearing_rad'])

fig_batted_ball = px.scatter(
    data, x='x', y='y', color='TaggedPitchType',
    color_discrete_map=pitch_type_colors, category_orders={'TaggedPitchType': pitch_type_order},
    symbol='PlayResult', symbol_map=play_result_shapes,
    hover_data={'Date': True, 'Pitcher': True, 'TaggedPitchType': True,
                'ExitSpeed': True, 'Angle': True, 'PlayResult': True},
    title=f"Batted Ball Locations for {selected_batter}"
)

# Update marker size based on selection
fig_batted_ball.update_traces(
    marker=dict(size=data['highlight'].apply(lambda x: 14 if x else 10))
)

st.plotly_chart(fig_batted_ball, use_container_width=True)

# **Handle User Clicks**
selected_data = st.session_state.get("selected_indices", [])

if st.button("Clear Selections"):
    st.session_state.selected_indices = []

# Capture selected data points
selected_points = st.session_state.get("selected_data", [])

if selected_points:
    selected_indices = [data.index[data['Date'] == row['Date']].tolist()[0] for row in selected_points]
    st.session_state.selected_indices = selected_indices
