import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objs as go

import pandas as pd
import numpy as np

import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from pytz import timezone

################################################################### New Added
import sshtunnel
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
import pytz


##comment this line if just running on own ##############################################################################
# from app import app


sshHostname = 'ssh.eu.pythonanywhere.com'
sshUsername = 'NickQUB'
sshPassword = 'Pyth0n$$'
bindAddress = 'NickQUB.mysql.eu.pythonanywhere-services.com'

username='NickQUB'
pword='C0bra$$$'
dbname='NickQUB$belfast'

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0


###############################################################################################


tunnel = SSHTunnelForwarder(
        sshHostname,
        ssh_username=sshUsername,
        ssh_password=sshPassword,
        remote_bind_address = (bindAddress, 3306)
    )
tunnel.start()


port=tunnel.local_bind_port
host = '127.0.0.1'

database_connection = create_engine('mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}'
            .format(username, pword,host,port,dbname)).connect()



JourneysDF = pd.read_sql('SELECT bikeid,stationoutid,datetimeout,stationinid,datetimein FROM journeys', con=database_connection)
StationsDF = pd.read_sql('SELECT stationid,stationname,racksize,latitude,longitude FROM stations', con=database_connection)
BikesOutDF = pd.read_sql('SELECT bikeid,stationid,datetimeout FROM bikesout', con=database_connection)
BikesLocationsDF = pd.read_sql('SELECT bikeid,stationid FROM bikeslocations', con=database_connection)


###################################################################################

############################################################ TIME ZONES


timeZone='Europe/London'

#Set Local Time
nowLocal= datetime.now(pytz.timezone(timeZone))
localDateTime = datetime.strptime(nowLocal.strftime('%Y-%m-%d'), '%Y-%m-%d')


#Format for use in visualisatiohs
nowLocalWords=nowLocal.strftime("%A %d %B %Y")
timeHHMM = nowLocal.strftime("%H:%M")

####################################################################

#Merge Journeys and Stations dataframes. Drop and rename columns

JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationoutid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)

JourneysDF=JourneysDF.rename(columns={'stationname': 'stationout','latitude': 'latout','longitude': 'longout'})

#Merge DataFrame again to get the stations in this time. Drop and rename columns
JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationinid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)
JourneysDF=JourneysDF.rename(columns={'stationname': 'stationin','latitude': 'latin','longitude': 'longin'})

#Take a copy of Journeys Data Frame, create some extra date/time cells and format ready for use in visualisations
JourneysFinalDF = JourneysDF
JourneysFinalDF['dateout'] = [d.date() for d in JourneysFinalDF['datetimeout']]
JourneysFinalDF['dateout'] = pd.to_datetime(JourneysFinalDF['dateout'],format='%Y-%m-%d')
JourneysFinalDF['datein'] = [d.date() for d in JourneysFinalDF['datetimein']]
JourneysFinalDF['datein'] = pd.to_datetime(JourneysFinalDF['datein'],format='%Y-%m-%d')

JourneysFinalDF['timeout'] = JourneysFinalDF['datetimeout'].dt.strftime('%H:%M:%S')
JourneysFinalDF['timein'] = JourneysFinalDF['datetimein'].dt.strftime('%H:%M:%S')

#Set up day in week, hour of day columns for use in visualisations

JourneysFinalDF['dayout']=JourneysFinalDF['dateout'].dt.day_name()
JourneysFinalDF['dayin']=JourneysFinalDF['datein'].dt.day_name()
JourneysFinalDF['hourout']=pd.to_datetime(JourneysFinalDF['timeout']).dt.hour
JourneysFinalDF['hourin']=pd.to_datetime(JourneysFinalDF['timein']).dt.hour

JourneysFinalDF['journeytime']=((JourneysFinalDF['datetimein']-JourneysFinalDF['datetimeout']).dt.total_seconds()/60)
JourneysFinalDF['journeytime']=JourneysFinalDF['journeytime'].astype(int)

JourneysFinalDF= JourneysFinalDF[(JourneysFinalDF['journeytime'] >= 3)]
JourneysFinalDF.reset_index(drop=True, inplace=True)

JourneysFinalDF=JourneysFinalDF.sort_values(by=['dateout'])

#Group Data For Graphs
#1 - All Dates
GroupedDateOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout'])['bikeid'].count()).reset_index()
GroupedDateOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)
GroupedDateOutDF['dateout'] = pd.to_datetime(GroupedDateOutDF['dateout']).dt.date

#2 - Day Of Week
GroupedDayOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout','dayout'])['bikeid'].count()).reset_index()
GroupedDayOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)
daycode={'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6,'Sunday':7}
GroupedDayOutDF['DayCode']=GroupedDayOutDF['dayout'].map(daycode)
#GroupedDayOutDF=GroupedDayOutDF.sort_values(by=['DayCode'],ascending=True)
DayOutSummaryDF=pd.DataFrame(GroupedDayOutDF.groupby(['dayout','DayCode'])['NumberPickUps'].sum()).reset_index()
DayOutSummaryDF=DayOutSummaryDF.sort_values(by=['DayCode'],ascending=True)
print(DayOutSummaryDF)

#3 - Hour of Day
GroupedHourOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout','hourout'])['bikeid'].count()).reset_index()
GroupedHourOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)

# Set up menu comment and link buttons
menu_content = [
    dbc.CardHeader("Pittsburgh Healthy Ride Bike Scheme", style={'text-align': 'center'}),
    dbc.CardBody(
        [
            html.H3("Current Network Status", className="card-title"),
            html.H4("Figures correct to local time of", className="card-title"),
            html.H4(f"{timeHHMM}"),
            html.H4(f"{nowLocalWords}"),
            html.H4(" "),
            html.H5("Please select to view other data"),
            html.Div([
                dbc.Button("Today's Data", color="primary", className="mr-1", href='/apps/gettoday'),
                dbc.Button("Station Data", color="primary", className="mr-1", href='/apps/stations'),
                dbc.Button("Forecast Use", color="primary", className="mr-1", href='/apps/forecast'),
            ]
            ),

        ], style={'text-align': 'center'}
    ),
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])  ########################################
server = app.server

app.title = "Pittsburgh Healthy Ride Bikes Network Analysis!"  ###########################################################################

## Header

app.layout = dbc.Container([

    ###########################################################################################################################
    dbc.Row([
        dbc.Col([
            html.Div(
                children=[
                    html.Div(
                        children="Select date range to view", className="menu-title",
                        style={'color': 'green', 'fontSize': 28},

                    ),
                    dcc.DatePickerRange(
                        id="date-range",
                        min_date_allowed=JourneysFinalDF.dateout.min().date(),
                        max_date_allowed=JourneysFinalDF.dateout.max().date(),
                        start_date=JourneysFinalDF.dateout.min().date(),
                        end_date=JourneysFinalDF.dateout.max().date()

                    ),
                ], className="menu", style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
            ),
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12,
            xl=12,

        ),
    ],
    ),

    #    ###########################################################################################################################

    dcc.Graph(
        id="BikesTotalOverTime", figure={}

    ),
    html.P('fgdfg')
    #                className="card",

    #      className="wrapper",
    #    ),

])

# #############################################################################################################################
if __name__ == "__main__":
    app.run_server(debug=False)


@app.callback(

    Output("BikesTotalOverTime", "figure"),

    [
        Input("date-range", "start_date"),
        Input("date-range", "end_date")
    ],
)
# Set a function to perform on the input parameters provided above that come from the user setting drop down menu options
# on the web application
def update_charts_date(start_date, end_date):
    #
    mask = (
             (GroupedDateOutDF.dateout >= start_date) & (GroupedDateOutDF.dateout <= end_date)
                )
    #     #the filtered_data is a subset (based on the mask inputs above chosen from drop down menu by the user)
    # of the total GroupedDF (which contains total number of bike pickups grouped by date)

    filtered_data_date = GroupedDateOutDF.loc[mask, :]

    # fig below is setting the parameters of the line graph object from the filtered data set
    figDate = px.line(filtered_data_date, x=filtered_data_date["dateout"], y=filtered_data_date["NumberPickUps"])
    figDate.update_traces(hovertemplate='Bikes Hired: %{y} <br>Date: %{x}'+'<extra></extra>')
    figDate.update_layout(title={
        'text': "Number of Network Rentals Over Time",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Date of Rental',
                   yaxis_title='Total Bikes Picked Up From Station')
    return figDate


