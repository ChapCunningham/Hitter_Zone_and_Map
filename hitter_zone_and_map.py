import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Load CSV files and combine them
file_paths = ["Spring Intrasquads MASTER.csv","filtered_fall_trackman.csv","WINTER_ALL_trackman.csv"]  # Add more file paths if needed
dataframes = [pd.read_csv(fp, low_memory=False) for fp in file_paths]
data = pd.concat(dataframes, ignore_index=True)

# Standardize date format
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
data = data.dropna(subset=['Date'])
data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')

# Filter only "InPlay" pitch calls
data = data[data['PitchCall'] == 'InPlay']

# Define marker shapes based on play result
play_result_shapes = {
    'Single': 'circle',
    'Double': 'square',
    'Triple': 'triangle-up',
    'HomeRun': 'diamond',
    'Out': 'x'
}

# Define consistent color mapping for TaggedPitchType
pitch_type_colors = {
    'Fastball': 'red',
    'Sinker': 'darkred',
    'Cutter': 'blue',
    'Slider': 'darkblue',
    'Curveball': 'purple',
    'Sweeper': 'darkpurple',
    'Splitter': 'green',
    'ChangeUp': 'darkgreen'
}

def get_marker_shape(play_result):
    return play_result_shapes.get(play_result, 'circle')  # Default to circle if not listed

# Ensure consistent category ordering
pitch_type_order = ['Fastball', 'Sinker', 'Cutter', 'Slider', 'Curveball', 'Sweeper', 'Splitter', 'ChangeUp']
play_result_order = ['Single', 'Double', 'Triple', 'HomeRun', 'Out']

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

# **Batted Ball Plot with Field Outline and Foul Lines**
data['Bearing_rad'] = np.radians(data['Bearing'])
data['x'] = data['Distance'] * np.sin(data['Bearing_rad'])
data['y'] = data['Distance'] * np.cos(data['Bearing_rad'])

fig_batted_ball = px.scatter(
    data,
    x='x', y='y',
    color='TaggedPitchType',
    color_discrete_map=pitch_type_colors,  # Ensure consistent colors
    symbol='PlayResult',
    symbol_map=play_result_shapes,
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

# Custom Legend for Pitch Type
pitch_legend = [go.Scatter(
    x=[None], y=[None],
    mode='markers',
    marker=dict(size=10, color=color),
    name=pitch_type
) for pitch_type, color in pitch_type_colors.items()]

# Custom Legend for Play Result
play_legend = [go.Scatter(
    x=[None], y=[None],
    mode='markers',
    marker=dict(size=10, color='black', symbol=symbol),
    name=play_result
) for play_result, symbol in play_result_shapes.items()]

for trace in pitch_legend + play_legend:
    fig_batted_ball.add_trace(trace)

# Outfield fence
foul_pole_left = 330
lc_gap = 365
cf = 390
rc_gap = 365
foul_pole_right = 330
angles = np.linspace(-45, 45, 500)
distances = np.interp(angles, [-45, -30, 0, 30, 45], [foul_pole_left, lc_gap, cf, rc_gap, foul_pole_right])
x_outfield = distances * np.sin(np.radians(angles))
y_outfield = distances * np.cos(np.radians(angles))
fig_batted_ball.add_trace(go.Scatter(x=x_outfield, y=y_outfield, mode='lines', line=dict(color='black')))

# Infield diamond
infield_side = 90
bases_x = [0, infield_side, 0, -infield_side, 0]
bases_y = [0, infield_side, 2 * infield_side, infield_side, 0]
fig_batted_ball.add_trace(go.Scatter(x=bases_x, y=bases_y, mode='lines', line=dict(color='brown', width=2)))

# Foul lines
foul_x_left = [-foul_pole_left * np.sin(np.radians(45)), 0]
foul_y_left = [foul_pole_left * np.cos(np.radians(45)), 0]
foul_x_right = [foul_pole_right * np.sin(np.radians(45)), 0]
foul_y_right = [foul_pole_right * np.cos(np.radians(45)), 0]
fig_batted_ball.add_trace(go.Scatter(x=foul_x_left, y=foul_y_left, mode='lines', line=dict(color='black', dash='dash')))
fig_batted_ball.add_trace(go.Scatter(x=foul_x_right, y=foul_y_right, mode='lines', line=dict(color='black', dash='dash')))

fig_batted_ball.update_traces(marker=dict(size=12))
fig_batted_ball.update_layout(
    xaxis_title="Field X Position",
    yaxis_title="Field Y Position",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    plot_bgcolor="white"
)

st.plotly_chart(fig_batted_ball)
