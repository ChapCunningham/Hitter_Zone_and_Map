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

# Ensure consistent category ordering AFTER filtering
pitch_type_order = ['Fastball', 'Sinker', 'Cutter', 'Slider', 'Curveball', 'Sweeper', 'Splitter', 'ChangeUp']
play_result_order = ['Single', 'Double', 'Triple', 'HomeRun', 'Out']


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

# **Strike Zone Plot with Strike Zone Box**
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

fig_strikezone.add_shape(
    go.layout.Shape(
        type="rect",
        x0=-0.83, x1=0.83, y0=1.5, y1=3.3775,
        line=dict(color="black", width=2),
    )
)
fig_strikezone.update_traces(marker=dict(size=10))
fig_strikezone.update_layout(
    xaxis_title="Plate Location Side",
    yaxis_title="Plate Location Height",
    xaxis=dict(range=[-2, 2]),
    yaxis=dict(range=[1.15, 3.75]),
)

st.plotly_chart(fig_strikezone)

# **Batted Ball Plot with Field Outline and Foul Lines**
data['Bearing_rad'] = np.radians(data['Bearing'])
data['x'] = data['Distance'] * np.sin(data['Bearing_rad'])
data['y'] = data['Distance'] * np.cos(data['Bearing_rad'])

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


fig_batted_ball = px.scatter(
    data,
    x='x', y='y',
    color='TaggedPitchType',
    color_discrete_map=pitch_type_colors,  # Apply fixed colors
    category_orders={'TaggedPitchType': pitch_type_order, 'PlayResult': play_result_order},
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
