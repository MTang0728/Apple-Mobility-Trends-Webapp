import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np

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

def add_trend(country, trend, forecast, include_forecast):
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
    # loop through transportation types and add corresponding trend lines
    for idx, transportation in enumerate(country_trend.columns):
        # add historical trend line
        fig.add_scatter(x = country_trend.index, 
                        y = country_trend[transportation],
                        line = dict(color = line_color[idx]),
                        name = transportation)
        # add forecasted trend line if include_forecast is True
        if include_forecast:
            fig.add_scatter(x = country_forecast.index,
                            y = country_forecast[transportation],
                            line = dict(color = line_color[idx],
                                        dash='dash'),
                            showlegend = False)
            pass
        else:
            pass
    
    return fig

#---------------------------------------------------------------------------------------------

# read in the historical trend data and forecasted trend data
trend_data = pd.read_csv('./data/applemobilitytrends-2020-12-08.csv', 
                         parse_dates = True, 
                         low_memory = False)
trends_countries, country_names = clean_data(trend_data)
forecast_countries = pd.read_csv('./data/forecasted_trends.csv', header = [0,1], index_col = 0)

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
                    height = 500)
# update choropleth map specs
geo = dict(projection_type = "natural earth",
           countrycolor = "RebeccaPurple", landcolor = 'silver',
           showocean = True, oceancolor = "rgb(136,204,238)", lakecolor = "rgb(136,204,238)",
           showland = True
          )
fig_map.update_geos(geo)

#---------------------------------------------------------------------------------------------

available_trends = ['No', 'Yes']

# define dashboard layout
app.layout = html.Div([
    dcc.Graph(id = 'world_map',
              figure = fig_map,
              hoverData = {'points': [{'hovertext': 'United States'}]}
             ),
    html.Div([
        html.Div('Include a 30-Day Forecast: '),
        dcc.RadioItems(id = 'include_forecast',
                       options = [{'label': i, 'value': i} for i in available_trends],
                       value = 'No',
                       labelStyle = {'display': 'inline-block'}
                      ),
             ]),
    dcc.Graph(id = 'trend')
])

#---------------------------------------------------------------------------------------------

@app.callback(
    Output(component_id = 'trend', component_property = 'figure'),
    [Input(component_id = 'world_map', component_property = 'hoverData'),
     Input(component_id = 'include_forecast', component_property = 'value')]
)
def update_output_div(input_map_value, input_radioitem_value):
    # get country name from hoverData
    country = input_map_value['points'][0]['hovertext']
    # convert include forecast selection to boolean
    include_forecast = True if input_radioitem_value == 'Yes' else False
    
    return add_trend(country, trends_countries, forecast_countries, include_forecast)

if __name__ == '__main__':
    app.run_server(debug = True)