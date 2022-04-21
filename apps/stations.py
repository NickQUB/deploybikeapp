#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
#import dash_auth
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
from datetime import datetime
from pytz import timezone

from app import app
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)




# In[2]:


#Set up Database Connection

localhost = 'pittsburghdb.c9rczggk5uzn.eu-west-2.rds.amazonaws.com'
username = 'pittsburghadmin'
password = 'Pitts$8burgh'
databasename='pittsburgh'
port=3306


database_connection = mysql.connector.connect(host=localhost, database=databasename, 
user=username, password=password)

JourneysDF = pd.read_sql('SELECT * FROM journeys', con=database_connection)
StationsDF = pd.read_sql('SELECT * FROM stations', con=database_connection)
BikesOutDF = pd.read_sql('SELECT * FROM bikesout', con=database_connection)
BikesLocationsDF = pd.read_sql('SELECT * FROM bikeslocations', con=database_connection)


# In[3]:


timeZone='America/New_York'

#Set Local Time

now=datetime.now()
nowLocal = now.astimezone(timezone(timeZone))
localDateTime = datetime.strptime(nowLocal.strftime('%Y-%m-%d'), '%Y-%m-%d')


#Format for visualisatioh
nowLocalWords=nowLocal.strftime("%A %d %B %Y")
timeHHMM = nowLocal.strftime("%H:%M")


# In[4]:


#Merge Journeys and Stations dataframes. Drop and rename columns
JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationoutid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)
JourneysDF=JourneysDF.rename(columns={'stationname': 'stationout','latitude': 'latout','longitude': 'longout'})


# In[5]:


#Merge DataFrame again to get the stations in this time. Drop and rename columns
JourneysDF = JourneysDF.merge(StationsDF[['stationid','stationname','latitude','longitude']],
                                              left_on=['stationinid'],right_on=['stationid'],how='left')
JourneysDF.drop('stationid', inplace=True, axis=1)
JourneysDF=JourneysDF.rename(columns={'stationname': 'stationin','latitude': 'latin','longitude': 'longin'})


# In[6]:


#Take a copy of Journeys Data Frame, create some extra date/time cells and format ready for use in visualisations
JourneysFinalDF = JourneysDF
JourneysFinalDF['dateout'] = [d.date() for d in JourneysFinalDF['datetimeout']]
JourneysFinalDF['dateout'] = pd.to_datetime(JourneysFinalDF['dateout'],format='%Y-%m-%d')
JourneysFinalDF['datein'] = [d.date() for d in JourneysFinalDF['datetimein']]
JourneysFinalDF['datein'] = pd.to_datetime(JourneysFinalDF['datein'],format='%Y-%m-%d')

JourneysFinalDF['timeout'] = JourneysFinalDF['datetimeout'].dt.strftime('%H:%M:%S')
JourneysFinalDF['timein'] = JourneysFinalDF['datetimein'].dt.strftime('%H:%M:%S')


# In[7]:


#Set up day in week, hour of day columns for use in visualisations
JourneysFinalDF['dayout']=JourneysFinalDF['dateout'].dt.day_name()
JourneysFinalDF['dayin']=JourneysFinalDF['datein'].dt.day_name()
JourneysFinalDF['hourout']=pd.to_datetime(JourneysFinalDF['timeout']).dt.hour
JourneysFinalDF['hourin']=pd.to_datetime(JourneysFinalDF['timein']).dt.hour

JourneysFinalDF['journeytime']=((JourneysFinalDF['datetimein']-JourneysFinalDF['datetimeout']).dt.total_seconds()/60)
JourneysFinalDF['journeytime']=JourneysFinalDF['journeytime'].astype(int)

JourneysFinalDF= JourneysFinalDF[(JourneysFinalDF['journeytime'] >= 3)]
JourneysFinalDF.reset_index(drop=True, inplace=True)


# In[8]:


#Group Data For Graphs

GroupedDF= pd.DataFrame(JourneysFinalDF.groupby(['stationout','dateout'])['bikeid'].count()).reset_index()
GroupedDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)


# In[9]:


#Group by station, date and hour for second graph
Grouped2DF= pd.DataFrame(JourneysFinalDF.groupby(['stationout','dateout','hourout'])['bikeid'].count()).reset_index()
Grouped2DF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)
Grouped2DF.isna().sum()


# In[10]:


#Set up mask for reading in and filtering user selections

mask = (
         (GroupedDF.stationout == "Hobart St & Wightman St")
        
    )

filtered_data = GroupedDF.loc[mask, :]

print(filtered_data)


# In[11]:


#Set up 2nd mask for reading in and filtering user selections

mask2 = (
         (Grouped2DF.stationout == "Hobart St & Wightman St")
        
    )

filtered_data2 = Grouped2DF.loc[mask2, :]

print(filtered_data2)


# In[12]:


#Set up menu comment and link buttons
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
            dbc.Button("Today's Data", color="primary", className="mr-1", href='/apps/gettoday'),
            dbc.Button("Historic Data", color="primary", className="mr-1", href='/apps/overall'),  
            dbc.Button("Forecast Use", color="primary", className="mr-1", href='/apps/forecast'),
            ]
        ),
            
        ],style={'text-align':'center'}
    ),
]


# In[ ]:


#Set out layout for application page


## Header

layout = dbc.Container([
  
     dbc.Row([
    
        dbc.Col([
            dbc.Card([
                    dbc.CardImg(
                        src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Healthy_Ride.png",
                        bottom=True),
                ],
                  style={"width": "50%" ,'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
            )
        ],style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3, xl=3, 
          
        ),


        dbc.Col([
            dbc.Card(menu_content, color="warning", inverse=True, style={'height':'90%'})
            
            
        ], xs=12, sm=12, md=6, lg=6, xl=6,
            
            ),
        
        
        
        dbc.Col([
            dbc.Card([
                    dbc.CardImg(
                        src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Healthy_Ride.png",
                        bottom=True),
                ],
                 style={"width": "50%" ,'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
            )
        ],style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3, xl=3, 
          
        ),
        
    ], style={"padding-bottom": "20px"}
           
    ),
    
  ####################################################################################################################  
    
    
    
   ## MENUS  

    dbc.Row([
        
        dbc.Col([ 
             
                html.Div(
                    children=[
                        html.Div(children="Select bike station", className="menu-title",style={'color': 'green', 'fontSize': 28, 'text-align': 'center'}),
                        dcc.Dropdown(
                            id="station-filter",
                            options=[
                                {"label": stationout, "value": stationout}
                                for stationout in np.sort(GroupedDF.stationout.unique())
                            ],
                            value="Hobart St & Wightman St",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
        ],style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
        ),     
    ],      
    ),       
    
    
     dbc.Row([
        
        dbc.Col([  


                 html.Div(
                    children=[
                        html.Div(
                            children="Select date range", className="menu-title",style={'color': 'blue', 'fontSize': 28, 'text-align': 'center'}
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=JourneysFinalDF.dateout.min().date(),
                            max_date_allowed=JourneysFinalDF.dateout.max().date(),
                            start_date=JourneysFinalDF.dateout.min().date(),
                            end_date=JourneysFinalDF.dateout.max().date(),
                        ),
                    ]
                ),
           
        
 ],style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
           
        ),
        
          ],style={"padding-bottom": "10px"}
          ),
              
              
###########################################################################################################        
## GRAPH
    
    #Display graph using a combination of Dash Boostrap components (dbc) for row, column
    #And dash core components (dcc) for displaying the graph
    #And dash html components for the HTML like commands
    
    dbc.Row([
    dbc.Col([
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="BelfastJourneyPickups", config={"displayModeBar": False},
                        
                    ),
                    
                ),

            ],

        ),
        ],style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,   

        ), 
      ],style={"padding-bottom": "50px"}
   ),

###############################################################################################################
    
      dbc.Row([    
        dbc.Col([ 
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="PickUpsByHourOfDay", config={"displayModeBar": False}, 
                        
                    ),
                    
                ),

            ],
           
        ),
        
      ],style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
             
   ),
],
),

], fluid=True)


###############################################################################################################
# Set the input and out parameter for the callback
@app.callback(
    
    Output("BelfastJourneyPickups", "figure"),  
    
    [
        Input("station-filter", "value"),        
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
# Set a function to perform on the input parameters provided above that come from the user setting drop down menu options
# on the web application
def update_charts(stationout, start_date, end_date):
#     
    mask = (
         (GroupedDF.stationout == stationout)
       & (GroupedDF.dateout >= start_date)
       & (GroupedDF.dateout <= end_date)
    )
    #the filtered_data is a subset (based on the mask inputs above chosen from drop down menu by the user) 
    #of the total GroupedDF (which contains total number of bike pickups grouped by date)
    filtered_data = GroupedDF.loc[mask, :]
    
    #fig below is setting the parameters of the line graph object from the filtered data set
    fig = px.line(filtered_data, x=filtered_data["dateout"], y=filtered_data["NumberPickUps"],)
    fig.update_layout(title={
        'text': "Number of station pick ups per day",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Date of Rental',
                   yaxis_title='Total Bikes Picked Up From Station')

    return fig

#######################################################################################################
@app.callback(
    
    Output("PickUpsByHourOfDay", "figure"),  ##add other in here
    
    [
        Input("station-filter", "value"),        
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(stationout, start_date, end_date):
    mask2 = (
         (Grouped2DF.stationout == stationout)
       & (Grouped2DF.dateout >= start_date)
       & (Grouped2DF.dateout <= end_date)
    )
    filtered_data2 = Grouped2DF.loc[mask2, :]
    
    figbarplot = px.bar(filtered_data2, x=filtered_data2['hourout'], y=filtered_data2['NumberPickUps'])
    figbarplot.update_layout(title={
        'text': "Number of pick ups from the station by hour of the day",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Hour of Day',
                   yaxis_title='Number of Hires',barmode='group')
    figbarplot.update_traces(marker_color='yellow')
    
    return figbarplot


# if __name__ == "__main__": ####################################################################################################
#     app.run_server(debug=True)#####################################################################

#######################################################################################################


# In[ ]:




