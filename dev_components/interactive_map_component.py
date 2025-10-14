import dash_leaflet as dl
from dash_extensions.enrich import DashProxy, Input, Output, State, html, dcc
from dash import exceptions, no_update
try:
    from dash import ctx  # Dash >= 2.9
except Exception:  
    from dash import callback_context as ctx
import requests
from dash_extensions.javascript import assign
import json
from pathlib import Path
import dash_bootstrap_components as dbc


# Styling for drawn polygons, feel free to change the colors opacity etc to match dashboard css
poly_style = assign(
    """function(feature, context){
        return {color: '#ff7f0e', weight: 2, fillOpacity: 0.3};
    }"""
)
# Renders labels on field polygons
label_on_each = assign(
    """function(feature, layer, context){
        var name = (feature && feature.properties && feature.properties.label) ? String(feature.properties.label) : null;
        if (name){
            layer.bindTooltip(name, {permanent: true, direction: 'center', className: 'polygon-label'});
        }
    }"""
)


# Created a sample app but container can be inserted into another Dash App layout
app = DashProxy(prevent_initial_callbacks=True)
app.layout = html.Div(
    [
    dbc.Card([
        html.Div(
            [
                dcc.Input(id="search_query", type="text", placeholder="Search location (e.g., Addis Ababa)", style={"width": "300px"}),
                html.Button("Search", id="search_btn", n_clicks=0),
                html.Span("  "),
                html.Div(id="location_status", style={"marginTop": "6px", "fontFamily": "monospace"}),
            ],
            style={"marginTop": "10px"},
        )],style={
                        "width": "90vw",
                        "backgroundColor": "rgba(255, 255, 255, 0.5)",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "margin": "10px",
                        "display": "flex", 
                        "alignItems": "center", 
                        "gap": "8px", 
                        "flexWrap": "wrap",
                        "padding": "10px"
            }),
    
    # Setup a map with the edit control within display card 
    dbc.Card([
        dl.Map(
            center=[0, 0],
            zoom=2,
            children=[
                    # Basemap switcher in layer control and fields overlay
                    dl.LayersControl(
                        [
                            dl.BaseLayer(
                                dl.TileLayer(
                                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                                ),
                                name="OpenStreetMap",
                                checked=True,
                            ),
                            dl.BaseLayer(
                                dl.TileLayer(
                                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                    attribution='Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
                                ),
                                name="Esri WorldImagery (satellite)",
                            ),
                            dl.Overlay(
                                dl.FeatureGroup([
                                    # Adds sidebar where you can draw features on map, only polygons enabled for outlining fields
                                    dl.EditControl( 
                                        id="edit_control",
                                        draw={
                                            "polygon": True,
                                            "marker": False,
                                            "polyline": False,
                                            "rectangle": False,
                                            "circle": False,
                                            "circlemarker": False,
                                        },
                                        edit={"edit": False, "remove": True}, # Can toggle edit, remove buttons here
                                    ),
                                    dl.GeoJSON(id="geojson", data=None, options={"style": poly_style, "onEachFeature": label_on_each}),
                                ]),
                                name="Fields",
                                checked=True,
                            ),
                        ],
                        position="topleft",
                    ),
                ],
                style={"width": "100%", "height": "100%"},
            id="map",
            )], style={
                        "height": "70vh",
                        "width": "90vw",
                        "backgroundColor": "rgba(255, 255, 255, 0.5)",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "margin": "10px",
                        "justifyContent": 'center',
                        "padding": "10px"
            }), # Map card styling 
    
        # Buttons for triggering actions, incl adding, removing, labelling and saving fields, all linked to callbacks
        dbc.Card([
            html.Button("Add Field", id="draw_poly", n_clicks=0),
            html.Button("Clear all", id="clear_all", n_clicks=0),
            html.Button("Save Fields", id="save_fields", n_clicks=0),
            dcc.Input(id="feature_label", type="text", placeholder="Field name/label"),
            html.Button("Apply label to last feature", id="apply_label", n_clicks=0),
            dbc.Alert(id='save_status', is_open=False, color='secondary', style={"marginLeft": "8px"})
        ], style={
                        "width": "90vw",
                        "backgroundColor": "rgba(255, 255, 255, 0.5)",
                        "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "margin": "10px",
                        "display": "flex", 
                        "alignItems": "center", 
                        "gap": "8px", 
                        "flexWrap": "wrap",
                        "padding": "10px"
            }) # Buttons card styling
    ]
)


# EditControl, and apply label to last feature
@app.callback(
    Output("geojson", "data"),
    [Input("edit_control", "geojson"), Input("apply_label", "n_clicks")], # Triggers from map, drawing/editing and labelling
    [State("feature_label", "value"), State("geojson", "data")],
    prevent_initial_call=True,
)
def sync_geojson(edit_geojson, n_clicks, label, current):
    triggered = getattr(ctx, "triggered_id", None) # Determine trigger type draw/edit or label
    
    if triggered == "edit_control":
        gj = edit_geojson if isinstance(edit_geojson, dict) else {"type": "FeatureCollection", "features": []}

        try:
            old_feats = (current or {}).get("features", []) if isinstance(current, dict) else []
            new_feats = gj.get("features", [])
            for nf, of in zip(new_feats, old_feats): # Solves indexing errors from adding new fields & preserves names
                if isinstance(of, dict):
                    props = of.get("properties") or {}
                    if "label" in props:
                        nf.setdefault("properties", {})
                        nf["properties"]["label"] = props["label"]
        except Exception:
            pass
        return gj
    
    elif triggered == "apply_label":
        if not n_clicks:
            raise exceptions.PreventUpdate
        if not label:
            return no_update
        if not current or not isinstance(current, dict):
            return no_update
        feats = current.get("features") or []
        if not feats:
            return no_update
        feats[-1].setdefault("properties", {})["label"] = str(label)
        return current
    else:
        raise exceptions.PreventUpdate


# Trigger draw polygon
@app.callback(Output("edit_control", "drawToolbar"), Input("draw_poly", "n_clicks"))
def trigger_mode(n_clicks):
    return dict(mode="polygon", n_clicks=n_clicks)  # include n_click to ensure prop changes


# Trigger mode remove all
@app.callback(Output("edit_control", "editToolbar"), Input("clear_all", "n_clicks"))
def trigger_action(n_clicks):
    return dict(mode="remove", action="clear all", n_clicks=n_clicks)  # include n_click to ensure prop changes


# Location/Address search callback, checks OSM db and returns lon, lat of address to update map
@app.callback(
    [Output("map", "center"), Output("map", "zoom"), Output("location_status", "children")],
    Input("search_btn", "n_clicks"),
    State("search_query", "value"),
    prevent_initial_call=True,
)
def on_search(n_clicks, query):
    if not n_clicks or not query:
        raise exceptions.PreventUpdate
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "agriim-dashboard/1.0"},
            timeout=8,
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            return no_update, no_update, f"No results for: {query}"
        item = items[0]
        lat, lon = float(item["lat"]), float(item["lon"]) 
        display = item.get("display_name", query)
        return [lat, lon], 12, f"Found: {display}"
    except Exception as e:
        return no_update, no_update, f"Search error: {e}"


# Save fields to GeoJSON on disk, can change this based on user profile storage 
@app.callback(
    [Output("save_status", "children"), Output("save_status", "color"), Output("save_status", "is_open")],
    Input("save_fields", "n_clicks"),
    State("geojson", "data"),
    prevent_initial_call=True,
)
def save_fields(n_clicks, gj):
    if not n_clicks:
        raise exceptions.PreventUpdate
    if not gj or not isinstance(gj, dict):
        return "No Field(s) to Save", "warning", True
    feats = gj.get("features") or []
    if not feats:
        return "No Field(s) to Save", "warning", True
    try:

        default_path = Path.cwd() / "drawn_fields.geojson" # Currently uses cwd but you can set a path here 
        path = Path(default_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(gj, ensure_ascii=False, indent=2))
        return f"Saved {len(feats)} Field(s)", "success", True
    except Exception as e:
        return f"Save error: {e}", "danger", True
    

if __name__ == "__main__":
    app.run(debug=True, port=8051)
