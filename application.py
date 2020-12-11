import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np

from datetime import datetime
from datetime import timedelta

from fbprophet import Prophet

import plotly.express as px
import plotly.graph_objects as go

#---------------------------------------------------------------------------------------------

app = dash.Dash(__name__)

#---------------------------------------------------------------------------------------------

def clean_data(trends):
    """Clean data to desired format
    Input:
        trends (dataframe): original Apple Mobility Trends report as a dataframe
    Output:
        trends (dataframe): hierarchical columns by 'country' and 'transportation type'
                            indexed are dates
        country_names (list): a list of all country names in the Trends report
    """
    # filter by country level data
    trends = trends[trends['geo_type'] == 'country/region']
    # drop unused columns and change column name
    trends = trends.drop(['geo_type', 'alternative_name', 'sub-region', 'country'], axis = 1)
    trends = trends.rename({'region': 'country'}, axis = 1)
    # get country names
    country_names = trends['country'].unique()
    # set hierarchical index
    trends.set_index(['country', 'transportation_type'], inplace = True)
    # get difference from baseline
    trends = trends - 100
    # transpose dataframe so indices are dates
    trends = trends.transpose()
    # change index to datetime format
    trends.index = pd.to_datetime(trends.index)
    
    return trends, country_names

def get_country_trend(trends_countries, country_names, country_name = 'United States'):
    """filter trends by user-defined country
    Input:
        trends (dataframe): hierarchical columns by 'country' and 'transportation type'
                            indexed are dates
        country_names (list): a list of all country names in the Trends report
        country_name (string): user defined country name
    Output:
        trends_country (dataframe): trends for user-specified country
                                    indexed by date
                                    columns are transportation type
    """
    # check if country exists
    # return corresponding data if yet
    if country_name in country_names:
        trends_country = trends_countries[country_name]
        
        return trends_country
    # return US data if not
    else:
        print('No Data available for ' + country_name + '.')
        trends_country = trends_countries['United States']
        
        return trends_country

def get_country_forecast(forecast_countries, country_names, country_name = 'United States'):
    """filter forecasted trends by user-defined country
    Input:
        trends (dataframe): hierarchical columns by 'country' and 'transportation type'
                            indexed are dates
        country_names (list): a list of all country names in the Trends report
        country_name (string): user defined country name
    Output:
        forecast_country (dataframe): forecasted trends for user-specified country
                                      indexed by date
                                      columns are transportation type
    """
    # check if country exists
    # return corresponding data if yet
    if country_name in country_names:
        forecast_country = forecast_countries[country_name]
        
        return forecast_country
    # return US data if not
    else:
        print('No Data available for ' + country_name + '.')
        forecast_country = forecast_countries['United States']
        
        return forecast_country

def add_trend(country, trend, forecast, include_forecast, start_date, end_date):
    """creates a line plot and adds historical and forecasted trend based on country
    Input:
        country (string): country name
        trend (dataframe): historical trends for all countries
                           hierarchical columns by 'country' and 'transportation type'
                           indexed are dates
        forecast (dataframe): forecasted trends for all countries
                              hierarchical columns by 'country' and 'transportation type'
                              indexed are dates
        include_forecast (boolean): whether or not to include forecasted trends
        start_date (datetime): trend start date in %Y-%m-%d, e.g datetime(2020, 1, 14, 0, 0)
        end_date (datetime): trend end date in %Y-%m-%d, e.g datetime(2021, 2, 2, 0, 0)
    Output 
        fig (plotly express figure): line plot
    """
    # define line colors for 3 transportation types
    line_color = np.array(['#636EFA', '#EF553B', '#00CC96'])
    # get historical and forecasted trends for a country
    country_trend = get_country_trend(trend, country_names, country)
    country_forecast = get_country_forecast(forecast, country_names, country)
    
    # create a line plot
    fig = px.line(template = 'plotly_dark')
    # there are 4 scenarios in total:
    # 1 - while include_forecast is ON, dates are picked from historical timeline
    # 2 - while include_forecast is ON, dates are picked from forecasted timeline
    # 3 - while include_forecast is ON, dates span both historical and forecasted timeline
    # 4 - while include_forecast is OFF, dates could only be picked from historical timeline
    
    # figure response for the first 3 scenarios where include_forecast is ON
    if include_forecast:
        # scenario 1, datepicker end date in historical timeline
        if end_date in country_trend.index:
            # fitler data based on selected date
            filtered_trend = country_trend.loc[start_date:end_date, :]
            # add trends
            for idx, transportation in enumerate(filtered_trend.columns):
                fig.add_scatter(x = filtered_trend.index, 
                                y = filtered_trend[transportation],
                                line = dict(color = line_color[idx]),
                                name = transportation)
                pass
            pass
        # scenario 2, datepicker start date in forecasted timeline
        elif start_date in country_forecast.index:
            # fitler data based on selected date
            filtered_forecast = country_forecast.loc[start_date:end_date, :]
            # add trends
            for idx, transportation in enumerate(filtered_forecast.columns):
                fig.add_scatter(x = filtered_forecast.index, 
                                y = filtered_forecast[transportation],
                                line = dict(color = line_color[idx]),
                                name = transportation)
                pass
            pass
        # scenario 3, datepicker start date in historical timeline
        # datepicker end date in forecasted timeline
        else:
            # fitler data based on selected date
            filtered_trend = country_trend.loc[start_date:, :]
            filtered_forecast = country_forecast.loc[:end_date, :]
            # add trends for both historical data and forecasted data
            for idx, transportation in enumerate(filtered_trend.columns):
                fig.add_scatter(x = filtered_trend.index, 
                                y = filtered_trend[transportation],
                                line = dict(color = line_color[idx]),
                                name = transportation)
                fig.add_scatter(x = filtered_forecast.index, 
                                y = filtered_forecast[transportation],
                                line = dict(color = line_color[idx],
                                            dash='dash'),
                                showlegend = False)
                pass
            pass
        pass
    # figure response for the 4th scenario where include_forecast is OFF
    else:
        # fitler data based on selected date
        filtered_trend = country_trend.loc[start_date:end_date, :]
        # add trends
        for idx, transportation in enumerate(filtered_trend.columns):
            fig.add_scatter(x = filtered_trend.index, 
                            y = filtered_trend[transportation],
                            line = dict(color = line_color[idx]),
                            name = transportation)
            pass
        pass
        
    return fig

#---------------------------------------------------------------------------------------------

# read in the historical trend data and forecasted trend data
trend_data = pd.read_csv('./data/applemobilitytrends-2020-12-09.csv',
                         low_memory = False)
trends_countries, country_names = clean_data(trend_data)
forecast_countries = pd.read_csv('./data/forecasted_trends.csv', 
                                 parse_dates = True,
                                 header = [0,1], 
                                 index_col = 0)
# convert index to string for both historical and forecasted data
trends_countries_index = [str(date)[:10] for date in trends_countries.index]
trends_countries.index = trends_countries_index
forecast_countries_index = [str(date)[:10] for date in forecast_countries.index]
forecast_countries.index = forecast_countries_index

#---------------------------------------------------------------------------------------------

# define most recent trend by taking the mean of transportation types
most_recent_trends = [trends_countries[c].iloc[-1, :].mean().round(2) for c in country_names]
# use reversed color scale for map
color_scale = list(reversed(px.colors.sequential.Oryel))
# create a choropleth geo map
fig_map = px.choropleth(locations = country_names,
                        locationmode = "country names",
                        color = most_recent_trends,
                        hover_name = country_names,
                        color_continuous_scale = color_scale,
                        projection = "natural earth",
                        template = 'plotly_dark',
                        height = 500,
                       )
# update choropleth map specs
geo = dict(projection_type = "natural earth",
           countrycolor = "RebeccaPurple", landcolor = 'silver',
           showocean = True, oceancolor = "rgb(136,204,238)", lakecolor = "rgb(136,204,238)",
           showland = True
          )
fig_map.update_geos(geo)
fig_map.update_layout(margin={"r":20,"t":20,"l":20,"b":20})

#---------------------------------------------------------------------------------------------

available_trends = ['No', 'Yes']

# define dashboard layout
app.layout = html.Div([
    html.Div(style={'backgroundColor': '#222A2A'}, children = [
        html.H1('Apple Mobility Trend Report',
                style = {'font-size': '80px',
                         'width':'35%', 
                         'display': 'inline-block',
                         'vertical-align': 'middle'}),
        dcc.Graph(id = 'world_map',
                  figure = fig_map,
                  hoverData = {'points': [{'hovertext': 'United States'}]},
                  style = {'width':'65%',
                           'display': 'inline-block',
                           'vertical-align': 'middle'})
    ]),
    
    html.Div(style={'backgroundColor': 'rgb(136,204,0)'}, children = [
        html.Div('Include a 30-Day Forecast: ',
                 style = {'font-size': '20px',
                          'textAlign': 'right',
                          'width':'30%', 
                          'display': 'inline-block'}),
        dcc.RadioItems(id = 'include_forecast',
                       options = [{'label': i, 'value': i} for i in available_trends],
                       value = 'No',
                       style = {'font-size': '20px',
                                'textAlign': 'center',
                                'width':'10%',
                                'display': 'inline-block'}),
        dcc.DatePickerRange(id = 'select_date',
                            clearable = True,
                            number_of_months_shown = 2,
                            minimum_nights = 1,
                            start_date = trends_countries.index[0],
                            end_date = trends_countries.index[-1],
                            min_date_allowed = trends_countries.index[0],
                            display_format = 'Y-M-D',
                            style = {'align': 'center',
                                     'display': 'inline-block'})
    ]),
    
    dcc.Graph(id = 'trend')
])

#---------------------------------------------------------------------------------------------

# callback for updating datepicker component based on include_forecast radioitem
@app.callback(
    [Output(component_id = 'select_date', component_property = 'max_date_allowed'),
     Output(component_id = 'select_date', component_property = 'end_date'),
     Output(component_id = 'select_date', component_property = 'start_date')],
    Input(component_id = 'include_forecast', component_property = 'value')
)
def update_datepicker_range(radioitem_value):
    # convert include forecast selection to boolean
    include_forecast = True if radioitem_value == 'Yes' else False
    # define a 1 day deltatime object
    delta = timedelta(days=1)
    # update maxmium allowed date on datepicker based on include_forecast
    if include_forecast == True:
        # fix 1-day-short bug with the max_date_allowed property by adding 1 day
        max_date = datetime.strptime(forecast_countries.index[-1], '%Y-%m-%d')
        max_date = (max_date + delta).strftime('%Y-%m-%d')
        
        return max_date, forecast_countries.index[-1], trends_countries.index[0]
    else:
        # fix 1-day-short bug with  the max_date_allowed property by adding 1 day
        max_date = datetime.strptime(trends_countries.index[-1], '%Y-%m-%d')
        max_date = (max_date + delta).strftime('%Y-%m-%d')
        
        return max_date, trends_countries.index[-1], trends_countries.index[0]

# callback for updating graph component based on selected country on map, 
# include_forecast radioitem, and date range on datepicker 
@app.callback(
    Output(component_id = 'trend', component_property = 'figure'),
    [Input(component_id = 'world_map', component_property = 'hoverData'),
     Input(component_id = 'include_forecast', component_property = 'value'),
     Input(component_id = 'select_date', component_property = 'start_date'),
     Input(component_id = 'select_date', component_property = 'end_date')]
)
def update_trend(map_value, radioitem_value, datepicker_start, datepicker_end):
    # get country name from hoverData
    country = map_value['points'][0]['hovertext']
    # convert include forecast selection to boolean
    include_forecast = True if radioitem_value == 'Yes' else False
    # rename input variables
    start_time = datepicker_start
    end_time = datepicker_end
    
    return add_trend(country, trends_countries, forecast_countries, 
                     include_forecast, start_time, end_time)

if __name__ == '__main__':
    app.run_server(debug = True)