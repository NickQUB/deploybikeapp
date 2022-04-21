#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Import Python Packages
#Import Python Packages
import dash
import dash_table
from dash import Dash,dcc,html, Input, Output
#import dash_core_components as dcc
# import dash_html_components as html
import dash_bootstrap_components as dbc
#from dash.dependencies import Input, Output
from dash_table.Format import Format, Sign

import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objs as go

import pandas as pd
import numpy as np

from sqlalchemy import create_engine
# import mysql.connector
# from mysql.connector import Error
from datetime import datetime, timedelta
import pytz
from pytz import timezone

from app import app ###############################################################################################
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

timeZone='America/New_York'


# In[2]:


# Connect to database and read in data to DataFrames

localhost = 'pittsburghdb.c9rczggk5uzn.eu-west-2.rds.amazonaws.com'
username = 'pittsburghadmin'
password = 'Pitts$8burgh'
databasename='pittsburgh'
port=3306

database_connection = create_engine('mysql+mysqlconnector://{0}:{1}@{2}/{3}'
            .format(username, password,localhost, databasename)).connect()
# database_connection = mysql.connector.connect(host=localhost, database=databasename,
# user=username, password=password)

JourneysDF = pd.read_sql('SELECT * FROM journeys', con=database_connection)
StationsDF = pd.read_sql('SELECT * FROM stations', con=database_connection)
BikesOutDF = pd.read_sql('SELECT * FROM bikesout', con=database_connection)
BikesLocationsDF = pd.read_sql('SELECT * FROM bikeslocations', con=database_connection)


# In[3]:

#Create DataFrames for use in visualisations

#Group Bikes by StationID
BikesGroupedDF = BikesLocationsDF.groupby(['stationid'])['bikeid'].count().reset_index(name="countbikes")
BikesGroupedDF

#Find stations with low number of bikes, and low number of spaces
StationBikesDF = StationsDF.merge(BikesGroupedDF,on=['stationid'],how='left')
StationBikesDF['countbikes']=StationBikesDF['countbikes'].fillna(0)
StationBikesDF['countbikes']=StationBikesDF['countbikes'].astype(int)
StationBikesDF['availablespaces']=StationBikesDF['racksize']-StationBikesDF['countbikes']
StationBikesDF=StationBikesDF[(StationBikesDF['countbikes']<3) | (StationBikesDF['availablespaces']<3)]
StationBikesDF


# In[4]:

#Set Local Time

# now=datetime.now()
# nowLocal = now.astimezone(timezone(timeZone))
nowLocal= datetime.now(pytz.timezone('Europe/London'))
#setTimeFormat = "%Y-%m-%d %H:%M:%S"

localDateTime = datetime.strptime(nowLocal.strftime('%Y-%m-%d'), '%Y-%m-%d')


#Format times for visualisatiohs
nowLocalWords=nowLocal.strftime("%A %d %B %Y")
timeHHMM = nowLocal.strftime("%H:%M")

Tomorrow = localDateTime + timedelta(days=1)

timeLocalHourAgo =nowLocal+ timedelta(hours=-1)
timeLocalHourAgo= timeLocalHourAgo.replace(tzinfo=None)



# In[5]:


# Count of Bikes in Stations and Bikes of Road for visualisations
BikesInStationsData = len(BikesLocationsDF.index)
BikesOutData = len(BikesOutDF.index)


# In[6]:


#Count number of journeys made today for visulalisations
JourneysDF = JourneysDF[(JourneysDF['datetimeout'])>localDateTime]
JourneysDF = JourneysDF[(JourneysDF['datetimein'])<Tomorrow]


JourneysTodayData = len(JourneysDF)


# In[7]:


#Count number of journeys made in the last hour for visualisations
JourneysHourData = len(JourneysDF[(JourneysDF['datetimein'])>timeLocalHourAgo])


# In[8]:


#Merge station dataframe to journeys dataframe so to add station name and latitude longitude data (First for Station Bike out
#taken out from)
JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationoutid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)

JourneysDF.head(5)


# In[9]:


#Rename columns
JourneysDF=JourneysDF.rename(columns={'stationname': 'stationout','latitude': 'latout','longitude': 'longout'})


# In[10]:


#Then merge again to get the same data for the station bike returned to
JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationinid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)


# In[11]:


#Rename headings again
JourneysDF=JourneysDF.rename(columns={'stationname': 'stationin','latitude': 'latin','longitude': 'longin'})


# In[12]:


#Take a copy of DataFrame
JourneysFinalDF = JourneysDF
#Split DateTime fields to date and time to make easier to work with and for visualisations
JourneysFinalDF['dateout'] = [d.date() for d in JourneysFinalDF['datetimeout']]
JourneysFinalDF['dateout'] = pd.to_datetime(JourneysFinalDF['dateout'],format='%Y-%m-%d')
JourneysFinalDF['datein'] = [d.date() for d in JourneysFinalDF['datetimein']]
JourneysFinalDF['datein'] = pd.to_datetime(JourneysFinalDF['datein'],format='%Y-%m-%d')

JourneysFinalDF['timeout'] = JourneysFinalDF['datetimeout'].dt.strftime('%H:%M:%S')
JourneysFinalDF['timein'] = JourneysFinalDF['datetimein'].dt.strftime('%H:%M:%S')



# In[13]:


#Further split date time fields to columns of days of week and hours of day for graphing purposes
JourneysFinalDF['dayout']=JourneysFinalDF['dateout'].dt.day_name()
JourneysFinalDF['dayin']=JourneysFinalDF['datein'].dt.day_name()
JourneysFinalDF['hourout']=pd.to_datetime(JourneysFinalDF['timeout']).dt.hour
JourneysFinalDF['hourin']=pd.to_datetime(JourneysFinalDF['timein']).dt.hour

JourneysFinalDF['journeytime']=((JourneysFinalDF['datetimein']-JourneysFinalDF['datetimeout']).dt.total_seconds()/60)
JourneysFinalDF['journeytime']=JourneysFinalDF['journeytime'].astype(int)

JourneysFinalDF= JourneysFinalDF[(JourneysFinalDF['journeytime'] >= 5)]
JourneysFinalDF= JourneysFinalDF[(JourneysFinalDF['datetimeout'] > '2020-12-31')]
JourneysFinalDF.reset_index(drop=True, inplace=True)


# In[14]:


#Create GroupedOutDF to show data for days of the week 

GroupedDayOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dayout'])['bikeid'].count()).reset_index()
GroupedDayOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)
daycode={'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6,'Sunday':7}
GroupedDayOutDF['DayCode']=GroupedDayOutDF['dayout'].map(daycode)
GroupedDayOutDF=GroupedDayOutDF.sort_values(by=['DayCode'],ascending=True)


# In[15]:


# Create number of movements out and in of stations for the map
out_df = JourneysFinalDF[['stationout', 'stationoutid', 'dateout']]
out_df['BikesOut'] = 1
out_df['BikesIn'] = 0
out_df['BikesMovements'] = 1
out_df.rename(columns={'stationout': 'Stationname', 'stationoutid': 'StationID'}, inplace=True)

return_df = JourneysFinalDF[['stationin', 'stationinid', 'dateout']]
return_df['BikesOut'] = 0
return_df['BikesIn'] = 1
return_df['BikesMovements'] = 1
return_df.rename(columns={'stationin': 'Stationname', 'stationinid': 'StationID'}, inplace=True)

# create a data frame of bikes out and returns to each station
station_df = pd.concat([out_df, return_df], ignore_index=True)
gstation_df = pd.DataFrame(station_df.groupby(['Stationname', 'StationID', 'dateout'])[
                               'BikesOut', 'BikesIn', 'BikesMovements'].sum()).reset_index()

# merge that with stations table from the database to get latitude and longitude data for the map
mergeddf = pd.merge(StationsDF, gstation_df,
                    left_on='stationid',
                    right_on='StationID',
                    how='left')
mergeddf.fillna(0, inplace=True)

# group stations with their lat/longs with sums of bikes in, out and total movements
newdf = mergeddf[['stationname', 'longitude', 'latitude', 'BikesOut', 'BikesIn', 'BikesMovements']]

# get a ratio of in/out movements to use in visualisations if required
newdf['ratio'] = (newdf['BikesOut'] / newdf['BikesMovements']) * 100
newdf['BikesMovements'] = newdf['BikesMovements'].astype(int)

# set size of bubble on map dependent on the number of movements in station.
# set size of bubble on map dependent on the number of movements in station.
# newdf['size'] = newdf['BikesMovements'].apply(lambda x: (np.sqrt(x/100) + 1) if x > 50 else (np.log(x) / 2 + 1)).replace(np.NINF, 0) * 0.5
# newdf['size'] = newdf['size'].map({0:0,range(1,5):3,range(6,10):4,range(11,16):5,range(19,25):6,
#                                          range(26,40):8,range(41,80):10,range(81,1000):15})

bins = [-1000, 0, 5, 10, 16, 25, 40, 80, np.inf]
names = [3, 4, 5, 6, 8, 10, 15, 20]
newdf['size'] = pd.cut(newdf['BikesMovements'], bins, labels=names)

# In[16]:


#Set up map

figmap = go.Figure(
    go.Scattermapbox(
        lat=newdf['latitude'],
        lon=newdf['longitude'],
        mode='markers',
        
        marker=go.scattermapbox.Marker( 
           size=(newdf['BikesMovements']),
        ),
        customdata=np.stack((pd.Series(newdf['stationname']), newdf['BikesOut'], newdf['BikesIn'],newdf['BikesMovements']), axis=-1),
        hovertemplate= """<extra></extra>
      <em>%{customdata[0]}  </em><br>
  ➡️  %{customdata[1]} Bikes Taken<br>
  ⬅️  %{customdata[2]} Bikes Returned<br>
  ↔️ %{customdata[3]} Bike Movements""",
    )
)


# Specify layout information
figmap.update_layout(
    font_family="Arial",
    font_color="blue",
    font_size=12,
    margin = dict(l = 0, r = 0, t = 0, b = 0),
    
    title=dict(
        text='<b>Todays Bike Pick Up and Returns</b>',
        x=0.5,
        y=0.85,
        font=dict(
            family="Arial",
            size=20,
            color='#000000'
        )),
    mapbox=dict(
        accesstoken='pk.eyJ1Ijoibmlja21hcHMiLCJhIjoiY2t0YWV4amJ2MDE4NTJvbGp5bm1xaHR6aCJ9.6GRCStGG-bw5vZPjkXsZKA', 
        center=go.layout.mapbox.Center(lat=40.44, lon=-79.98),
        zoom=11.5
    )
)


# In[17]:


#Create dataframes of completed journeys for line plot.
completeOutDF=pd.DataFrame(columns=[])
completeOutDF['datetimeout']=JourneysFinalDF['datetimeout']
completeOutDF.sort_values(by=['datetimeout'],inplace=True)
completeOutDF['Count']= range(1, 1+len(completeOutDF))
completeOutDF['Count2'] = np.arange(completeOutDF.shape[0])

completeInDF=pd.DataFrame(columns=[])
completeInDF['datetimein']=JourneysFinalDF['datetimein']
completeInDF.sort_values(by=['datetimein'],inplace=True)
completeInDF['Count']= range(1, 1+len(completeInDF))


figLine = go.Figure()
figLine.add_trace(go.Scatter(x=completeOutDF['datetimeout'], y=completeOutDF['Count'],
                    mode='lines',
                    name='Bikes Going Out'))
figLine.add_trace(go.Scatter(x=completeInDF['datetimein'],y=completeInDF['Count'],
                    mode='lines',
                    name='Bikes Returning'))
figLine.update_layout(
    title={
        'text': "Bike Movements Over Today",
        'y':0.85,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    xaxis_title="Time of Day",
    yaxis_title="Number of Bikes")


# In[18]:


# Workings for Cards on application page


menu_content = [
    dbc.CardHeader("Pittsburgh Healthy Ride Bike Scheme",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H3("Current Network Status",className="card-title"),
            html.H4("Figures correct to local time of", className="card-title"),
            html.H4(f"{timeHHMM}"),
            html.H4(f"{nowLocalWords}"),
            html.H4(" "),
            html.H5("Please select to view other data"),
            html.Div([
            dbc.Button("Historic Data", color="primary", className="mr-1", href='/apps/overall'),
            dbc.Button("Station Data", color="primary", className="mr-1", href='/apps/stations'),
            dbc.Button("Forecast Use", color="primary", className="mr-1", href='/apps/forecast'),
            ]
        ),
            
        ],style={'text-align':'center'}
    ),
]



card_content1 = [
    dbc.CardHeader("BIKE JOURNEYS",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H5("Number of bike journeys today", className="card-title"),
            html.H3(f"{JourneysTodayData}",
                className="card-text",
            ),
        ],style={'text-align':'center'}
    ),
]

card_content2 = [
    dbc.CardHeader("BIKE JOURNEYS",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H5("Number of bike journeys in the last hour", className="card-title"),
            html.H3(f"{JourneysHourData}",
                className="card-text",
            ),
        ],style={'text-align':'center'}
    ),
]

card_content3 = [
    dbc.CardHeader("BIKE IN STATIONS",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H5("Number of bikes available in all stations", className="card-title"),
            html.H3(f"{BikesInStationsData}",
                className="card-text",
            ),
        ],style={'text-align':'center'}
    ),
]

card_content4 = [
    dbc.CardHeader("BIKES ON ROAD",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H5("Number of bikes currently on the road", className="card-title"),
            html.H3(f"{BikesOutData}",
                className="card-text",
            ),
        ],style={'text-align':'center'}
    ),
]


# In[19]:

app.title = "Pittsburgh Healthy Bike Network Analysis!"
#Design layout of application page

layout = dbc.Container([

    dbc.Row([

        dbc.Col([
            dbc.Card([
                dbc.CardImg(
                    src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Healthy_Ride.png",
                    bottom=True),
            ],
                style={"width": "50%", 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
            )
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3,
            xl=3,

        ),

        dbc.Col([
            dbc.Card(menu_content, color="warning", inverse=True, )

        ], xs=12, sm=12, md=6, lg=6, xl=6,

        ),

        dbc.Col([
            dbc.Card([
                dbc.CardImg(
                    src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Healthy_Ride.png",
                    bottom=True),
            ],
                style={"width": "50%", 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
            )
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3,
            xl=3,

        ),

    ],

    ),

    ##########################################################################################################################

    dbc.Row(

        [
            dbc.Col([dbc.Card(card_content1, color="primary", inverse=True)], xs=12, sm=12, md=3, lg=3, xl=3, ),
            dbc.Col([dbc.Card(card_content2, color="primary", inverse=True)], xs=12, sm=12, md=3, lg=3, xl=3, ),
            dbc.Col([dbc.Card(card_content3, color="success", inverse=True)], xs=12, sm=12, md=3, lg=3, xl=3, ),
            dbc.Col([dbc.Card(card_content4, color="danger", inverse=True)], xs=12, sm=12, md=3, lg=3, xl=3, ),
        ],

    ),

    ###########################################################################################################################

    dbc.Row([
        dbc.Col([
            #          html.Div(
            #             children=[
            #                 html.Div(
            #                     children=dcc.Graph(id='map', figure=figmap),
            #                 ),

            #             ],

            #         ),
            dcc.Graph(id='map', figure=figmap)
        ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'},
            xs=12, sm=12, md=12, lg=12, xl=12,
        ),
    ], style={"padding-bottom": "50px"}

    ),

    ###########################################################################################################################

    dbc.Row([
        dbc.Col([
            #         html.Div(
            #             children=[
            #                 html.Div(
            #                     children=dcc.Graph(
            #                         id="Bikeplot", config={"displayModeBar": False},figure=figLine,

            #                     ),

            #                 ),

            #             ],

            #         ),

            dcc.Graph(id='Bikeplot', figure=figLine, config={"displayModeBar": True})
        ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12,
            xl=12,

        ),
    ], style={"padding-bottom": "50px"}

    ),

    ###########################################################################################################################

    dbc.Row([
        dbc.Col([

            #                   dash_table.DataTable(
            #  #                sort_action='native',
            #                 data=StationBikesDF.to_dict('records'),
            #   #                      id='mydatatable',

            #                 # columns=[{'id': c, 'name': c} for c in StationBikesDF.columns],
            #                   columns=[
            #             {'name': 'Station Name', 'id': 'stationname', 'type': 'text', 'editable': True},
            #             {'name': 'Total Racks', 'id': 'racksize', 'type': 'numeric', 'editable': True},
            #             {'name': 'countbikes', 'id': 'countbikes', 'type': 'numeric', 'editable': True},
            #             {'name': 'availablespaces', 'id': 'availablespaces', 'type': 'numeric', 'editable': True},],
            #    #             style_cell={
            #    #     'overflow': 'hidden',
            #    #     'textOverflow': 'ellipsis',
            #    #     'maxWidth': 0
            #    # },
            #  #                style_table={'overflowX': 'auto'},

            # #         style_data_conditional=[
            # #         {
            # #             'if': {'row_index': 'odd'},
            # #             'backgroundColor': 'rgb(220, 220, 220)',
            # #         }
            # #     ],

            #         style_data_conditional=([

            #                 {
            #                     'if': {
            #                         'filter_query': '{availablespaces} > 5',
            #                         'column_id': 'availablespaces'
            #                     },
            #                     'backgroundColor': 'rgb(220, 220, 220)',
            #                     #'fontWeight': 'bold'
            #                 }

            #         ],),
            #         ),

            dash_table.DataTable(
                sort_action='native',
                data=StationBikesDF.to_dict('records'),
                id='mydatatable',
                # columns=[{'id': c, 'name': c} for c in StationBikesDF.columns],
                columns=[
                    {'name': 'Station Name', 'id': 'stationname', 'type': 'text', 'editable': True},
                    {'name': 'Total Racks', 'id': 'racksize', 'type': 'numeric', 'editable': True},
                    {'name': 'countbikes', 'id': 'countbikes', 'type': 'numeric', 'editable': True},
                    {'name': 'availablespaces', 'id': 'availablespaces', 'type': 'numeric', 'editable': True}, ],

                style_cell={
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0
                },

                style_data_conditional=[
                    {

                        'if': {
                            'filter_query': '{availablespaces} > 10',
                            'column_id': 'availablespaces'
                        },
                        'backgroundColor': 'rgb(220, 220, 220)',
                    }
                ], )

        ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12,
            xl=12,
        ),

    ],
    ),

], fluid=True)


# if __name__ == "__main__": ####################################################################################################
#     app.run_server(debug=True)################################################################################################
