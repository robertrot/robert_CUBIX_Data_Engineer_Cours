from io import StringIO
import json
import boto3
import pandas as pd

def read_json_from_s3(bucket: str, path: str, filename: str) -> dict:
    """
    Reads a JSON file from an S3 bucket and returns it as a dictionary.

    Parameters:
        bucket : str
            The name of the S3 bucket.
        path : str
            The path within the S3 bucket where the file is located.
        filename : str
            The name of the JSON file.

    Returns:
        dict: Dictionary containing the contents of the JSON file.
    """
    s3 = boto3.client('s3')
    
    full_path = f'{path}/{filename}'
    
    obj = s3.get_object(Bucket=bucket, Key=full_path)
    content = obj['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    
    return json_data

# Parameters
bucket = 'cubix-chicago-taxi-rr'
raw_taxi_trip_folder = 'path/to_processed/taxi_data/'
raw_weather_folder = 'path/to_processed/weather_data/'

# File List
taxi_filenames = ['taxi_trip_1.json', 'taxi_trip_2.json']  # A taxi fájlok nevei
weather_filenames = ['weather_data_1.json', 'weather_data_2.json']  # Az időjárás fájlok nevei

# Taxi data Read
taxi_trips_data = []
for filename in taxi_filenames:
    taxi_data = read_json_from_s3(bucket=bucket, path=raw_taxi_trip_folder, filename=filename)
    taxi_trips_data.append(taxi_data)

# Weather data read
weather_data = []
for filename in weather_filenames:
    weather_data_item = read_json_from_s3(bucket=bucket, path=raw_weather_folder, filename=filename)
    weather_data.append(weather_data_item)

# Check
print("Taxi trips data:", taxi_trips_data)
print("Weather data:", weather_data)


