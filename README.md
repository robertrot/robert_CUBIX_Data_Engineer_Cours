CUBIX_Data_Engineer_Course
Short description
Analysing the Taxi trips at Chicago
README
Analyzing the project involving taxi trips in Chicago.

https://cubixedu.com/hu/data-engineer-alapkepzes/

The sources of the data:

 > Open-Meteo - Free weather API
 > Chicago Data Portal
 > Community areas in Chicago
I'm Robert Rotar and i've attended to a Data Engineering course at Cubix using AWS and Python and created the following project:

01_json_scraping.ipynb Reading CV file that contains spofity playlist and listing:
the 31th song
total playcount
lowest playcount song

Weather and Chicago Taxi Data Processing

02_web_scraping.ipynb -Getting Chicago City's community areas from wikipedia using BeautifulSoup. -Pairing the area names with it's id pair and storing it in a dictionary.

03_get_taxi_data.ipynb Using the https://data.cityofchicago.org/ page and API. Requesting a daily taxi data.

04_get_weather_data.ipynb Using the https://openweathermap.org/api page and it's API, requesting weather data for Chichago City. Used attributes :

datetime
temperature
windspeed
rain
precipitation
05_date_dimension.ipynb Preparing date columns for further usage like:
isweekend
dayofweek
06_chicago_data_to_mapping.ipynb Fetching Taxi Trip Data:
Calculating the current date minus two months. Formatting this date as YYYY-MM-DD. Constructs a URL to fetch taxi trip data from the City of Chicago's data portal for the specified date. Sending a GET request to the URL and retrieves the data in JSON format. Converting the JSON data into a Pandas DataFrame.

Drops columns with significant missing data (pickup_census_tract, dropoff_census_tract, pickup_centroid_location, dropoff_centroid_location). Renames columns for clarity. Converts date columns to datetime type and creates a helper column for weather data (datetime_for_weather).

Fetching Weather Data: Constructing a URL to fetch weather data from the Open-Meteo API for the same date. Sending a GET request to the URL with appropriate parameters and retrieves the weather data in JSON format. Filtering and organizes the weather data into a DataFrame.

Integrating Weather Data: Merging the taxi trip DataFrame with the weather DataFrame on the datetime column.

Data Transformation and Optimization:

Converting various columns to more memory-efficient data types to save memory. "trip_seconds":"int32", "trip_miles":"float", "pickup_community_area_id": "int8", "dropoff_community_area_id": "int8", "fare":"float", "tips":"float", "tolls":"float", "extras":"float", "trip_total":"float",

Displays updated DataFrame information and memory usage. Performs sanity checks on the data (e.g., checking for outliers).

Creating Master Tables: Extracting unique payment types and companies to create master tables. Generating ID columns for these tables and merges them back with the main taxi trip DataFrame, replacing text fields with IDs. Saving the master tables to CSV files.

Updating Master Tables: Showing how to add new payment types and companies to the master tables if they are not already present.

07_transform_load.ipynb Writing and testing functions locally. Preparing to migrate to the cloud and use these functions in AWS - Lambda. Imports and Settings:
Importign necessary libraries such as datetime, pandas, and requests. Configures pandas to display a maximum of 30 columns.

Taxi Trips Transformation:

The code retrieves taxi trip data from the Chicago Data Portal for a date two months ago. The data is cleaned by removing columns and rows with missing values, and renaming columns to clairfy to further usage. Adds a new column for weather data association.

Function for Taxi Trips Transformation: Defines a function taxi_trips_transformations that encapsulates the transformation steps for reusability.
