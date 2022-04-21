

# In[1]:


#Import Packages

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from pytz import timezone

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objs as go


from app import app
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

import pathlib
import joblib


# In[2]:


# Machine Learning Model

filePath= pathlib.Path(__file__).parent
MLModelPath = filePath.joinpath("../files").resolve()
filename = 'MLmodel.sav'
machineLearningModel = joblib.load(MLModelPath.joinpath(filename))


# In[3]:


#Construct URL to fetch JSON Data for weather forecast

API_Endpoint = "http://api.openweathermap.org/data/2.5/forecast?q="
city = "Pittsburgh"
country = ",US,"
personalKey = "&appid=" + "d59cc47ea1c5676186dd74622fa9dfe8"
metric = "&units=metric"

pittsburghForecast = API_Endpoint+city+country+personalKey+metric

# import requests
jsonDataForecast = requests.get(pittsburghForecast).json()

timeZone='America/New_York'


# In[4]:


#Set Local Time

now=datetime.now()
nowLocal = now.astimezone(timezone(timeZone))
localDateTime = datetime.strptime(nowLocal.strftime('%Y-%m-%d'), '%Y-%m-%d')

#Format for visualisations
nowLocalWords=nowLocal.strftime("%A %d %B %Y")
timeHHMM = nowLocal.strftime("%H:%M")


# In[5]:


# Creating empty lists to store JSON weather data

dateTime = [] # UTC
timeZone = [] # Seconds Difference from UTC
temperaturePrediction = []
windPrediction = []
rainPrediction = []


# In[6]:


timePeriod = 0

# Loop through and read in JSON weather forecast values
for periods in jsonDataForecast['list']:
    dateTime.append(jsonDataForecast['list'][timePeriod]['dt_txt']) 
    
    if jsonDataForecast['city']['timezone'] >0 :
        timeZone.append("+" + str((jsonDataForecast['city']['timezone'])/3600))
    else:
        timeZone.append((jsonDataForecast['city']['timezone'])/3600)
   
    temperaturePrediction.append(jsonDataForecast['list'][timePeriod]['main']['temp'])
    windPrediction.append(jsonDataForecast['list'][timePeriod]['wind']['speed']) 
    
    #rain data on present if rain forecast
    try:
        rainPrediction.append(jsonDataForecast['list'][timePeriod]['rain']['3h'])
    except KeyError:
        rainPrediction.append(0)
    
    timePeriod+=1


# In[7]:


# Put all lists together into a dataframe
pittsDF = pd.DataFrame()

pittsDF['DateTime'] = dateTime
pittsDF['TimeZone'] = timeZone
pittsDF['Temperature'] = temperaturePrediction
pittsDF['Wind'] = windPrediction
pittsDF['Rain'] = rainPrediction


# In[8]:


#Format columns
pittsDF['DateTime'] =  pd.to_datetime(pittsDF['DateTime'], format="%Y-%m-%d %H:%M:%S")
pittsDF['TimeZone']= pittsDF['TimeZone'].astype(int)


# In[9]:


#Convert DateTime field to local time, then dtop timezone column

pittsDF['DateTime']=pittsDF['DateTime']+pd.to_timedelta(pittsDF['TimeZone'],unit='h')
pittsDF.drop(['TimeZone'],axis=1, inplace=True)


# In[10]:


#Add further data fields required for machine learning model
pittsDF['DayOfWeek'] = pittsDF['DateTime'].dt.dayofweek
pittsDF['Month'] = pittsDF['DateTime'].dt.month
pittsDF['Hour'] = pittsDF['DateTime'].dt.hour


# In[11]:


#Map Data to codes
hourmap = {0:0, 1:0, 2:0, 3:3, 4:3, 5:3, 6:6, 7:6, 8:6, 9:9,10:9,11:9,12:12,13:12,14:12,
           15:15,16:15,17:15,18:18,19:18,20:18,21:21,22:21,23:21}
pittsDF['HourGroup'] = pittsDF['Hour'].map(hourmap)
pittsDF.drop(['Hour'],axis=1, inplace=True)

dayweek = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu',4:'Fri',5:'Sat',6:'Sun'}
pittsDF['DayOfWeek']= pittsDF['DayOfWeek'].map(dayweek)

monthmap = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',5:'May',6:'Jun',
            7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
pittsDF['Month']= pittsDF['Month'].map(monthmap)


# In[12]:


#Drop DateTime to a DataFrame for later
dateTimeList = pittsDF.DateTime
#dateTimeDF=dateTimeDF.to_frame().reset_index()
pittsDF = pittsDF.drop('DateTime',axis='columns')


# In[13]:


#One Hot Code for input to model
#Hour Group
pittsDF['Hour_0']=np.where(pittsDF['HourGroup']<3, 1, 0)
pittsDF['Hour_3']=np.where((pittsDF['HourGroup']>=3) & (pittsDF['HourGroup']<6), 1, 0)
pittsDF['Hour_6']=np.where((pittsDF['HourGroup']>=6) & (pittsDF['HourGroup']<9), 1, 0)
pittsDF['Hour_9']=np.where((pittsDF['HourGroup']>=9) & (pittsDF['HourGroup']<12), 1, 0)
pittsDF['Hour_12']=np.where((pittsDF['HourGroup']>=12) & (pittsDF['HourGroup']<15), 1, 0)
pittsDF['Hour_15']=np.where((pittsDF['HourGroup']>=15) & (pittsDF['HourGroup']<18), 1, 0)
pittsDF['Hour_18']=np.where((pittsDF['HourGroup']>=18) & (pittsDF['HourGroup']<21), 1, 0)
pittsDF.drop(['HourGroup'],axis=1, inplace=True)

pittsDF['Mon']=np.where(pittsDF['DayOfWeek']=='Mon', 1, 0)
pittsDF['Tue']=np.where(pittsDF['DayOfWeek']=='Tue', 1, 0)
pittsDF['Wed']=np.where(pittsDF['DayOfWeek']=='Wed', 1, 0)
pittsDF['Thu']=np.where(pittsDF['DayOfWeek']=='Thu', 1, 0)
pittsDF['Fri']=np.where(pittsDF['DayOfWeek']=='Fri', 1, 0)
pittsDF['Sat']=np.where(pittsDF['DayOfWeek']=='Sat', 1, 0)
pittsDF.drop(['DayOfWeek'],axis=1, inplace=True)

pittsDF['Jan']=np.where(pittsDF['Month']=='Jan', 1, 0)
pittsDF['Feb']=np.where(pittsDF['Month']=='Feb', 1, 0)
pittsDF['Mar']=np.where(pittsDF['Month']=='Mar', 1, 0)
pittsDF['Apr']=np.where(pittsDF['Month']=='Apr', 1, 0)
pittsDF['May']=np.where(pittsDF['Month']=='May', 1, 0)
pittsDF['Jun']=np.where(pittsDF['Month']=='Jun', 1, 0)
pittsDF['Jul']=np.where(pittsDF['Month']=='Jul', 1, 0)
pittsDF['Aug']=np.where(pittsDF['Month']=='Aug', 1, 0)
pittsDF['Sep']=np.where(pittsDF['Month']=='Sep', 1, 0)
pittsDF['Oct']=np.where(pittsDF['Month']=='Oct', 1, 0)
pittsDF['Nov']=np.where(pittsDF['Month']=='Nov', 1, 0)
pittsDF.drop(['Month'],axis=1, inplace=True)


# In[14]:


#Load DataFrame to Machine Learning Model

predictions = machineLearningModel.predict(pittsDF)


# In[15]:


#Develop the bar plot of predicted bike usage

figforecast = px.bar( x=dateTimeList, y=predictions)
figforecast.update_layout(title={
        'text': "Predicted Usage of Pittsburgh Bike Scheme Over the Next 5 Days",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
                   xaxis_title='Date',
                   yaxis_title='Number of Hires')


figforecast.show()


# In[16]:


# Workings for application page


menu_content = [
    dbc.CardHeader("Pittsburgh Healthy Ride Bike Scheme",style={'text-align':'center'}),
    dbc.CardBody(
        [
            html.H3("5 day Forecast usage of scheme",className="card-title"),
            html.H4("Beginning from now", className="card-title"),
            html.H4(f"{timeHHMM}"),
            html.H4(f"{nowLocalWords}"),
            html.H4(" "),
            html.H5("Please select to view other data"),
            html.Div([
            dbc.Button("Today's Data", color="primary", className="mr-1", href='/apps/gettoday'),
            dbc.Button("Historic Data", color="primary", className="mr-1", href='/apps/overall'),  
            dbc.Button("Station Data", color="primary", className="mr-1", href='/apps/stations'),
            ]
        ),
            
        ],style={'text-align':'center'}
    ),
]


# In[17]:


#Application layout page
   
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
       ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=3, lg=3, xl=3,          
       ),
       
   ], 
          
   ),
   
##########################################################################################################################   
   
dbc.Row([    
         dbc.Col([
       html.Div(
           children=[
               html.Div(
                   children=dcc.Graph(
                       id="PittsPrediction", config={"displayModeBar": False},
                       figure=figforecast                       
                   ),
                  
               ),
       
           ],
           
       ),    
], style={'display': 'block', 'align-items': 'center', 'justify-content': 'center'}, xs=12, sm=12, md=12, lg=12, xl=12,
),
    ], 
),
   
], fluid=True)


# if __name__ == "__main__": ####################################################################################################
#     app.run_server(debug=True)#####################################################################


