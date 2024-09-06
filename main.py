import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os

# Load the dataset
# df = pd.read_csv('weatherHistory.csv')  # Update this line to load your dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the CSV file
csv_file_path = os.path.join(BASE_DIR, 'data', 'weatherHistory.csv')
df = pd.read_csv(csv_file_path)  
# Convert 'Formatted Date' to datetime, handling timezone information
df['Formatted Date'] = pd.to_datetime(df['Formatted Date'], utc=True)  # Set utc=True to handle timezone-aware datetimes

# Extract year and week from the date
df['Year'] = df['Formatted Date'].dt.year
df['Week'] = df['Formatted Date'].dt.to_period('W').apply(lambda r: r.start_time)

# Aggregate data by Year and Week, calculating the mean for numerical columns
df_weekly = df.groupby(['Year', 'Week']).agg({
    'Temperature (C)': 'mean',
    'Apparent Temperature (C)': 'mean',
    'Humidity': 'mean',
    'Wind Speed (km/h)': 'mean',
    'Precip Type': lambda x: x.mode()[0]  # Mode for categorical data
}).reset_index()

# Get unique years for the year dropdown
years = df['Year'].unique()

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Weather Patterns and Trends Visualization Dashboard'),

    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(years)],
        value=years[0],  # Default value
        style={'width': '50%'}
    ),

    html.Div([
        # First Column
        html.Div(dcc.Graph(id='time-series-plot'), style={'width': '100%'}),
    ], style={'display': 'flex', 'flex-direction': 'column', 'width': '100%'}),

    html.Div([
        # Second Column
        html.Div(dcc.Graph(id='precipitation-pie-chart'), style={'width': '50%'}),
        html.Div(dcc.Graph(id='temperature-bar-chart'), style={'width': '50%'}),
    ], style={'display': 'flex', 'width': '100%'}),

    html.Div([
        # Third Column
        html.Div(dcc.Graph(id='humidity-scatter-plot'), style={'width': '50%'}),
        html.Div(dcc.Graph(id='wind-speed-histogram'), style={'width': '50%'}),
    ], style={'display': 'flex', 'width': '100%'}),

    html.Div([
        # Fourth Column
        html.Div(dcc.Graph(id='temperature-histogram'), style={'width': '100%'}),
    ], style={'display': 'flex', 'flex-direction': 'column', 'width': '100%'})
])

# Define the callback to update the graphs based on the dropdown value
@app.callback(
    [Output('time-series-plot', 'figure'),
     Output('precipitation-pie-chart', 'figure'),
     Output('temperature-bar-chart', 'figure'),
     Output('humidity-scatter-plot', 'figure'),
     Output('wind-speed-histogram', 'figure'),
     Output('temperature-histogram', 'figure')],
    [Input('year-dropdown', 'value')]
)
def update_graphs(selected_year):
    # Filter the data based on the selected year
    filtered_df = df_weekly[df_weekly['Year'] == selected_year]

    # Create a long-format DataFrame for all numerical features
    features_to_plot = ['Temperature (C)', 'Apparent Temperature (C)', 'Humidity', 'Wind Speed (km/h)']
    df_long = filtered_df.melt(id_vars='Week', value_vars=features_to_plot,
                               var_name='Feature', value_name='Average Value')

    # Ensure data types are correct
    df_long['Week'] = pd.to_datetime(df_long['Week'])
    df_long['Average Value'] = pd.to_numeric(df_long['Average Value'], errors='coerce')

    # Create the time series line plot
    time_series_fig = px.line(df_long, x='Week', y='Average Value', color='Feature',
                             title=f'Average Values Over Time in {selected_year}')

    # Create the pie chart for precipitation types
    precip_type_counts = df[df['Year'] == selected_year]['Precip Type'].value_counts()
    precip_pie_fig = px.pie(names=precip_type_counts.index, values=precip_type_counts.values,
                           title=f'Precipitation Type Distribution in {selected_year}')

    # Create the bar chart for average temperature
    temp_avg = filtered_df[['Week', 'Temperature (C)']].copy()
    temp_avg.set_index('Week', inplace=True)
    temp_bar_fig = px.bar(temp_avg, x=temp_avg.index, y='Temperature (C)',
                          title=f'Weekly Average Temperature in {selected_year}')

    # Create the scatter plot for humidity vs. wind speed
    scatter_fig = px.scatter(filtered_df, x='Humidity', y='Wind Speed (km/h)',
                            title=f'Humidity vs. Wind Speed in {selected_year}')

    # Create the histogram for wind speed distribution
    wind_speed_histogram_fig = px.histogram(filtered_df, x='Wind Speed (km/h)',
                                            title=f'Wind Speed Distribution in {selected_year}')

    # Create the histogram for Temperature (C)
    temp_histogram_fig = px.histogram(filtered_df, x='Temperature (C)',
                                      title=f'Temperature Distribution in {selected_year}')

    return time_series_fig, precip_pie_fig, temp_bar_fig, scatter_fig, wind_speed_histogram_fig, temp_histogram_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
