# Apple-Mobility-Trends-Webapp

This project aims to provide a dashboard web app for Apple's [COVID-19 Mobility Trend Report](https://covid19.apple.com/mobility)

The web app is now [online](http://applemobilitydash-env.eba-bywaivsk.us-east-1.elasticbeanstalk.com) on AWS

## Current Progress:
- Created functions to scrape and clean data (currently using country level data only)
- Visualized mobility trends for a single country
- Added dropdown menu, can now visualize mobility trends for a user selected country
- Added ability to forecast and visualize mobility trends
- Added ability to visualize and interact with a map
- Migrated everything to Plotly Dash
- Trend can now change dynamically by hovering the cursor over a country on the map
- Added a RadioItem to turn ON and OFF the forecast
- Added a Datapicker that allows user to select a time window, trends displayed change dynamically based on selected dates
- Migrated to AWS Cloud and deployed on Elastic Beanstalk (need to automate file update with AWS Lambda)

**Please see the demo gif below for current progress:**

![fig1](./resources/demo.gif)
