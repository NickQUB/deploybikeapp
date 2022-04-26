

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output

# Connect to main app.py file
from app import app
from app import server

# Connect to app pages
from apps import gettoday, overall, stations, forecast


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', children=[])
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/gettoday':
        return gettoday.layout
    if pathname == '/apps/overall':
        return overall.layout
    if pathname == '/apps/stations':
        return stations.layout
    if pathname == '/apps/forecast':
        return forecast.layout
    else:
        return gettoday.layout

if __name__ == '__main__':
    app.run_server(debug=True)




