import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd

from fbprophet import Prophet

import plotly.express as px
import plotly.graph_objects as go

app = dash.Dash(__name__)

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

trend_data = pd.read_csv('./data/applemobilitytrends-2020-12-08.csv', 
                         parse_dates = True, 
                         low_memory = False)

trends_countries, country_names = clean_data(trend_data)
forecast_countries = pd.read_csv('./data/forecasted_trends.csv')


# define most recent trend by taking the mean of transportation types
most_recent_trends = [trends_countries[c].iloc[-1, :].mean().round(2) for c in country_names]
color_scale = list(reversed(px.colors.sequential.Oryel))
fig_map = px.choropleth(locations = country_names,
                    locationmode = "country names",
                    color = most_recent_trends,
                    hover_name = country_names,
                    color_continuous_scale = color_scale,
                    projection = "natural earth",
                    template = 'plotly_dark',
                    height = 500)
geo = dict(projection_type = "natural earth",
           countrycolor = "RebeccaPurple", landcolor = 'silver',
           showocean = True, oceancolor = "rgb(136,204,238)", lakecolor = "rgb(136,204,238)",
           showland = True)
fig_map.update_geos(geo)

app.layout = html.Div([
    dcc.Graph(id = 'world_map',
              figure = fig_map,
              hoverData = {'points': [{'hovertext': 'United States'}]}
             ),
    dcc.Graph(id = 'trend')
])

def add_trend(country, trend):
    line_color = ['#636EFA', '#EF553B', '#00CC96']
    country_trend = get_country_trend(trend, country_names, country)
    fig = px.line(country_trend,
                  template = 'plotly_dark')
    
    return fig

@app.callback(
    Output(component_id='trend', component_property='figure'),
    Input(component_id='world_map', component_property='hoverData')
)
def update_output_div(input_value):
    country = input_value['points'][0]['hovertext']
    return add_trend(country, trends_countries)

if __name__ == '__main__':
    app.run_server(debug=True)