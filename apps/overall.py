#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

from app import app
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)






# In[2]:


#database Connections

localhost = 'pittsburghdb.c9rczggk5uzn.eu-west-2.rds.amazonaws.com'
username = 'pittsburghadmin'
password = 'Pitts$8burgh'
databasename='pittsburgh'
port=3306


database_connection = mysql.connector.connect(host=localhost, database=databasename, 
user=username, password=password)

#Import database tables to dataframes
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


#Format for use in visualisatiohs
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


# In[7]:


#Take a copy of Journeys Data Frame, create some extra date/time cells and format ready for use in visualisations
JourneysFinalDF = JourneysDF
JourneysFinalDF['dateout'] = [d.date() for d in JourneysFinalDF['datetimeout']]
JourneysFinalDF['dateout'] = pd.to_datetime(JourneysFinalDF['dateout'],format='%Y-%m-%d')
JourneysFinalDF['datein'] = [d.date() for d in JourneysFinalDF['datetimein']]
JourneysFinalDF['datein'] = pd.to_datetime(JourneysFinalDF['datein'],format='%Y-%m-%d')

JourneysFinalDF['timeout'] = JourneysFinalDF['datetimeout'].dt.strftime('%H:%M:%S')
JourneysFinalDF['timein'] = JourneysFinalDF['datetimein'].dt.strftime('%H:%M:%S')


JourneysFinalDF.dtypes


# In[8]:


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


JourneysFinalDF


# In[9]:


#Group Data For Graphs
#1 - All Dates
GroupedDateOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout'])['bikeid'].count()).reset_index()
GroupedDateOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)

#2 - Day Of Week
GroupedDayOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout','dayout'])['bikeid'].count()).reset_index()
GroupedDayOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)
daycode={'Monday':1,'Tuesday':2,'Wednesday':3,'Thursday':4,'Friday':5,'Saturday':6,'Sunday':7}
GroupedDayOutDF['DayCode']=GroupedDayOutDF['dayout'].map(daycode)
GroupedDayOutDF=GroupedDayOutDF.sort_values(by=['DayCode'],ascending=True)
print(GroupedDayOutDF)

#3 - Hour of Day
GroupedHourOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout','hourout'])['bikeid'].count()).reset_index()
GroupedHourOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)


# In[10]:


# out_df = JourneysFinalDF[['stationout','stationoutid','dateout']]
# out_df['BikesOut'] = 1
# out_df['BikesIn'] = 0
# out_df['BikesMovements'] = 1
# out_df.rename(columns={'stationout':'Stationname','stationoutid':'StationID'},inplace=True)
# # print(out_df)

# return_df = JourneysFinalDF[['stationin','stationinid','dateout']]
# return_df['BikesOut'] = 0
# return_df['BikesIn'] = 1
# return_df['BikesMovements'] = 1
# return_df.rename(columns={'stationin':'Stationname','stationinid':'StationID'},inplace=True)
# # print(return_df)

# station_df = pd.concat([out_df,return_df],ignore_index=True)
# # print(station_df)


# #Stations = pd.read_csv('Stations.csv')
# mergeddf = pd.merge(station_df, StationsDF, 
#                      left_on = 'StationID', 
#                      right_on = 'stationid', 
#                      how='left')

# # print(mergeddf)


# newdf = pd.DataFrame(mergeddf.groupby(['stationname','longitude','latitude'])['BikesOut','BikesIn','BikesMovements'].sum()).reset_index()



# newdf['ratio'] = (newdf['BikesOut']/ newdf['BikesMovements'])*100



# newdf['size'] = (newdf['BikesMovements'].apply(lambda x: (np.sqrt(x/100) + 1) if x > 500 else (np.log(x) / 2 + 1)).replace(np.NINF, 0))*3

# print(newdf)


# In[11]:


# fig1 = go.Figure(data=[go.Bar(
#             x=GroupedDayOutDF.dayout.unique(), y=GroupedDayOutDF['NumberPickUps'],
#             text=GroupedDayOutDF['NumberPickUps'],
#             textposition='auto',
            
#         )])

# fig1.update_layout(title={
#         'text': "Bike Hires by Day of the Week",
#         'y':0.9,
#         'x':0.5,
#         'xanchor': 'center',
#         'yanchor': 'top'},
#                    xaxis_title='Day of the Week',
#                    yaxis_title='Number of Hires')


# In[12]:


# GroupedHourOutDF= pd.DataFrame(JourneysFinalDF.groupby(['hourout'])['bikeid'].count()).reset_index()
# GroupedHourOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)

# fig2 = go.Figure(data=[go.Bar(
#             x=GroupedHourOutDF.hourout.unique(), y=GroupedHourOutDF['NumberPickUps'],
#             text=GroupedHourOutDF['NumberPickUps'],
#             textposition='auto',
            
#         )])

# fig2.update_layout(title={
#         'text': "Bike Hires by Hour of the Day",
#         'y':0.9,
#         'x':0.5,
#         'xanchor': 'center',
#         'yanchor': 'top'},
#                    xaxis_title='Day of the Week',
#                    yaxis_title='Number of Hires')


# In[13]:


# GroupedDateOutDF= pd.DataFrame(JourneysFinalDF.groupby(['dateout'])['bikeid'].count()).reset_index()
# GroupedDateOutDF.rename(columns={'bikeid':'NumberPickUps'},inplace=True)



# fig3 = go.Figure()
# fig3.add_trace(go.Scatter(x=GroupedDateOutDF['dateout'], y=GroupedDateOutDF['NumberPickUps'],
#                     mode='lines',
#                     name='Bikes Going Out'))

# fig3.update_layout(
#     title={
#         'text': "Bike Hires over Time",
#         'y':0.85,
#         'x':0.5,
#         'xanchor': 'center',
#         'yanchor': 'top'},
#     xaxis_title="Date",
#     yaxis_title="Number of Bikes Hired")


# In[17]:


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
            dbc.Button("Station Data", color="primary", className="mr-1", href='/apps/stations'), 
            dbc.Button("Forecast Use", color="primary", className="mr-1", href='/apps/forecast'),
            ]
        ),
            
        ],style={'text-align':'center'}
    ),
]


# In[18]:



## Header

layout = dbc.Container([
  
     dbc.Row([
    
        dbc.Col([
            dbc.Card([
                    dbc.CardImg(
                        src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Healthy_Ride.png",
                        bottom=True)
                ],
                 
                style={"width": "50%" ,'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},
            )
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3, xl=3, 
          
        ),


        dbc.Col([
            dbc.Card(menu_content, color="warning", inverse=True)
            
            
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
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3, xl=3,
          
        ),
        
    ], style={"padding-bottom": "100px"}
           
    ),
    
 
    

   ########################################################################################################################### 
    dbc.Row([
          dbc.Col([ 
         html.Div(
                    children=[
                        html.Div(
                            children="Select date range to view", className="menu-title", style={'color': 'green', 'fontSize': 28},
                                                                                     
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=JourneysFinalDF.dateout.min().date(),
                            max_date_allowed=JourneysFinalDF.dateout.max().date(),
                            start_date=JourneysFinalDF.dateout.min().date(),
                            end_date=JourneysFinalDF.dateout.max().date(),
                        ),
                    ],  className="menu",style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                ),
   ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
          
        ),
    ], 
        ),
   ###########################################################################################################################
    
     dbc.Row([
         dbc.Col([
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="BikesTotalOverTime", config={"displayModeBar": False},
                        
                    ),
                    className="card",
                ),

            ],
            className="wrapper",
        ),
           ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
          
        ),
     ],
       
     ),

   ###########################################################################################################################
    
     dbc.Row([
         dbc.Col([
         html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="BikesDayOfWeek", config={"displayModeBar": False},
                        
                    ),
                    className="card",
                ),

            ],
            className="wrapper",
       
        ),
           ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
          
        ),
     ], 
       
     ),

    ###########################################################################################################################
    
     dbc.Row([
         dbc.Col([
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="BikesHourOfDay", config={"displayModeBar": False},
                        
                    ),
                    className="card",
                ),

            ],className="wrapper",
        ),
           ], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
          
        ),
     ],
       
     ),
 
############################################################################################################################
    
], fluid=True)



    
############################################################################################################################

@app.callback(
    Output('our_graph','figure'),
    [Input('bike-range-slider','value')]
)

#Set the input and out parameter for the callback
@app.callback(
    
    Output("BikesTotalOverTime", "figure"), 
    
    [      
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
# Set a function to perform on the input parameters provided above that come from the user setting drop down menu options
# on the web application
def update_charts_date(start_date, end_date):
#     
    mask = (
         (GroupedDateOutDF.dateout >= start_date)
       & (GroupedDateOutDF.dateout <= end_date)
    )
    #the filtered_data is a subset (based on the mask inputs above chosen from drop down menu by the user) 
    #of the total GroupedDF (which contains total number of bike pickups grouped by date)
    filtered_data_date = GroupedDateOutDF.loc[mask, :]    
    #fig below is setting the parameters of the line graph object from the filtered data set
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


@app.callback(
    
    Output("BikesDayOfWeek", "figure"), 
    
    [      
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
# Set a function to perform on the input parameters provided above that come from the user setting drop down menu options
# on the web application
def update_charts_day(start_date, end_date):
#     
    maskDay = (
         (GroupedDayOutDF.dateout >= start_date)
       & (GroupedDayOutDF.dateout <= end_date)
    )    
    
    filtered_data_day = GroupedDayOutDF.loc[maskDay, :]
    filtered_data_day = pd.DataFrame(filtered_data_day.groupby(['dayout','DayCode'])['NumberPickUps'].sum().reset_index())
    filtered_data_day= filtered_data_day.sort_values(by=['DayCode'])
    
    
    figDay = go.Figure(data=[go.Bar(
            x=filtered_data_day.dayout.unique(), y=filtered_data_day['NumberPickUps'],
            text=filtered_data_day['NumberPickUps'],
            textposition='auto',marker_color='yellow'            
        )])
    figDay.update_traces(hovertemplate='Bikes Hired: %{y} <br>Day of Week: %{x}'+'<extra></extra>')
    figDay.update_layout(title={
        'text': "Bike Hires by Day of the Week",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Day of the Week',
                   yaxis_title='Number of Hires')
    return figDay
    
    
@app.callback(
    
    Output("BikesHourOfDay", "figure"), 
    
    [      
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
# Set a function to perform on the input parameters provided above that come from the user setting drop down menu options
# on the web application
def update_charts_hour(start_date, end_date):
#     
    maskHour = (
         (GroupedHourOutDF.dateout >= start_date)
       & (GroupedHourOutDF.dateout <= end_date)
    )    

    #Workings for Hour Graph
    filtered_data_hour = GroupedHourOutDF.loc[maskHour, :]
    filtered_data_hour= pd.DataFrame(filtered_data_hour.groupby(['hourout'])['NumberPickUps'].sum().reset_index())
    
    figHour = go.Figure(data=[go.Bar(
            x=filtered_data_hour.hourout.unique(), y=filtered_data_hour['NumberPickUps'],
            text=filtered_data_hour['NumberPickUps'],
            textposition='auto',marker_color='lightsalmon'            
        )])
    figHour.update_traces(hovertemplate='Bikes Hired: %{y} <br>Hour of Day: %{x}'+'<extra></extra>')
    figHour.update_layout(title={
        'text': "Bike Hires by Hour of the Day",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Hour of the Day',
                   yaxis_title='Number of Hires')
    

    return figHour


# if __name__ == "__main__": ####################################################################################################
#     app.run_server(debug=True)#####################################################################

#############################################################################################################################


# In[ ]:




