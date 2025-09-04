import os
import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import matplotlib.colors as colors
import seaborn as sns
import plotly.express as px
import json

from dash import Dash, html, dcc, Output, Input

import warnings
warnings.filterwarnings("ignore")

app = Dash()

#colors = {
#  'eco_green': '#AFC912',
#  'forest_green': '#4C7A2E',
#  'earth_brown': '#7B5E34',
#  'harvest_yellow': '#F2D16B',
#  'neutral_light': '#F5F5F5',
#  'dark_text': '#333333',
#  'accent_warm': '#E07A5F'
#}

brand_colors = {
    "Medium violet red": "#af245c",
    "Dark khaki": "#aabf7e",
    "Seagreen": "#095d40",
    "Dark slate grey": "#0080a3",
    "White": "#ffffff",
    "Black": "#000000"
}

# Loading and Formatting MPI Data
path = "/Users/jemim/app_dev_EFS/assets/data/"
MPI = gpd.read_file(path+"Hanoi_districts_MPI.geojson")#.set_index('Dist_Name')
MPI['Normalized'] = MPI['Normalized'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Adding MPI Choropleth to the map
fig_ch = px.choropleth_mapbox(MPI, geojson=geojson, 
                    locations="Dist_Name", 
                    featureidkey="properties.Dist_Name",
                    color='Normalized',
                    color_continuous_scale="Reds",
                    opacity=0.7,
                    range_color=(0, 1),
                    labels={'Normalized':'MPI',
                            'Dist_Name':'District Name'},

                    mapbox_style="carto-positron",
                    zoom=8,
                    center={"lat": MPI.geometry.centroid.y.mean(), 
                            "lon": MPI.geometry.centroid.x.mean()}
                    )

fig_ch.update_layout(coloraxis_colorbar=None)

#fig_ch.update_layout(coloraxis_colorbar=dict(
#    title=None,
#    orientation='h',  # 'v' for vertical (default), 'h' for horizontal
#    thickness=20,
#    len=0.9,
#    x=0.5,  # position on x-axis (for horizontal orientation)
#    y=-0.1,   # position on y-axis
#    tickvals=[0, 0.5, 1],
#    ticktext=["Low", "Medium", "High"]
#))

fig_ch.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=0, b=0)
)

# Adding grouped bar chart of MDI variables per dist
df = pd.read_csv(path+"Hanoi_districts_MPI_long.csv")
variables = df['Variable'].unique()

app.layout = html.Div([

    # Main body (flex layout)
    html.Div([
        # Left panel: header, controls and bar chart stacked vertically

        html.Div([
            # Adding heading over the left panel screen to give map the full vertical height available
            html.Header(
                [
                    html.H1(
                        'EcoFoodSystems Dash Demo',
                        style={
                            'color': brand_colors['Black'],
                            'font-weight': 'bold',
                            #'font-size': '32px',
                            'margin': '0',
                            'padding': '10px',
                            'margin-left': '20px'
                        })
                ], style={
                        "backgroundColor": brand_colors['Dark khaki'],
                        "border-radius": "0 0 0 0",
                        "display": "flex",
                        "justify-content": "space-between",
                        "align-items": "center",
                        "border-radius": "8px",
                        "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                }),
                
            # Page description, dropdown and bar chart
            html.P('Please select a variable from the dropdown menu:'),
            dcc.Dropdown(
                id='variable-dropdown',
                options=[{'label': v, 'value': v} for v in variables],
                value=variables[0],
                style={"margin-bottom": "20px"}
            ),
            dcc.Graph(id='bar-plot',
                        style={
                        'padding': '0',
                        'margin': '0',
                        "border-radius": "8px",
                        "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                        })

        ], style={
            "width": "min(60vw, 600px)",
            "height": "90vh", 
            "padding": "10px",
            "backgroundColor": "#f9f9f9",
            "border-radius": "0",
            "margin": "0",
            #"box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "overflowY": "auto",
            "box-sizing": "border-box",
            "zIndex": 2,
            "position": "relative",
        }),


        # Right panel: map, full height
        html.Div([
            dcc.Graph(
                id='map',
                figure=fig_ch,
                style={"height": "100%",
                       "width": "100%",  # fill the parent div
                       "padding": "0",
                       "margin": "0"}
            ),
            html.Div("Legend text about MPI?...", style={
                "position": "absolute",
                "bottom": "30px",
                "left": "30px",
                "backgroundColor": "rgba(255,255,255,0.9)",
                "padding": "10px",
                "border-radius": "6px",
                "box-shadow": "0 2px 8px rgba(0,0,0,0.15)"
            })
        ], style={
            "flex": "1",
            "height": "100vh",
            "padding": "0",
            "margin": "0",
            "backgroundColor": brand_colors['White'],
            "border-radius": "0",
            "display": "flex",
            "alignItems": "stretch",
            "justifyContent": "center",
            "box-sizing": "border-box",
            "zIndex": 1,
            "position": "relative",
        })
    ], style={
        "display": "flex",
        "width": "100vw",
        "height": "100vh"
    }),

    # Footer
    html.Footer([
        #html.P("Websites, maybe Logos, Links?"),
        html.Div([
                html.Img(src="/assets/logos/DeSIRA.png", style={'height': '60px', 'margin': '0 10px'}),
                html.Img(src="/assets/logos/IFAD.png", style={'height': '50px', 'margin': '0 10px'}),
                html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '100px', 'margin': '0 10px'})
            ], style={"display": "flex", "align-items": "center"})

    ], style={
        "width": "100%",
        "height": "80px",
        "backgroundColor": brand_colors['Dark khaki'],
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "margin-top": "20px",
        "border-radius": "10px 10px 0 0"
    })
])


@app.callback(
    Output('bar-plot', 'figure'),
    Input('variable-dropdown', 'value')
)

def update_bar(selected_variable):
    # Sort by selected variable, descending
    filtered_df = df[df["Variable"]==selected_variable]
    sorted_df = filtered_df.sort_values('Value', ascending=False)
    fig = px.bar(
        sorted_df,
        x='Value',
        y='Dist_Name',
        orientation='h',
        hover_data=['Dist_Name'],
        labels={'Dist_Name': 'District',
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[brand_colors['Dark khaki']]
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                      height=25 * len(sorted_df),
                      hoverlabel=dict(
                        bgcolor="white",      # Tooltip background color
                        font_color="black",   # Tooltip text color
                        #font_family="Calibri"
    ))
    return fig

# Adding MPI map and linking it to the bar chart via click
@app.callback(
    Output('map', 'figure'),
    Input('bar-plot', 'clickData'),
    Input('variable-dropdown', 'value')
)

def update_map_on_bar_click(clickData, selected_variable):
    center = {
        "lat": MPI.geometry.centroid.y.mean(),
        "lon": MPI.geometry.centroid.x.mean()
    }
    zoom = 8

    MPI_display = MPI.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    # If a bar is clicked, zoom to that district
    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']  # y is Dist_Name for horizontal bar
        match = MPI[MPI['Dist_Name'] == selected_dist]
        if not match.empty:
            centroid = match.geometry.centroid
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            area = match.geometry.area.values[0]
            zoom = max(8, min(12, 12 - area * 150))  # Zoom in closer
            # Highlight: set opacity and line_width for the selected district
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'opacity'] = 1
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_width'] = 2


    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color='Normalized',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 1),
        labels={'Normalized':'MPI','Dist_Name':'District Name'},
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center
    )

    
    fig_ch.update_layout(coloraxis_colorbar=None)

    fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=0, b=0)
    )

    # Update per-feature opacity and line width upon click to highlight 
    fig.update_traces(
        marker=dict(
            opacity=MPI_display['opacity'],
            line=dict(width=MPI_display['line_width'], color='black')
        )
    )

    return fig


if __name__ == '__main__':
    app.run(debug=True)


                    #    [
                    #        'Food Systems Stakeholders',
                    #        'Multidimensional Poverty',
                    #        'Dietry Mapping & Affordability',
                    #        'Health & Nutrition',
                    #        'Food Flows, Supply & Value Chain',
                    #        'Climate Shocks and Resilience'
                    #    ]