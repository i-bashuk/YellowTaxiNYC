import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import numpy as np
import pickle
from dash.dependencies import Output, Input

data = pd.read_pickle('yt_result.pkl').sort_index()
zones = pd.read_pickle('zones.pkl').to_list()
min_date = data.index.get_level_values(0).min().date()
max_date = data.index.get_level_values(0).max().date()
with open('grid.pkl', 'rb') as f:
    grid = pickle.load(f)

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "NYC Yellow taxi"
server = app.server

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="🚕", className="header-emoji"),
                html.H1(
                    children="Yellow Taxi", className="header-title"
                ),
                html.P(
                    children="Predict number of rides"
                    "for different regions of NY"
                    " mean error = 14.48 (June 2016)",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Date", className="menu-title"),
                        dcc.DatePickerSingle(
                            id="date",
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            date=min_date,
                            first_day_of_week=1,
                            disabled=False,
                            display_format='DD-MM-Y',
                            className="dropdown",
                            show_outside_days=False,
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Time", className="menu-title"),
                        dcc.Dropdown(
                            id="time",
                            options=[
                                {"label": f'{time}H', "value": time}
                                for time in range(24)
                            ],
                            value=19,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Lag", className="menu-title"),
                        dcc.Dropdown(
                            id="lag",
                            options=[
                                {"label": f'{time}H', "value": time}
                                for time in range(1, 7)
                            ],
                            value=1,
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Region", className="menu-title"),
                        dcc.Dropdown(
                            id="region",
                            options=[
                                {"label": region, "value": region}
                                for region in zones
                            ],
                            value=1231,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Type", className="menu-title"),
                        dcc.RadioItems(
                            id='type',
                            options=[
                                {"label": 'Map', "value": 'map'},
                                {"label": 'Graph', "value": 'graph'}
                            ],
                            value='map',
                            labelStyle={'display': 'block'},
                        )
                    ],
                ),  
            ],
            className="menu1",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="map", config={"displayModeBar": True},
                    ),
                    className="card",
                ),
                # html.Div(
                #     children='', id='error',
                #     # children=dcc.Graph(
                #     #     id="ts", config={"displayModeBar": True},
                #     # ),
                #     className="card",
                # ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [Output("map", "figure"),
     Output("date", "disabled"),
     Output("time", "disabled"), 
     Output("region", "disabled"), 
    #  Output("error", "children")
    ],
    [
        Input("date", "date"),
        Input("time", "value"),
        Input("region", "value"),
        Input("lag", "value"),
        Input("type", "value"),
    ],
)
def update_charts(date, time, region, lag, type):
    pred = f'pred_{lag}'
    df_ts = data.loc[(slice(None), region), ['y', pred]].dropna()
    ts_date = df_ts.index.get_level_values(0).to_list()
    date = pd.to_datetime(date) + pd.Timedelta(f'{time}H')
    if type == 'graph':
        # -----timeSeries-----
        ts_real = go.Scatter(x = ts_date, 
                            y = df_ts.y, 
                            name = 'Real data'
                            )

        ts_predicted = go.Scatter(x =ts_date,
                                y = df_ts.iloc[:, -1],
                                opacity=0.6,
                                name = 'Predicted data'
                                )

        ts = [ts_real, ts_predicted]

        layout = {'title': 'Time Series: Real vs Predicted',
                'xaxis': {'rangeslider': {'visible': True}, 'type': 'date'},
                'font': {'family': 'Balto'},
                'height': 600,
                'margin':{'l': 20, 'r': 10, 'b': 0, 't': 50, 'pad': 0}}

        fig = go.FigureWidget(data = ts, layout = layout)
        dd = [True, True, False]
        # err = np.mean(np.abs(df_ts.y - df_ts[pred]))
        # err = f'Mean error for current region and lag = {err:.1f}, {err/df_ts.y.mean()*100: .1f}%'

    else:
        # -----map----
        rides = data.reset_index(-1).loc[date, ['y', pred, 'zone']]
        max_ = rides[pred].max()
        fig = px.choropleth_mapbox(
            rides, geojson=grid, color=pred, title='Choropleth map: predicted # of rides',
            locations="zone", featureidkey="properties.region",
            center={"lat": 40.74, "lon": -73.90}, zoom=10.3,
            hover_data=['y', pred],
            range_color=[0, max_], opacity=0.4, labels={'y': 'Real', pred: 'Prediction'})
        fig.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            mapbox_style = 'carto-positron', 
            height=600)
        dd = [False, False, True]
        # err = ''
        
    return fig, *dd




if __name__ == "__main__":
    app.run_server(debug=True,
                   host='127.0.0.1')