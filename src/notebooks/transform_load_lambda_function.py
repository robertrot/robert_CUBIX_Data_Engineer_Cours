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
    
    full_path = f'{path}{filename}'
    
    object = s3.get_object(Bucket=bucket, Key=full_path)
    content = object['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    
    return json_data

# Kód használata

# s3 kliens 
s3 = boto3.client('s3')

# TAXI TRIP DATA
taxi_trips_data_json = read_json_from_s3(bucket=bucket, path=raw_taxi_trip_folder, filename=filename)

# WEATHER DATA
weather_data_json = read_json_from_s3(bucket=bucket, path=raw_weather_folder, filename=filename)



