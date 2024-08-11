import json
import boto3

import requests
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta 
from typing import List, Dict

# 1. DONE - get T - 2 months taxi data
# 2. DONE - get T - 2 months weather data
# 3. DONE - upload to S3 (row_data /to processes / weather_data and row_data /to processes / taxi_data )
# 4. DONE - create functions - organise the code
# 5. creating a trigger

def get_taxi_data(formatted_datetime: str) -> Dict:
    '''
    Retrieves taxi_data for the given date.
    
    Parameters:
        formatted_datetime(str): The date in 'YYYY-MM-DD'format.
        
        
    Returns:
        Dict:  A dictionary contatining the taxi_data as a JSON.
    
    '''
    taxi_url = (
    f"https://data.cityofchicago.org/resource/wrvz-psew.json?"
    f"$where=trip_start_timestamp >= '{formatted_datetime}T00:00:00'"
    f"AND trip_start_timestamp <= '{formatted_datetime}T23:59:59'&$limit=30000"
    )
    
    
    headers  = {"X-App-Token": os.environ.get("CHICAGO_API_TOKEN")}
    
    response = requests.get(taxi_url, headers) 
    taxi_data = response.json()
    
    return taxi_data

def get_weather_data(formatted_datetime: str) -> Dict:
    '''
    Retrieves weather_data for the Open meteo API for a specific date and location.
    
    Parameters:
        formatted_datetime(str): The date in 'YYYY-MM-DD'format.
        
        
    Returns:
        Dict:  A dictionary contatining weather_data, including temperature at 2 meters, wind at 10 meters,
                rain, and precipitacion for the specified date and location.
    
    '''
    
    weather_url ='https://archive-api.open-meteo.com/v1/era5'
    
    params = {
        'latitude': 41.85,
        'longitude': -87.65,
        'start_date': formatted_datetime,
        'end_date': formatted_datetime,
        'hourly': 'temperature_2m,wind_speed_10m,precipitation,rain'
    }
    
    response = requests.get(weather_url, params = params)
    
    weather_data = response.json()
    
    return weather_data
    
    
def upload_to_s3(data: Dict, folder_name: str, filename: str) -> None:
    '''
    Upload data to an Amazon s3 bucket.
    
    Parameters:
        data (Dict): A dictionary containing the data to be uploaded, either taxi or weather data.
        folder_name (str): The name of the folder within the s3 bucket where the data will be stored.
        filename (str): The name of the fileto be created within the specified folder.
        
    Returns:
        None: This function dose not return anything.
    
    '''
   
    client = boto3.client('s3')
    client.put_object(
        Bucket = 'cubix-chicago-taxi-rr',
        Key = f'raw_data/to_processed/{folder_name}/{filename}',
        Body = json.dumps(data)
    )


def lambda_handler(event, context):
    current_datetime = datetime.now() - relativedelta(months=8)
    formatted_datetime = current_datetime.strftime("%Y-%m-%d")
    
    taxi_data_api_call = get_taxi_data(formatted_datetime)  
    weather_data_api_call = get_weather_data(formatted_datetime)
    
    taxi_filename = f'taxi_raw_{formatted_datetime}.json'
    weather_filename = f'weather_raw_{formatted_datetime}.json'
    
    upload_to_s3(data=taxi_data_api_call, filename = taxi_filename, folder_name = 'taxi_data')
    print('Taxi_data has been uploaded!')
    
    upload_to_s3(data=weather_data_api_call, filename = weather_filename, folder_name = 'weather_data')
    print('Weather data has been uploaded!')