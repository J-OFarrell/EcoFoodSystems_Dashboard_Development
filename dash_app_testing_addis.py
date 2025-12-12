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
import dash
from dash import Dash, html, dcc, Output, Input, State, callback, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash_extensions.javascript import assign
import random
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import plotly.graph_objects as go
from lorem_text import lorem

import warnings
warnings.filterwarnings("ignore")

from dashboard_components import create_nutrition_kpi_card

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

#colors = {
#  'eco_green': '#AFC912',
#  'forest_green': '#4C7A2E',
#  'earth_brown': '#7B5E34',
#  'harvest_yellow': '#F2D16B',
#  'neutral_light': '#F5F5F5',
#  'dark_text': '#333333',
#  'accent_warm': '#E07A5F'
#}


green_gradient = [
    "#095d40",
    "#206044",
    "#3a6649",
    "#547d5b",
    "#6f946d",
    "#8aa97f",
    "#a5be91",
    "#b8d099",
    "#c1d88e",
    "#d1e7a8"
]

brand_colors = {    'Black':         '#333333',
                    "Brown":         "#313715",
                    "Red":           "#A80050",
                    "Dark green":    "#939f5c",
                    "Mid green":     "#bbce8a",
                    "Light green":   "#E8F0DA",
                    "White":         "#ffffff"  
}

greens_pie_palette = [
    brand_colors['Light green'],   # "#E8F0DA"
    brand_colors['Mid green'],     # "#bbce8a"
    brand_colors['Dark green'],    # "#939f5c"
    "#b7c49a",                     # lighter tint of Dark green
    "#d6e5b8",                     # lighter tint of Mid green
    "#e3f6d5",                     # very light green
    "#c1d88e",                     # soft khaki-green
    "#d1e7a8",                     # pastel green
    "#aabf7e",                     # olive green
    "#8aa97f",                     # muted green
]

reds_pie_palette = [
    "#a80050",   # main brand red
    "#84003d",   # deep accent red
    "#C97A9A",   # soft pink
    "#E07A5F",   # warm accent
    "#F2D16B",   # harvest yellow (for contrast)
    "#F5F5F5",   # neutral light
    "#7B5E34",   # earth brown
    "#C97A9A",   # repeat pink
    "#E07A5F",   # repeat accent
    "#F2D16B"    # repeat yellow
]

plotting_palette_cat = [
    "#a80050",  
    "#84003d",   
    "#F5F5F5",   
    '#E8F0DA',
    "#bbce8a",
    "#939f5c",
    "#E07A5F",   
    "#d33030",
]

tabs = [
        'Food Systems Stakeholders',                #Populated
        'Food Flows, Supply & Value Chains',        #Populated
        'Sustainability Metrics & Indicators',      #Currently empty
        'Multidimensional Poverty',                 #Populated
        'Resilience to Food System Shocks',         #In progress
        'Dietary Mapping & Affordability',          #Semi-Populated (In development)
        'Food Losses & Waste',                      #Currently empty
        'Food System Policies',                     #Currently empty
        'Health & Nutrition',                       #Populated
        'Environmental Footprints of Food & Diets', #Currently empty 
        'Behaviour Change Tool (AI Chatbot & Game)' #Currently empty (In development)
        ]


# -------------------------- Loading and Formatting All Data ------------------------- #

homepath = os.getcwd()

# Loading and Formatting MPI Data
path = homepath + "/assets/data/"
MPI = gpd.read_file(path+"/addis_adm3_mpi.geojson")#.set_index('Dist_Name')
MPI['MPI'] = MPI['MPI'].astype(float)
MPI['Dist_Name'] = MPI['Dist_Name'].astype(str)
geojson = json.loads(MPI.to_json())

# Loading and Formatting MPI CSV Data=
df_mpi = pd.read_csv(path+"addis_mpi_long.csv")
variables = df_mpi['Variable'].unique()

# Loading and Formatting Food Systems Stakeholders Data
df_sh = pd.read_csv(path+"/addis_stakeholders_cleaned.csv").dropna(how='any').astype(str)

# Format Website column as clickable markdown links
if 'Website' in df_sh.columns:
    df_sh['Website'] = df_sh['Website'].apply(
        lambda x: f'[🔗]({x})' if x and x.startswith('http') else '--'
    )

# Pre-calculate fixed column widths (6px per character, min 80px, max 200px)
column_widths = {}
for col in df_sh.columns:
    max_len = max(len(str(col)), df_sh[col].astype(str).str.len().max())
    column_widths[col] = min(max(max_len * 6, 80), 200)

total_table_width = sum(column_widths.values())

# Loading GeoJSON files for Food Outlets
outlets_path = "/Users/jemimaofarrell/Documents/Python/EcoFoodSystems/EcoFoodSystems_Dashboard_Development/assets/data/jsons_addis_foodoutlets/"
outlets_geojson_files = sorted(os.listdir(outlets_path))

# Loading and Formatting Food Environment Choropleth Data
food_env_path = path + "addis_diet_env_mapping.geojson"
gdf_food_env = gpd.read_file(food_env_path).to_crs('EPSG:4326')

# Define food environment metrics and their labels
cols_food_env = ['density_healthyout', 'density_unhealthyout', 'density_mixoutlets',
                 'ratio_obesogenic', 'pct_access_healthy', 'ptc_access_unhealthy']

data_labels_food_env = ['Healthy Outlet Density', 'Unhealthy Outlet Density', 'Mixed Outlet Density',
                        'Obesogenic Ratio', 'Percent Access to Healthy Food', 'Percent Access to Unhealthy Food']

# Define which metrics are "good" when higher (True) or "bad" when higher (False)
metric_direction = {
    'Count_healthy': True,
    'Count_UnhealthyOutlets': False,
    'Count_MixOutlets': None,
    'density_healthyout': True,
    'density_unhealthyout': False,
    'density_mixoutlets': None,
    'ratio_obesogenic': False,
    'pop_sum': None,
    'density_pop_healthy': True,
    'density_pop_unhealthy': False,
    'total_density_pop': None,
    'acc_healthyaccess_pop_healthysum': True,
    'acc_unhealthyaccess_unhealthy_popsum': False,
    'pct_access_healthy': True,
    'ptc_access_unhealthy': False
}

# Color schemes for choropleth
green_scale = ['#e3f6d5', '#c1d88e', '#a5be91', '#6f946d', '#3a6649']
red_scale = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
grey_scale = ['#f7f7f7', '#d9d9d9', '#bdbdbd', '#969696', '#636363']

# Loading supply flow data for Sankey Diagram
df_sankey = pd.read_csv(path+'/hanoi_supply.csv')

df_policies = pd.read_csv(path+'/addis_policy_database.csv').drop('Unnamed: 0',axis=1)

df_indicators = pd.read_csv(path+'/addis_policy_database_expanded_sdg.csv')

# Create SDG logos as list of numbers for rendering
def get_sdg_numbers(row):
    sdg_cols = ['SDG_1', 'SDG_2', 'SDG_3', 'SDG_4', 'SDG_5']
    sdg_numbers = []
    for col in sdg_cols:
        if pd.notna(row[col]) and str(row[col]).strip():
            # Extract just the number (e.g., "1.3.1" -> "1", "2.1" -> "2")
            sdg_num = str(row[col]).split('.')[0]
            if sdg_num.isdigit() and sdg_num not in sdg_numbers:
                sdg_numbers.append(sdg_num)
    return ', '.join(sdg_numbers) if sdg_numbers else '--'

df_indicators['SDG Numbers'] = df_indicators.apply(get_sdg_numbers, axis=1)

df_env = pd.read_csv(path+'/addis_lca_pivot.csv')
df_lca = df_env  # Alias for compatibility

# -------------------------- Defining Custom Styles ------------------------- #

tabs_style = {
                "backgroundColor": brand_colors['Mid green'],
                "color": brand_colors['Brown'],
                "width":"100%",
                "margin-bottom": "4px",
                "borderRadius": "8px",
                "padding": "6px 4px",
                "fontWeight": "bold",
                "textAlign": "left",
                "fontSize": "clamp(0.6em, 1vw, 1.1em)",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                "border": "none",
                "textDecoration": "none",
                "whiteSpace": "normal",
                "box-sizing": "border-box",
                "maxWidth": "90%",
                "wordBreak": "normal"
            }

kpi_card_style ={"textAlign": "center", 
                "backgroundColor": brand_colors['White'], 
                "color":brand_colors['Brown'],
                "font-weight":"bold",
                "border-radius": "8px",
                "padding":"10px",
                "margin-bottom":"10px",
                "flexDirection": "column",
                "border": "2px solid " + brand_colors['White'],
                }

kpi_card_style_2 = {
                "textAlign": "center",
                "backgroundColor": brand_colors['White'],
                "borderRadius": "12px",
                "boxShadow": "0 4px 16px rgba(0,0,0,0.10)",
                "padding": "clamp(4px, 3vw, 12px)", 
                "padding":"6px",
                "marginBottom": "12px",
                "width": "100%",
                #"maxWidth": "350px",
                "height": "auto",
                #"minWidth": "220px"
            }

header_style = {"color": brand_colors['Brown'], 
                'fontWeight': 'bold',
                "margin": "0", 
                'textAlign': 'center',
                "fontSize": "clamp(0.8em, 3vw, 1.25em)",
                'whiteSpace': 'normal',
                }

card_style = {
    "backgroundColor": brand_colors['White'],
    "border-radius": "10px",
    "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
    "padding": "20px",  # Increase padding for consistency
    "margin-bottom": "15px"
}


# ----------------------- App Layout Components -------------------------- #

sidebar = dbc.Card([
    #html.Img(src="/assets/logos/temp_efs_logo.png", style={"width": "40%", "margin-bottom": "10px", "justifyContent": "center"}),
    dbc.Nav([
        dbc.NavItem(dbc.NavLink("Food Systems Stakeholders", id="tab-1-stakeholders", href="#", active="exact"), style=tabs_style),                         # Populated
        dbc.NavItem(dbc.NavLink("Food Flows, Supply & Value Chains", id="tab-2-supply", href="#", active="exact"), style=tabs_style),                       # Suplemented with Hanoi Data    
        dbc.NavItem(dbc.NavLink("Sustainability Metrics & Indicators", id="tab-3-sustainability", href="#", active="exact"), style=tabs_style),             # Empty!
        dbc.NavItem(dbc.NavLink("Multidimensional Poverty", id="tab-4-poverty", href="#", active="exact"), style=tabs_style),                               # Populated
        dbc.NavItem(dbc.NavLink("Labour, Skills & Green Jobs", id="tab-5-labour", href="#", active="exact"), style=tabs_style),                             # Empty!
        dbc.NavItem(dbc.NavLink("Resilience to Food System Shocks", id="tab-6-resilience", href="#", active="exact"), style=tabs_style),                    # Empty!
        dbc.NavItem(dbc.NavLink("Dietary Mapping & Affordability", id="tab-7-affordability", href="#", active="exact"), style=tabs_style),                  # Populated
        dbc.NavItem(dbc.NavLink("Food Losses & Waste", id="tab-8-losses", href="#", active="exact"), style=tabs_style),                                     # Empty!
        dbc.NavItem(dbc.NavLink("Food System Policies", id="tab-9-policies", href="#", active="exact"), style=tabs_style),                                  # In progress
        dbc.NavItem(dbc.NavLink("Health & Nutrition", id="tab-10-nutrition", href="#", active="exact"), style=tabs_style),                                  # Populated
        dbc.NavItem(dbc.NavLink("Environmental Footprints of Food & Diets", id="tab-11-footprints", href="#", active="exact"), style=tabs_style),           # Empty!
        dbc.NavItem(dbc.NavLink("Behaviour Change Tool (AI Chatbot & Game)", id="tab-12-behaviour", href="#", active="exact"), style=tabs_style),           # Empty!
    ], 
    vertical="md", 
    pills=True, 
    fill=True,
    style={"marginTop": "20px",
           "alignItems": "center",
           "textAlign": "center",
           "zIndex": 1000})

], style={
    #"backgroundColor": brand_colors['Light green'],
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "borderRadius": "12px",
    "padding": "10px",
    "height": "100%",
    "width": "100%",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "flex-start",
    "overflowY": "auto",  
    "backgroundImage": "url('/assets/photos/urban_food_systems_6.jpg')",  
    "backgroundSize": "cover",        
    "backgroundPosition": "center",  
    "backgroundRepeat": "no-repeat" ,
})

footer = html.Footer([
            html.Div([
            html.Img(src="/assets/logos/DeSIRA.png", style={'height': '60px', 'margin': '0 30px'}),
            html.Img(src="/assets/logos/IFAD.png", style={'height': '65px', 'margin': '0 30px'}),
            html.Img(src="/assets/logos/Rikolto.png", style={'height': '40px', 'margin': '0 30px'}),
            html.Img(src="/assets/logos/RyanInstitute.png", style={'height': '60px', 'margin': '0 30px'})
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "baseline",
                "margin": "20px 0px",
            })
        ])
   

# ------------------------- Main app layout ------------------------- #

def landing_page_layout():
    tab_labels = [
        "Food Systems Stakeholders", "Food Flows, Supply & Value Chains", "Sustainability Metrics / Indicators", "Multidimensional Poverty",
        "Labour, skills & green jobs", "Resilience to Food System Shocks", "Dietary Mapping & Affordability", "Food Losses & Waste",
        "Food System Policies", "Health & Nutrition", "Environmental Footprints of Food & Diets", "Behaviour Change Tool (AI Chatbot & Game)"
    ]

    tab_ids = [
        "stakeholders", "supply", "sustainability", "poverty",
        "labour", "resilience", "affordability", "losses",
        "policies", "nutrition", "footprints", "behaviour"]

    white_tab_bg, grey_tab_bg = "rgba(255, 255, 255, 0.7)", "rgba(173, 181, 189, 0.7)"
    background_colours = {
        "stakeholders":white_tab_bg, 
        "supply":white_tab_bg,
        "sustainability":white_tab_bg, 
        "poverty":white_tab_bg,
        "labour":grey_tab_bg,
        "resilience":grey_tab_bg, 
        "affordability":white_tab_bg, 
        "losses":grey_tab_bg,
        "policies":white_tab_bg, 
        "nutrition":white_tab_bg, 
        "footprints":white_tab_bg, 
        "behaviour":grey_tab_bg
    }
    
    # Create grid items
    grid_items = []
    for i, (tab_id, label) in enumerate(zip(tab_ids, tab_labels)):
        grid_items.append(
            dbc.Card([
                dbc.Button(label, id=f"tab-{i+1}-{tab_id}", color="light", 
                           className="dash-landing-btn",
                           style={
                                "width": "100%",
                                "height": "100%",
                                "fontWeight": "bold",
                                "fontSize": "clamp(1.25em, 1.3em, 2.25em)",
                                "color": brand_colors['Brown'],
                                "backgroundColor": background_colours[tab_id],
                                "borderRadius": "10px",
                                "boxShadow": "0 4px 8px rgba(0,0,0,0.08)",
                                "border": f"2px solid {brand_colors['White']}",
                                "whiteSpace": "normal",
                                "padding": "18px 8px",
                }), 
            ], style={
                "height": "25vh",
                "backgroundColor": "rgba(255, 255, 255, 0.5)",
                "borderRadius": "10px",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                "margin": "10px"
            })
        )

    # Arrange grid items in 4 columns x 3 rows
    grid_layout = html.Div([
        dbc.Row([
            dbc.Col(grid_items[0], width=3),
            dbc.Col(grid_items[1], width=3),
            dbc.Col(grid_items[2], width=3),
            dbc.Col(grid_items[3], width=3),
        ], style={"marginBottom": "0"}),
        dbc.Row([
            dbc.Col(grid_items[4], width=3),
            dbc.Col(grid_items[5], width=3),
            dbc.Col(grid_items[6], width=3),
            dbc.Col(grid_items[7], width=3),
        ], style={"marginBottom": "0"}),
        dbc.Row([
            dbc.Col(grid_items[8], width=3),
            dbc.Col(grid_items[9], width=3),
            dbc.Col(grid_items[10], width=3),
            dbc.Col(grid_items[11], width=3),
        ], style={"marginBottom": "0"}),
    ], style={"width": "100%", "margin": "0 auto", "padding": "0 4px"})

    return html.Div([
        # Logo and Title
        html.Div([
                html.H1("EcoFoodSystems Dashboard", style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "fontSize": "2.75em",
                    "margin-bottom": "30px",
                }),

            html.P("EcoFoodSystems takes a food systems research approach to enable transitions towards diets that are more sustainable, healthier and affordable for consumers in city regions",
                style={
                    "color": brand_colors['Brown'],
                    "fontSize": "1em",
                    "textAlign": "center",
                    "maxWidth": "800px",
                    "margin-bottom": "30px",
               }
            ),

        ], style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "paddingTop": "40px",
        }),

        # Tab Grid
        html.Div([grid_layout], style={ "width": "100%", 
                                        "height":"auto",
                                        "display": "block",
                                        "marginTop": "auto",
                                        "backgroundImage": "url('/assets/photos/addis_header.png')",  
                                        "backgroundSize": "cover",        # Image covers the whole area
                                        "backgroundPosition": "center",   # Center the image
                                        "backgroundRepeat": "no-repeat"   # Don't repeat the image
                                            }),

        # Footer logos (optional)
        footer

    ], style={
        "backgroundColor": brand_colors['Light green'],
        "height": "100vh",
        "width": "100vw",
        "padding": "0",
        "margin": "0",
        "boxSizing": "border-box",
        'overflowY':'auto'
    })


# ------------------------- Defining tab layouts ------------------------- #

def stakeholders_tab_layout():
    return html.Div([

        html.Div([sidebar], style={
                                    "width": "15%",
                                    "height": "100%",
                                    "display": "flex",
                                    "vertical-align":'top',
                                    "flexDirection": "column",
                                    "justifyContent": "flex-start",
                                    }), # End of sidebar div

        # Left Panel
        html.Div([

            # Card 2: Filter Dropdown
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                    html.P("Filter Database by:", 
                            style={     "margin": "0 12px 0 0", 
                                        'fontSize': 'clamp(0.8em, 1em, 1.1em)',
                                        "whiteSpace": "nowrap"
                                        }),
                                        
                    dcc.Dropdown(
                        id='pie-filter-dropdown',
                        options=[
                            {'label': 'Primary Sector', 'value': 'Sector'},
                            {'label': 'Area of Activity', 'value': 'Area'},
                            {'label': 'Scale of Activity', 'value': 'Scale'}
                        ],
                        value='Sector',
                        clearable=False,
                        style={"margin-bottom": "0", 
                                'fontSize': 'clamp(0.8em, 1em, 1.1em)',
                                "minWidth": "180px"}
                    )
                    ], style={  "display":'flex',
                                "flexDirection":'row',
                                "alignItems": "center",
                                'width':'100%'})
                ])
            ], style={  "height": "auto", 
                        "padding":"2px" ,
                        "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                        'margin-bottom': '15px',
                        "backgroundColor": brand_colors['White'],
                        "border-radius": "10px"
                        }),

            # Card 3: Pie Chart
            dbc.Card([
                dbc.CardBody([
                    html.Div([html.P("Select a slice of the pie chart to filter the database.", 
                                    style={     "margin": "0 6px", 
                                                'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "center",
                                                "whiteSpace": "normal",
                                                "fontStyle": "italic"
                                                })
                              ], style={"width":"100%",
                                        "marginBottom":"6px"}),
                    dcc.Graph(id='piechart', 
                              style={
                                "flex": "1 1 auto",
                                "height":"90%",
                                'padding': '4px',
                                'margin': '0',
                                #"border-radius": "8px",
                                #"box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                                })
                ],style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "100%"             
                        })
            ], style={  "height": "60%", 
                        "padding":"6px" ,
                        "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                        "backgroundColor": brand_colors['White'],
                        "border-radius": "10px"}),
            dcc.Store(id='selected_slice', data=None)
        ], style={
            #"flex": "1 1 30%",
            "maxWidth": "30%",
            "height": "100%",
            "padding": "10px",
            "margin": "0",
            "border-radius": "10px",
            #"backgroundColor": brand_colors['Light green'],
            "display": "flex",
            "flexDirection": "column"
        }),

        # Right Panel: Table 
        html.Div([
            dbc.Card([
                #dbc.CardHeader("Stakeholder Database"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='sh_table',
                        data=df_sh.to_dict('records'),
                        columns=[
                            {"name": str(i), "id": str(i), "presentation": "markdown"} 
                            if i == "Website" 
                            else {"name": str(i), "id": str(i)} 
                            for i in df_sh.columns
                        ],
                        page_size=11,
                        page_action='native',
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'nowrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'fontSize': 'clamp(0.7em, 1vw, 1em)',
                            'minWidth': '120px',
                            'maxWidth': '250px',
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        tooltip_data=[
                            {
                                column: {'value': str(row[column]), 'type': 'markdown'}
                                for column in df_sh.columns
                            } for row in df_sh.to_dict('records')
                        ],
                        tooltip_duration=None,
                        css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: ' +brand_colors['Light green']+ '; color: '+brand_colors['Black']+'; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px '+brand_colors['Black']+';'
                        }],
                        style_table={  
                            'overflowX': 'auto',
                            'width': '100%',
                        }
                    )
                ],style={"height": "auto",
                         "overflowY":"auto",
                         "display": "flex", 
                         "flexDirection": "column"})

            ], style={"height": "auto",
                      "overflowY":"auto",
                      "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                      "backgroundColor": brand_colors['White'],
                      "border-radius": "10px",
                      "padding": "10px"
                    }),
        ], style={
            "flex": "1 1 50%",
            #"backgroundColor": brand_colors['Light green'],
            #"width": "50%",
            "height": "90%",
            "display": "flex",
            "flexDirection": "column",
            "overflow":'hidden',
            "border-radius": "10px",
            'margin':"10px 2px 10px 10px"
        })

    ], style={  "display": "flex", 
                "width": "100%", 
                "height": "100%", 
                "backgroundColor": brand_colors['Light green']
              })

def supply_tab_layout():
    return html.Div([

            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start"}), # End of sidebar div

            # Left Panel
            html.Div([
    
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Flow", className="card-title", style={
                                                                            "fontWeight": "normal",
                                                                            "fontSize": "clamp(0.6em, 0.8em, 1.2em)",
                                                                            "color": brand_colors['Brown'],
                                                                            "marginBottom": "4px"
                                                                        }),
                        html.H1(id="kpi-total-flow", className="card-text", style={
                                                                                "fontWeight": "bold",
                                                                                "fontSize": "clamp(1.2em, 2em, 2.8em)",
                                                                                "color": brand_colors['Red'],
                                                                                "margin": "0"
                                                                        }),
                        html.H5("tons", style={
                                                    "fontSize": "clamp(0.6em, 0.8em, 1em)",
                                                    "color": brand_colors['Brown'],
                                                    "marginTop": "4px",
                                                    "fontWeight": "normal",
                                                })
                                ])
                            ], style={**kpi_card_style_2}),

                dbc.Card([
                    dbc.CardBody([
                        html.H5("Urban Share", className="card-title", style={
                                                                                "fontWeight": "normal",
                                                                                "fontSize": "clamp(0.6em, 0.8em, 1.2em)",
                                                                                "color": brand_colors['Brown'],
                                                                                "marginBottom": "10px"
                                                                            }),



                        dcc.Graph(id="urban-indicator", style={"height": "clamp(80px, 10vh, 200px)"}, config={"displayModeBar": False})
                                ])
                ], style={**kpi_card_style_2}),

            ], style={
                "flex": "0 0 20%",  # Changed: Narrow left column for KPI cards
                #"width":"80%",
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "padding": "10px",
                "margin-left":"20px",
                "alignItems": "center",
                "marginBottom": "auto" 
            }),

            # Sankey + Slider + Footnote (right)
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id="sankey-graph", 
                                    style={"width": "100%", "height":"70vh"}  
                                )
                            ),
                        ], style={"width": "100%"}),

                        # Info button (positioned absolute in top right)
                        html.Div([
                            dbc.Button("ⓘ", id="sankey-info-btn", style={
                                "fontSize": "1.5em",
                                "color": brand_colors['Red'],
                                "background": "none",
                                "border": "none",
                                "padding": "0",
                                "cursor": "pointer"
                            }),
                            dbc.Tooltip(
                                "Data Source: General Statistics Office of Vietnam (GSO). 2025. Production of paddy by province. Consulted on: June 2025. Link: https://www.nso.gov.vn/en/agriculture-forestry-and-fishery/. Estimation method: Trade attractiveness method, including two steps as follows: A) Estimation of Rice Net Supply (Consumption – Production) for every province, based on Consumption (Population * Consumption per person), and Production (Paddy production/Live weight/Raw production * Conversion rate). B) Distribute the rice consumption of Hanoi, considering: Province Production, National Production, and International Import.",
                                target="sankey-info-btn",
                                placement="bottom",
                                style={"fontSize": "0.5em", "maxWidth": "500px"}
                            )
                        ], style={
                            "position": "absolute",
                            "top": "12px",
                            "right": "18px",
                            "zIndex": 10
                        }),

                        html.Div([dcc.Slider(
                            id='slider', min=2010, max=2022, value=2022, step=2,
                            marks={year: str(year) for year in range(2010,2023,2)},
                            tooltip={"placement": "bottom", "always_visible": True},
                            updatemode='mouseup'
                            )
                        ], style={"margin-top":"10px", 
                                       "color":brand_colors['Brown'],
                                       "width": "100%", 
                                       "height":"10%"}),

                    ],style={"display": "flex", "flexDirection": "column", "height": "100%"})
                ],style={**card_style, "height": "90vh", "width":"60vw"}),

            ], style={
                "flex": "1 1 60%",  
                "height": "calc(100vh - 20px)",
                "display": "flex",
                "flexDirection": "column",
                "padding": "10px",
                "margin":"0",
                "backgroundColor": brand_colors['Light green'],
                "marginBottom": "auto" 
            }),
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

def poverty_tab_layout():
    return html.Div([
        html.Div([sidebar], style={
                                        "width": "15%",
                                        "height": "100%",
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",}), # End of sidebar div

        # Left Panel: text, dropdown, bar chart
        html.Div([
        dbc.Card([
                dbc.CardBody([
                    html.H2("Multidimensional Poverty Index", style=header_style),
                    html.P("The Multidimensional Poverty Index (MPI) assesses poverty across health, education, and living standards using ten indicators including nutrition, schooling, sanitation, water, electricity, and housing. This spatial analysis maps deprivation levels across Addis Ababa's sub-cities, revealing where households face multiple overlapping disadvantages. These insights identify priority areas for targeted interventions, supporting equitable resource allocation and sustainable poverty reduction strategies aligned with SDG goals.",
                            style={  "margin": "10px 6px", 
                                    "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                    "textAlign": "justify",
                                    "whiteSpace": "normal",
                                    })
                            ])
                    ], style={  "height": "auto", 
                                "padding":"6px" ,
                                "margin-bottom": "5px",
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"}),

        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(
                        id='variable-dropdown',
                        options=[{'label': v, 'value': v} for v in variables],
                    value=variables[0],
                    style={"margin-bottom": "20px"}),

                    dcc.Graph(id='bar-plot',
                            style={
                            "flex": "1 1 auto",
                            "height":"98%",
                            'padding': '4px',
                            'margin': '8px',
                            #"border-radius": "8px",
                            #"box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
                            })
                            ],style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "height": "100%"             
                                    })
                    ], style={#"height": "60%", 
                                "padding":"6px" ,
                                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                                "backgroundColor": brand_colors['White'],
                                "border-radius": "10px"}),

                    ], style={
                        "height": "100%",
                        "backgroundColor": brand_colors['Light green'],
                        "border-radius": "0",
                        "margin": "0",
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "flex-start",

                        "box-sizing": "border-box",
                        "zIndex": 2,
                        "position": "relative",
                    }),
                    ],style={
        "overflowY": "auto",
        "display": "flex",
        "flexDirection": "column",
        "width": "min(40%)",
        "height": "100%",
        "padding": "10px",
        "backgroundColor": brand_colors['Light green']
        }),


        # Right panel: map, full height
        html.Div([
            dcc.Graph(
                id='map',
                style={"height": "100%",
                       "width": "100%",  # fill the parent div
                       "padding": "0",
                       "margin": "0"})
        ], style={
            "flex": "1",
            "height": "100%",
            "padding": "0",
            "margin": "0",
            "backgroundColor": brand_colors['White'],
            "border-radius": "0",
            "display": "flex",
            "alignItems": "stretch",
            "justifyContent": "center",
            "box-sizing": "border-box",
            "zIndex": 1000,
            "position": "relative",
        })

    ], style={
        "display": "flex",
        "width": "100vw",
        "height": "100%"
    })

def affordability_tab_layout():
    return html.Div([
            html.Div([sidebar], style={
                                "width": "15%",
                                "height": "100%",
                                "display": "flex",
                                "vertical-align":'top',
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
            }), # End of sidebar div

            # Left Panel
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([ 
                            html.H2("Food Environment Analysis", style=header_style),
                            html.P("This map shows the distribution of healthy and unhealthy food outlets across Addis Ababa's sub-cities. The obesogenic ratio reveals where unhealthy outlets dominate, indicating areas with limited access to nutritious food. Population exposure metrics highlight which communities face the greatest imbalance, providing evidence to guide equitable food policy interventions. This analysis forms part of a broader assessment integrating socioeconomic and built environment factors.",
                                       style={  "margin": "10px 6px", 
                                                "fontSize": 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "justify",
                                                "whiteSpace": "normal",
                                                })],
                                style={
                                    'margin': '2px 0px',
                                    'zIndex': '1000',
                                    'justifyContent': 'end',
                                    'alignItems': 'center',
                                    'textAlign': 'center'
                    })],style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%"             
                            })
                ], style={"height": "auto", 
                            "padding":"6px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px"}),

                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select food outlet layers to display on the map."],                                    
                                       style={   "margin": "6px", 
                                                'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "center",
                                                "whiteSpace": "normal",
                                                "fontStyle": "italic"
                                                }),
                                dcc.Dropdown(
                                    id="outlets-layer-select",
                                    options=[{"label": f.split('_')[1] if len(f.split('_')) < 4 else f"{f.split('_')[1]} {f.split('_')[2]}", 
                                            "value": f} for f in outlets_geojson_files],
                                    multi=True,
                                    placeholder="Select outlet layers to display",
                                    style={'zIndex': '2000'})
                                ],
                                style={
                                    'margin': '2px 0px',
                                    'justifyContent': 'end',
                                    'alignItems': 'center',
                                    'textAlign': 'center'
                    })],style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%"             
                            })
                ], style={"height": "auto", 
                            "padding":"6px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px",
                            "zIndex": "2000",
                            "position": "relative"}),

                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                                html.P(["Select a food environment metric to display as a choropleth layer."],                                    
                                       style={   "margin": "6px", 
                                                'fontSize': 'clamp(0.7em, 1em, 1.0em)',
                                                "textAlign": "center",
                                                "whiteSpace": "normal",
                                                "fontStyle": "italic"
                                                }),
                                dcc.Dropdown(
                                    id="choropleth-select",
                                    options=[{"label": label, "value": col} 
                                            for label, col in zip(data_labels_food_env, cols_food_env)],
                                    multi=False,
                                    value='ratio_obesogenic',  # Set default to Obesogenic Ratio
                                    placeholder="Select metric to display",
                                    style={'zIndex': '1900'})
                                ],
                                style={
                                    'margin': '2px 0px',
                                    'justifyContent': 'end',
                                    'alignItems': 'center',
                                    'textAlign': 'center'
                    })],style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%"             
                            })
                ], style={"height": "auto", 
                            "padding":"6px" ,
                            "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                            "backgroundColor": brand_colors['White'],
                            "border-radius": "10px"}),
                
            ], style={
                    "width": "min(30%)",
                    "height": "100%",
                    "padding": "10px",
                    "backgroundColor": brand_colors['Light green'],
                    "border-radius": "0",
                    "margin": "0",
                    "box-shadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "overflowY": "auto",
                    "box-sizing": "border-box",
                    "position": "relative",
                }), # End of left panel

                # Right panel: map, full height
                html.Div([
                    dcc.Graph(
                        id='affordability-map',
                        figure=go.Figure().update_layout(
                            mapbox=dict(style="carto-positron", center={"lat": 9.1, "lon": 38.7}, zoom=10),
                            margin=dict(l=0, r=0, t=0, b=0),
                            paper_bgcolor=brand_colors['White']
                        ),
                        style={"height": "100%", "width": "100%", "padding": "0", "margin": "0"}
                    )
                ], style={
                "flex": "1",
                "height": "100%",
                "padding": "0",
                "margin": "0",
                "backgroundColor": brand_colors['White'],
                "border-radius": "0",
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "stretch",
                "justifyContent": "center",
                "box-sizing": "border-box",
                "zIndex": 1000,
                "position": "relative",
            })

        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

def sustainability_tab_layout():
    # Select display columns (use SDG Numbers instead of SDG Logos)
    display_cols = ['Dimensions', 'Components', 'Indicators', 'SDG impact area/target', 'SDG Numbers']
    df_display = df_indicators[display_cols]
    
    return html.Div([
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"
        }),

        # Main content area
        html.Div([
            # SDG Filter Buttons at top
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H5("Filter by SDG Goal:", style={
                            "marginBottom": "10px",
                            "fontWeight": "bold",
                            "color": brand_colors['Brown'],
                            "fontSize": "clamp(0.9em, 1.1vw, 1.2em)"
                        }),
                        html.Div([
                            html.Button([
                                html.Img(src=f"/assets/logos/SDG%20logos/SDG%20Web%20Files%20w-%20UN%20Emblem/E%20SDG%20Icons%20Square/E_SDG%20goals_icons-individual-rgb-{str(i).zfill(2)}.png",
                                        style={"height": "80px", "display": "block"}),
                            ], 
                            id=f"sdg-filter-{i}",
                            n_clicks=0,
                            style={
                                "border": "3px solid transparent",
                                "borderRadius": "8px",
                                "padding": "5px",
                                "margin": "5px",
                                "cursor": "pointer",
                                "backgroundColor": "transparent",
                                "transition": "all 0.2s"
                            })
                            for i in range(1, 18)
                        ], style={"display": "grid", "gridTemplateColumns": "repeat(9, 1fr)", "gap": "5px", "justifyItems": "center", "maxWidth": "100%"}),
                        html.Button("Clear Filter", 
                                   id="sdg-clear-filter",
                                   n_clicks=0,
                                   style={
                                       "marginTop": "10px",
                                       "padding": "8px 20px",
                                       "backgroundColor": brand_colors['Red'],
                                       "color": "white",
                                       "border": "none",
                                       "borderRadius": "5px",
                                       "cursor": "pointer",
                                       "fontWeight": "bold"
                                   }),
                        html.Div(id="sdg-filter-status", style={
                            "marginTop": "10px",
                            "fontSize": "0.9em",
                            "color": brand_colors['Brown'],
                            "fontStyle": "italic"
                        })
                    ])
                ])
            ], style={
                "marginBottom": "15px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
            
            # Table
            dbc.Card([
                dbc.CardHeader(html.H3("Sustainability Metrics & Indicators", style=header_style)),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='indicators_table',
                        data=df_display.to_dict('records'),
                        columns=[
                            {"name": "SDG Goals" if col == "SDG Numbers" else str(col), "id": str(col)} 
                            for col in display_cols
                        ],
                        page_size=14,
                        page_action='native',
                        filter_action='native',
                        sort_action='native',
                        sort_mode='multi',
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'nowrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'fontSize': 'clamp(0.7em, 1vw, 1em)',
                            'minWidth': '120px',
                            'maxWidth': '250px',
                        },
                        style_cell_conditional=[
                            {
                                'if': {'column_id': 'SDG Numbers'},
                                'minWidth': '100px',
                                'maxWidth': '150px',
                                'textAlign': 'center',
                            }
                        ],
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_filter={
                            'backgroundColor': '#f0f0f0',
                            'fontSize': 'clamp(0.7em, 0.9vw, 0.95em)',
                            'padding': '5px'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        tooltip_data=[
                            {
                                column: {'value': str(row[column]), 'type': 'text'}
                                for column in display_cols
                            } for row in df_display.to_dict('records')
                        ],
                        tooltip_duration=None,
                        css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: ' + brand_colors['Light green'] + '; color: ' + brand_colors['Black'] + '; border: 2px solid ' + brand_colors['Dark green'] + '; padding: 6px; font-size: 14px; box-shadow: 0 4px 8px ' + brand_colors['Black'] + ';'
                        }],
                        style_table={
                            'overflowX': 'auto',
                            'width': '100%',
                        }
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column", "overflowY": "auto"})
            ], style={
                "height": "auto",
                "overflowY":"auto",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
        ], style={
            "flex": "1 1 85%",
            "height": "90%",
            "display": "flex",
            "flexDirection": "column",
            "overflow": 'auto',
            "border-radius": "10px",
            'margin': "10px 10px 10px 10px"
        })
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


def policies_tab_layout():
    return html.Div([
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"
        }),

        # Main content area
        html.Div([
            dbc.Card([
                dbc.CardHeader(html.H3("Food System Policies Database", style=header_style)),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='policies_table',
                        data=df_policies.to_dict('records'),
                        columns=[
                            {"name": str(col), "id": str(col)}
                            for col in df_policies.columns
                        ],
                        page_size=14,
                        page_action='native',
                        filter_action='native',
                        sort_action='native',
                        sort_mode='multi',
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'nowrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'fontSize': 'clamp(0.7em, 1vw, 1em)',
                            'minWidth': '120px',
                            'maxWidth': '250px',
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': brand_colors['Red'],
                            'color': 'white',
                            'textAlign': 'center',
                            'fontSize': 'clamp(0.8em, 1vw, 1.1em)'
                        },
                        style_filter={
                            'backgroundColor': '#f0f0f0',
                            'fontSize': 'clamp(0.7em, 0.9vw, 0.95em)',
                            'padding': '5px'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                        ],
                        style_table={
                            'overflowX': 'auto',
                            'width': '100%',
                        }
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
            ], style={
                "height": "auto",
                "overflowY":"auto",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
        ], style={
            "flex": "1 1 85%",
            "height": "90%",
            "display": "flex",
            "flexDirection": "column",
            "overflow": 'hidden',
            "border-radius": "10px",
            'margin': "10px 10px 10px 10px"
        })
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    }) 

def health_nutrition_tab_layout():
    tile_width, lg = 12, 4  # Tile width in columns, large screen size, height in pixels
    return html.Div([
                html.Div([sidebar], style={
                                        "width": "15%",
                                        "height": "100%",
                                        "display": "flex",
                                        "vertical-align":'top',
                                        "flexDirection": "column",
                                        "justifyContent": "flex-start",}), # End of sidebar div

                # Main content area

                html.Div([
                    # CHILDREN Section (6 cards)
                    html.H3("Children Aged 0-59 Months", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "20px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([
                        
                        dbc.Col([create_nutrition_kpi_card("Stunting", 13.9, 40.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Wasting", 3.8, 11.2, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Concurrent Stunting and Wasting", 0.7, 2.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Underweight", 5.5, 23.3, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight", 6.9, 3.9, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Malnutrition", 21.9, 51.5, lower_is_better=True)], width=tile_width, lg=lg),
            
                    ]),

                                     
                    # ADOLESCENT GIRLS Section (4 cards)
                    html.H3("Adolescent Girls (10-19 Years)", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "30px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([

                        dbc.Col([create_nutrition_kpi_card("Underweight (BMI)", 5.3, 9.3, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight (BMI)", 12.5, 5.1, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Obese (BMI)", 3.5, 1, lower_is_better=True)], width=tile_width, lg=lg),
            
                    ]),
                    
                    # WOMEN Section (2 cards)
                    html.H3("Women (15-49 Years)", style={
                        "color": brand_colors['Brown'],
                        "fontWeight": "bold",
                        "marginTop": "30px",
                        "marginBottom": "15px",
                        "borderBottom": f"3px solid {brand_colors['Mid green']}",
                        "paddingBottom": "10px"
                    }),
                    dbc.Row([

                        dbc.Col([create_nutrition_kpi_card("Underweight", 10.7, 20.1, lower_is_better=True)], width=tile_width, lg=lg),
                        dbc.Col([create_nutrition_kpi_card("Overweight", 35.8, 11.4, lower_is_better=True)], width=tile_width, lg=lg),
            
                    ]),
                ], style={  "overflowY": "auto",
                            "flex": "1 1 85%",
                            "padding": "10px",
                            "backgroundColor": brand_colors['Light green']})
    
        ], style={
                    "display": "flex", 
                    "width": "100%", 
                    "height": "100%",
                    "backgroundColor": brand_colors['Light green']
        })

def footprints_tab_layout():
    return html.Div([
        html.Div([sidebar], style={
            "width": "15%",
            "height": "100%",
            "display": "flex",
            "vertical-align": 'top',
            "flexDirection": "column",
            "justifyContent": "flex-start"
        }),

        # Main content area
        html.Div([
            
            # Dropdown card to select food group
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Food Group:", style={
                        "fontSize": "clamp(0.9em, 1.1vw, 1.2em)",
                        "marginBottom": "10px",
                        "color": brand_colors['Brown']
                    }),
                    dcc.Dropdown(
                        id='food-group-select',
                        options=[
                            {'label': group.split('-')[1] if '-' in group else group, 'value': group}
                            for group in sorted(df_lca['Food Group'].dropna().unique())
                        ],
                        value=sorted(df_lca['Food Group'].dropna().unique())[0],
                        clearable=False,
                        style={"fontSize": "clamp(0.8em, 1vw, 1.1em)"}
                    )
                ])
            ], style={
                "marginBottom": "20px",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.1)",
                "backgroundColor": brand_colors['White'],
                "border-radius": "10px",
                "padding": "10px"
            }),
            
            # Container for food item cards (populated by callback)
            html.Div(id='food-items-container', style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
                "gap": "15px",
                "width": "100%"
            }),

        ], style={
            "flex": "1 1 85%",
            "overflowY":'auto',
            "padding": "20px",
            "display": "flex",
            "flexDirection": "column"
        })
        
    ], style={
        "display": "flex",
        "width": "100%",
        "height": "100%",
        "backgroundColor": brand_colors['Light green']
    })


#------------------------- App Layout ----------------------- #

app.layout = html.Div([

                    html.Div(id="tab-content", children=landing_page_layout(), style={"width": "100%",
                                                                                            "height": "100%"})

                    # Parent container for full page
                    ], style={
                        "display": "flex",
                        "flexDirection": "column",
                        "height": "100vh",
                        "width": "100vw"
            })

# ------------------------- Callbacks ------------------------- #

# Linking the dropdown to the bar chart for the MPI page    
@app.callback(
    Output('bar-plot', 'figure'),
    Input('variable-dropdown', 'value'),
    prevent_initial_call=False
    
)
def update_bar(selected_variable):
    # Sort by selected variable, descending
    filtered_df = df_mpi[df_mpi["Variable"]==selected_variable]
    sorted_df = filtered_df.sort_values('Value', ascending=False)
    fig = px.bar(
        sorted_df,
        x='Value',
        y='Dist_Name',
        orientation='h',
        hover_data=['Dist_Name'],
        labels={'Dist_Name': " ",
                'Value':"Percentage of Deprived Households"},
        color_discrete_sequence=[brand_colors['Red']]
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        autosize=True,  # Allow figure to fill container
        #height=25 * len(sorted_df),
        margin=dict(l=0.15, r=0.1, t=0.15, b=1),
        hoverlabel=dict(
            bgcolor="white",      # Tooltip background color
            font_color="black",   # Tooltip text color
        )
    )

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
    zoom = 10

    MPI_display = MPI.copy()
    MPI_display['opacity'] = 0.7
    MPI_display['line_width'] = 0.8

    # If a bar is clicked, zoom to that district
    if clickData and 'points' in clickData:
        selected_dist = clickData['points'][0]['y']  # y is Dist_Name for horizontal bar
        match = MPI[MPI['Dist_Name'] == selected_dist]
        if not match.empty:
            #centroid = match.geometry.centroid
            center = {
                "lat": match.geometry.centroid.y.values[0],
                "lon": match.geometry.centroid.x.values[0]
            }
            #area = match.geometry.area.values[0]
            #zoom = max(8, min(12, 12 - area * 150))  # Zoom in closer
            # Highlight: set opacity and line_width for the selected district

            zoom = 10
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'opacity'] = 1
            MPI_display.loc[MPI_display['Dist_Name'] == selected_dist, 'line_width'] = 2


    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color='MPI',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 50),
        labels={'MPI':'MPI','Dist_Name':'District Name'},
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center
    )

    
    fig.update_layout(coloraxis_colorbar=None)
    fig.update_coloraxes(showscale=False)

    fig.update_layout(
    paper_bgcolor=brand_colors['White'],
    plot_bgcolor=brand_colors['White'],
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



@app.callback(
    Output('map_foodoutlets', 'figure'),
    Input('variable-dropdown', 'value')
)
def add_outlets_map(selected_variable):
    center = {
        "lat": MPI.geometry.centroid.y.mean(),
        "lon": MPI.geometry.centroid.x.mean()
    }
    zoom = 10

    fig = px.choropleth_mapbox(
        MPI,
        geojson=geojson,
        locations="Dist_Name",
        featureidkey="properties.Dist_Name",
        color='MPI',
        color_continuous_scale="Reds",
        opacity=0.7,
        range_color=(0, 50),
        labels={'MPI':'MPI','Dist_Name':'District Name'},
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center
    )

    
    fig.update_layout(coloraxis_colorbar=None)
    fig.update_coloraxes(showscale=False)

    fig.update_layout(
    paper_bgcolor=brand_colors['White'],
    plot_bgcolor=brand_colors['White'],
    margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig


# Update Piechart 1 UI on click while filtering table
@app.callback(
    Output('piechart', 'figure'),
    Output('selected_slice', 'data'),
    Input('pie-filter-dropdown', 'value'),
    Input('piechart', 'clickData'),
    State('selected_slice', 'data')
)
def update_pie(filter_by, clickData, current_selected):
    if filter_by == 'Area':
        df_count = df_sh['Area of Activity (Food Systems Value Chain)'].value_counts().reset_index()
        df_count.columns = ['name', 'count']
    elif filter_by == 'Scale':
        df_count = df_sh['Scale of Activity'].value_counts().reset_index()
        df_count.columns = ['name', 'count']
    elif filter_by == 'Sector':
        df_count = df_sh['Primary sector '].value_counts().reset_index()
        df_count.columns = ['name', 'count']

    # Handle click to select/unselect slice
    new_selected = current_selected
    pull = [0]*len(df_count)
    if clickData:
        clicked = clickData['points'][0]['label']
        new_selected = None if clicked == current_selected else clicked
        pull = [0.2 if name==new_selected else 0 for name in df_count['name']]

    slice_colors = plotting_palette_cat  # or greens_pie_palette
    text_colors = []
    for color in slice_colors:
        # Simple luminance check for hex color
        rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        text_colors.append('white' if luminance < 180 else brand_colors['Brown'])


    fig = px.pie(df_count, values='count', names='name', hole=0,
                 color_discrete_sequence=slice_colors)
    fig.update_traces(textfont_color=text_colors, pull=pull, hoverinfo='percent', textinfo='label', textposition='inside', insidetextorientation='radial')
    fig.update_layout(margin=dict(t=0.1, l=0.1, r=0.1, b=0.1), showlegend=False)

    return fig, new_selected


# Table filtering based on both selections made in piecharts
@app.callback(
    Output('sh_table', 'data'),
    Input('pie-filter-dropdown', 'value'),
    Input('selected_slice', 'data')
)
def filter_table(filter_by, selected):
    if selected:
        if filter_by == 'Area':
            df_filtered = df_sh[df_sh['Area of Activity (Food Systems Value Chain)'] == selected]
        elif filter_by == 'Scale':
            df_filtered = df_sh[df_sh['Scale of Activity'] == selected] 
        elif filter_by == 'Sector':
            df_filtered = df_sh[df_sh['Primary sector '] == selected]
        return df_filtered.to_dict('records')
    else:
        return df_sh.to_dict('records')
    

@app.callback(
    Output('affordability-map', 'figure'),
    [Input("choropleth-select", "value"),
     Input("outlets-layer-select", "value")],
    [State('affordability-map', 'relayoutData')]
)
def update_affordability_map(selected_metric, selected_outlets, relayout_data):
    # Preserve current zoom and center if available
    if relayout_data and 'mapbox.center' in relayout_data:
        center = relayout_data['mapbox.center']
        zoom = relayout_data.get('mapbox.zoom', 11)
    else:
        center = {"lat": 9.0192, "lon":  38.752}
        zoom = 11
    
    fig = go.Figure()
    
    # Add choropleth layer if metric selected
    if selected_metric:
        gdf = gdf_food_env.copy()
        
        if selected_metric in gdf.columns:
            gdf[selected_metric] = pd.to_numeric(gdf[selected_metric], errors='coerce')
            
            # Get human-readable label for the metric
            metric_label = data_labels_food_env[cols_food_env.index(selected_metric)] if selected_metric in cols_food_env else selected_metric
            
            # Choose color scale based on metric direction
            direction = metric_direction.get(selected_metric, None)
            if direction is True:
                colorscale = [[0, green_scale[0]], [0.25, green_scale[1]], [0.5, green_scale[2]], 
                             [0.75, green_scale[3]], [1, green_scale[4]]]
            elif direction is False:
                colorscale = [[0, red_scale[0]], [0.25, red_scale[1]], [0.5, red_scale[2]], 
                             [0.75, red_scale[3]], [1, red_scale[4]]]
            else:
                colorscale = [[0, grey_scale[0]], [0.25, grey_scale[1]], [0.5, grey_scale[2]], 
                             [0.75, grey_scale[3]], [1, grey_scale[4]]]
            
            geojson_data = json.loads(gdf.to_json())
            
            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson_data,
                locations=gdf.index,
                z=gdf[selected_metric],
                colorscale=colorscale,
                marker=dict(opacity=0.7, line=dict(color='#222', width=1)),
                hovertemplate='<b>' + metric_label + '</b>: %{z:.2f}<extra></extra>',
                text=gdf.get('Dist_Name', gdf.index),
                showscale=False
            ))
    
    # Add outlet markers if selected
    if selected_outlets:
        # Dark/vivid blue color palette for outlet markers (stands out against light red/green choropleth)
        blue_palette = [
                    "#1a3a3a",  
                    "#4a2c2a",  
                    "#2d4263",  
                    "#3d1f1f",  
                    "#2c4a2c",  
                ]
        
        for i, filename in enumerate(selected_outlets):
            outlet_gdf = gpd.read_file(outlets_path + filename).to_crs('EPSG:4326')
            
            # Cycle through blue palette colors
            marker_color = blue_palette[i % len(blue_palette)]
            
            fig.add_trace(go.Scattermapbox(
                lat=outlet_gdf.geometry.y,
                lon=outlet_gdf.geometry.x,
                mode='markers',
                marker=dict(size=6, color=marker_color, opacity=0.8),
                name=filename.split('_')[1] if len(filename.split('_')) < 4 else f"{filename.split('_')[1]} {filename.split('_')[2]}",
                hoverinfo='skip'
            ))
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=center,
            zoom=zoom
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=brand_colors['White'],
        showlegend=True if selected_outlets else False,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
        uirevision='constant'  # Preserve zoom/pan state
    )
    
    return fig


@app.callback(
    [Output("kpi-total-flow", "children"),
     Output("urban-indicator", "figure"),
     Output("sankey-graph", "figure")],
    Input("slider", "value"))

def update_sankey(value):
    df_sankey_filt = df_sankey[df_sankey['Year']==int(value)]
    flow1 = df_sankey_filt[['province', 'Target', 'Supply to Hanoi']].rename(
        columns={'province':'source', 'Target':'target', 'Supply to Hanoi':'supply'})

    flow2 = df_sankey_filt[['Target', 'Target_1', 'Rice supply']].rename(
        columns={'Target':'source', 'Target_1':'target', 'Rice supply':'supply'})

    df_sankey_final = pd.concat([flow1.drop_duplicates(), flow2.groupby(['source','target']).sum().reset_index()], ignore_index=True)
    labels = list(pd.unique(df_sankey_final[['source','target']].values.ravel('K')))

    # Map sources and targets to indices
    source_indices = df_sankey_final['source'].apply(lambda x: labels.index(x))
    target_indices = df_sankey_final['target'].apply(lambda x: labels.index(x))
    weights = df_sankey_final['supply']

    node_colors = [brand_colors['Red'] for l in labels]
    link_colors = ["rgba(209, 231, 168, 0.5)" for link in df_sankey_final['source']]


    # Calculating KPIs 
    total_flow = flow1.drop_duplicates()["supply"].sum()
    total_flow_text = f"{total_flow:,.0f}"

    total = flow2.groupby(['source','target']).sum().reset_index()['supply'].sum()
    urban_only = flow2.groupby(['source','target']).sum().reset_index().set_index('target').loc['Hanoi urban'].values[1]
    urban_share = urban_only/total *100
    urban_share_text = f"{urban_share:.1f}%"

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, color=node_colors, pad=15, thickness=20),
        link=dict(source=source_indices, target=target_indices, value=weights, color=link_colors, 
                  hovertemplate='From %{source.label} → %{target.label}<br>Flow: %{value}<extra></extra>')
    ))

    fig.update_layout(
        hovermode='x',
        font=dict(size=12, color='black'),
        paper_bgcolor=brand_colors['White'],
        plot_bgcolor=brand_colors['White'],
        margin=dict(l=10, r=10, t=20, b=20), 
        width=None)

    urban_fig = go.Figure(go.Pie(
        values=[urban_share, 100-urban_share],
        hole=0.6,
        marker=dict(colors=[brand_colors['Red'], brand_colors['Light green']]),
        textinfo="none",
        labels=["Urban", "Rural"],  # Add labels for clarity
        hoverinfo="label+percent",  # Show label, percent, and value on hover
        hovertext=[f"Urban: {urban_share:.1f}%", f"Rural: {100-urban_share:.1f}%"]  # Custom hover text
    ))
    
    urban_fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=0,b=0.1),
                            paper_bgcolor="rgba(0,0,0,0)",  
                            plot_bgcolor="rgba(0,0,0,0)")


    return total_flow_text, urban_fig, fig

# Populate food items grid based on selected food group
@app.callback(
    Output('food-items-container', 'children'),
    [Input('food-group-select', 'value')]
)
def update_food_items_grid(selected_group):
    # Filter items by selected group
    filtered_df = df_lca[df_lca['Food Group'] == selected_group].sort_values('Item Cd')
    
    # Calculate percentile thresholds for traffic light system across all foods
    # Lower values are better for environmental impact
    thresholds = {
        'Total GHG Emissions': {
            'green': df_lca['Total GHG Emissions'].quantile(0.33),
            'yellow': df_lca['Total GHG Emissions'].quantile(0.67)
        },
        'Freshwater Comsumption (l)': {
            'green': df_lca['Freshwater Comsumption (l)'].quantile(0.33),
            'yellow': df_lca['Freshwater Comsumption (l)'].quantile(0.67)
        },
        'Acidification (kg SO2eq)': {
            'green': df_lca['Acidification (kg SO2eq)'].quantile(0.33),
            'yellow': df_lca['Acidification (kg SO2eq)'].quantile(0.67)
        },
        'Eutrophication (kg PO43-eq)': {
            'green': df_lca['Eutrophication (kg PO43-eq)'].quantile(0.33),
            'yellow': df_lca['Eutrophication (kg PO43-eq)'].quantile(0.67)
        }
    }
    
    def get_traffic_light_colors(value, indicator):
        """Return border and shadow colors based on traffic light system (green=good, yellow=medium, red=bad)"""
        if value <= thresholds[indicator]['green']:
            return {"border": "#2e7d32", "shadow": "#a5d6a7"}  # Dark green border, light green shadow
        elif value <= thresholds[indicator]['yellow']:
            return {"border": "#f57f17", "shadow": "#fff59d"}  # Dark yellow border, light yellow shadow
        else:
            return {"border": "#c62828", "shadow": "#ef9a9a"}  # Dark red border, light red shadow
    
    # Create a card for each food item
    food_cards = []
    for _, row in filtered_df.iterrows():
        # Create 2x2 grid of mini KPI cards with traffic light colors
        mini_kpis = html.Div([
            # Row 1: GHG and Water
            html.Div([
                # GHG mini card
                html.Div([
                    html.Div("GHG", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Total GHG Emissions']:.4f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg CO₂-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Total GHG Emissions'], 'Total GHG Emissions')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Total GHG Emissions'], 'Total GHG Emissions')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"}),
                
                # Water mini card
                html.Div([
                    html.Div("Water", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Freshwater Comsumption (l)']:.2f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("liters", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Freshwater Comsumption (l)'], 'Freshwater Comsumption (l)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Freshwater Comsumption (l)'], 'Freshwater Comsumption (l)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"})
            ], style={"display": "flex", "marginBottom": "5px"}),
            
            # Row 2: Acidification and Eutrophication
            html.Div([
                # Acidification mini card
                html.Div([
                    html.Div("Acidification", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Acidification (kg SO2eq)']:.6f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg SO₂-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Acidification (kg SO2eq)'], 'Acidification (kg SO2eq)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Acidification (kg SO2eq)'], 'Acidification (kg SO2eq)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"}),
                
                # Eutrophication mini card
                html.Div([
                    html.Div("Eutrophication", style={"fontSize": "0.7em", "color": brand_colors['Brown'], "marginBottom": "2px"}),
                    html.Div(f"{row['Eutrophication (kg PO43-eq)']:.6f}", style={"fontSize": "1em", "fontWeight": "bold", "color": brand_colors['Brown']}),
                    html.Div("kg PO₄³⁻-eq", style={"fontSize": "0.6em", "color": brand_colors['Brown']})
                ], style={"flex": "1", "textAlign": "center", "padding": "8px", 
                         "backgroundColor": brand_colors['White'], 
                         "border": f"2px solid {get_traffic_light_colors(row['Eutrophication (kg PO43-eq)'], 'Eutrophication (kg PO43-eq)')['border']}",
                         "boxShadow": f"0 2px 8px {get_traffic_light_colors(row['Eutrophication (kg PO43-eq)'], 'Eutrophication (kg PO43-eq)')['shadow']}",
                         "borderRadius": "5px", "margin": "3px"})
            ], style={"display": "flex"})
        ])
        
        # Main card for this food item
        food_card = dbc.Card([
            dbc.CardBody([
                html.H5(row['Item Cd'], style={
                    "color": brand_colors['Brown'],
                    "fontWeight": "bold",
                    "marginBottom": "10px",
                    "textAlign": "center",
                    "fontSize": "clamp(0.9em, 1em, 1.1em)"
                }),
                mini_kpis
            ])
        ], style={
            "backgroundColor": brand_colors['White'],
            "borderRadius": "10px",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
            "padding": "10px",
            "height": "100%"
        })
        
        food_cards.append(food_card)
    
    return food_cards

# Callback for SDG filter buttons
@app.callback(
    [Output('indicators_table', 'data'),
     Output('sdg-filter-status', 'children'),
     Output('sdg-filter-1', 'style'),
     Output('sdg-filter-2', 'style'),
     Output('sdg-filter-3', 'style'),
     Output('sdg-filter-4', 'style'),
     Output('sdg-filter-5', 'style'),
     Output('sdg-filter-6', 'style'),
     Output('sdg-filter-7', 'style'),
     Output('sdg-filter-8', 'style'),
     Output('sdg-filter-9', 'style'),
     Output('sdg-filter-10', 'style'),
     Output('sdg-filter-11', 'style'),
     Output('sdg-filter-12', 'style'),
     Output('sdg-filter-13', 'style'),
     Output('sdg-filter-14', 'style'),
     Output('sdg-filter-15', 'style'),
     Output('sdg-filter-16', 'style'),
     Output('sdg-filter-17', 'style')],
    [Input('sdg-filter-1', 'n_clicks'),
     Input('sdg-filter-2', 'n_clicks'),
     Input('sdg-filter-3', 'n_clicks'),
     Input('sdg-filter-4', 'n_clicks'),
     Input('sdg-filter-5', 'n_clicks'),
     Input('sdg-filter-6', 'n_clicks'),
     Input('sdg-filter-7', 'n_clicks'),
     Input('sdg-filter-8', 'n_clicks'),
     Input('sdg-filter-9', 'n_clicks'),
     Input('sdg-filter-10', 'n_clicks'),
     Input('sdg-filter-11', 'n_clicks'),
     Input('sdg-filter-12', 'n_clicks'),
     Input('sdg-filter-13', 'n_clicks'),
     Input('sdg-filter-14', 'n_clicks'),
     Input('sdg-filter-15', 'n_clicks'),
     Input('sdg-filter-16', 'n_clicks'),
     Input('sdg-filter-17', 'n_clicks'),
     Input('sdg-clear-filter', 'n_clicks')]
)
def filter_by_sdg(*args):
    ctx = dash.callback_context
    
    # Default style for buttons
    default_style = {
        "border": "3px solid transparent",
        "borderRadius": "8px",
        "padding": "5px",
        "margin": "5px",
        "cursor": "pointer",
        "backgroundColor": "transparent",
        "transition": "all 0.2s"
    }
    
    # Selected style
    selected_style = {
        "border": f"3px solid {brand_colors['Red']}",
        "borderRadius": "8px",
        "padding": "5px",
        "margin": "5px",
        "cursor": "pointer",
        "backgroundColor": brand_colors['Light green'],
        "transition": "all 0.2s",
        "boxShadow": "0 2px 8px rgba(168, 0, 80, 0.3)"
    }
    
    # All buttons default style
    button_styles = [default_style.copy() for _ in range(17)]
    
    # Get all columns including SDG Numbers
    display_cols = ['Dimensions', 'Components', 'Indicators', 'SDG impact area/target', 'SDG Numbers']
    
    if not ctx.triggered:
        return df_indicators[display_cols].to_dict('records'), "Click an SDG icon to filter indicators", *button_styles
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Clear filter
    if button_id == 'sdg-clear-filter':
        return df_indicators[display_cols].to_dict('records'), "Showing all indicators", *button_styles
    
    # Extract SDG number from button id
    if button_id.startswith('sdg-filter-'):
        sdg_num = button_id.split('-')[-1]
        
        # Filter dataframe to rows containing this SDG number
        filtered_df = df_indicators[df_indicators['SDG Numbers'].str.contains(sdg_num, na=False)]
        
        # Update button style for selected SDG
        sdg_index = int(sdg_num) - 1
        button_styles[sdg_index] = selected_style
        
        status = f"Showing {len(filtered_df)} indicators for SDG {sdg_num}"
        
        return filtered_df[display_cols].to_dict('records'), status, *button_styles
    
    return df_indicators[display_cols].to_dict('records'), "Click an SDG icon to filter indicators", *button_styles

# Linking the tabs to page content loading 
@app.callback(
    Output("tab-content", "children"),
    [
        Input("tab-1-stakeholders", "n_clicks"),
        Input("tab-2-supply", "n_clicks"),
        Input("tab-3-sustainability", "n_clicks"),
        Input("tab-4-poverty", "n_clicks"),
        Input("tab-5-labour", "n_clicks"),
        Input("tab-6-resilience", "n_clicks"),
        Input("tab-7-affordability", "n_clicks"),
        Input("tab-8-losses", "n_clicks"),
        Input("tab-9-policies", "n_clicks"),
        Input("tab-10-nutrition", "n_clicks"),
        Input("tab-11-footprints", "n_clicks"),
        Input("tab-12-behaviour", "n_clicks"),
    ]
)
def render_tab_content(n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12):
    ctx = dash.callback_context
    if not ctx.triggered:
        return landing_page_layout()
    tab_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if tab_id == "tab-1-stakeholders":
        return stakeholders_tab_layout()
        
    elif tab_id == "tab-2-supply":
        return supply_tab_layout()
    
    elif tab_id == "tab-3-sustainability":
        return sustainability_tab_layout()
    
    elif tab_id == "tab-4-poverty":
        return poverty_tab_layout()
    
    elif tab_id == "tab-7-affordability":
        return affordability_tab_layout()
    
    elif tab_id == "tab-9-policies":
        return policies_tab_layout()

    elif tab_id == "tab-10-nutrition":
        return health_nutrition_tab_layout()
    
    elif tab_id == "tab-11-footprints":
        return footprints_tab_layout()

    else:
        return landing_page_layout()


if __name__ == '__main__':
    app.run(debug=True, port=8051)
