from io import StringIO
import json

import boto3
import pandas as pd

def taxi_trips_transformations(taxi_trips: pd.DataFrame) -> pd.DataFrame:
    """ Perform transformation with the taxi data.
    
    Parameters
    ----------
    taxi_trips : pd.DataFrame
        The DataFrame holding the daily taxi trips

    Returns   
    -------   
    pd.DataFrame
       The cleaned, transformed DataFrame holding the daily taxi trips.     
    """

    if not isinstance(taxi_trips, pd.DataFrame):
        raise TypeError('taxi_trips is not a valid pandas DataFrame.')

    taxi_trips.drop(['pickup_census_tract', 'dropoff_census_tract',
                     'pickup_centroid_location', 'dropoff_centroid_location'], axis=1, inplace=True)
    #taxi_trips.drop(['pickup_centroid_location', 'dropoff_centroid_location'], axis=1, inplace=True)

    taxi_trips.dropna(inplace=True)

    taxi_trips.rename(columns={'pickup_community_area':'pickup_community_area_id',
                            'dropoff_community_area': 'dropoff_community_area_id'}, inplace=True)

    taxi_trips['datetime_for_weather'] = pd.to_datetime(taxi_trips['trip_start_timestamp']).dt.floor('h')

    return taxi_trips

def update_taxi_trips_with_master_data(taxi_trips: pd.DataFrame, payment_type_master: pd.DataFrame, company_master: pd.DataFrame) -> pd.DataFrame:
    """Update the taxi_trips DataFrame with the company_master and payment_type_master ids, and delete the string column.

    Parameters
    ----------
    taxi_trips : pd.DataFrame
        The DataFrame with the daily taxi trips.
    payment_type_master : pd.DataFrame
        Tha payment type master table.
    company_master : pd.DataFrame
        The company master table.

    Returns
    -------        
    pd.DataFrame
        Tha taxi_trips data, with only paymant_type id and company_id, without company on payment_type values.
    """

    taxi_trips_id = taxi_trips.merge(payment_type_master, on='payment_type')

    taxi_trips_id = taxi_trips_id.merge(company_master, on='company')

    taxi_trips_id.drop(['payment_type', 'company'], axis = 1, inplace = True) 

    return taxi_trips_id

def update_master(taxi_trips: pd.DataFrame, master: pd.DataFrame, id_column: str, values_column: str) -> pd.DataFrame:
    """ Extend the master DataFrame with new values if there are any.
    
    Parameters
    ----------
    taxi_trips : pd.DataFrame
        Dataframe holding the daily taxi trips.
    master : pd.DataFrame   
        DataFrame holding the master data.
    id_column: str
        The id_column of the master DataFrame.
    values_column: str
        Name of the column in master_df containing the values.

    Returns   
    -------   
    pd.DataFrame
       The updated master data, if new values are in the taxi data, they will be loaded to it.    
    """
    
    max_id = master[id_column].max()

    new_values_list = [value for value in taxi_trips[values_column].values if value not in master[values_column].values]
    new_values_df = pd.DataFrame({
        id_column: range(max_id + 1, max_id + len(new_values_list) + 1),
        values_column: new_values_list
    })

    updated_master = pd.concat([master, new_values_df], ignore_index=True)

    return updated_master    
    
    
def transform_weather_data(weather_data: json) -> pd.DataFrame:
    """Make transformations on the daily weather API response.

    Parameters
    ----------
    weather_data : JSON
        The daily weather_data from the Open Meteo API

    Returns
    -------
    pd.DataFrame
        A DataFrame represontation of the data.
    """
    weather_data_filtered = {
            'datetime': weather_data['hourly']['time'],
            'temperature': weather_data['hourly']['temperature_2m'],
            'wind_speed':weather_data['hourly']['wind_speed_10m'],
            'precipitation':weather_data['hourly']['precipitation'],
            'rain':weather_data['hourly']['rain'],
        }

    weather_df = pd.DataFrame(weather_data_filtered)

    weather_df['datetime'] = pd.to_datetime(weather_df['datetime'])
    
    return weather_df

def read_csv_from_s3(bucket: str, path: str, filename: str) -> pd.DataFrame:
    """
    Reads a CSV file from an S3 bucket and returns it as a pandas DataFrame.

    Parameters:
        bucket (str): The name of the S3 bucket.
        path (str): The path within the S3 bucket where the file is located.
        filename (str): The name of the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing the contents of the CSV file.

    """
    s3 = boto3.client('s3')
    
    full_path = f'{path}{filename}'
    
    object = s3.get_object(Bucket=bucket, Key=full_path)
    object = object['Body'].read().decode('utf-8')
    output_df = pd.read_csv(StringIO(object))
    
    return output_df

def upload_dataframe_to_s3(dataframe: pd.DataFrame, bucket: str, path: str):
    """
    Upload dataframe to the specified s3 path. 

    Parameters:
        dataframe: pd.DataFrame
            The dataframe to be uploaded.
        bucket (str): 
            Name of the s3 bucket where we want to store the files.
        path (str): str
            Path within the bucket to upload the file.
    Returns:
        None
    """
    
    s3 = boto3.client('s3')
    buffer = StringIO()
    dataframe.to_csv(buffer, index = False)
    df_content = buffer.getvalue()
    s3.put_object(Bucket = bucket, Key = path, Body = df_content)
    
    
def upload_master_data_to_s3(bucket: str, path: str, file_type: str, dataframe: pd.DataFrame):
    """
    Upload master data (paymant_type or company) to s3. Copies the previous version and creates the new one.

    Parameters
    ----------
    Bucket : str
        Name of the s3 bucket where we want to store the files.
    path : str
        Path within the bucket to upload the file.
    file_type : str
        Either 'company' or 'paymant_type'.
    dataframe : pd.DataFrame
        The dataframe to be uploaded.

    Returns
    -------        
        None
    """
    
    s3 = boto3.client('s3')
    
    master_file_path = f"{path}{file_type}_master.csv"
    previous_master_file_path = f"transformed_data/master_table_previous_version/{file_type}_master_previous_version.csv"
    
    s3.copy_object(
        Bucket = bucket,
        CopySource = {'Bucket': bucket, 'Key': master_file_path},
        Key = previous_master_file_path
    )
        
    
    upload_dataframe_to_s3(bucket = bucket, dataframe = dataframe, path = master_file_path)

def upload_and_move_file_on_s3(
        dataframe: pd.DataFrame, 
        datetime_col: str, 
        bucket: str, 
        file_type: str,
        filename: str,
        source_path: str,
        target_path_raw: str,
        target_path_transformed: str
    ):
        
    """
     Upload Dataframe to s3 and then moves a file from the base folder to another . 

    Parameters
    ----------
    dataframe : pd.DataFrame
        The DataFrame to be uploaded.
    datetime_col : str, optional
        Datatime column name, which we derive the date for the filename.
    bucket : str
        Name of the s3 bucket.
    file_type : str
        "weather" or "taxi".
    filename : str
        Name of the file to be uploaded or moved.
    source_path : str
        Source path within the bucket.
    target_path_raw : str
        Target path within the bucket where the raw data would go.
    target_path_transformed : str
        Target path within the bucket where the transformed data would go.
       
    Returns
    -------        
        None    
    """
    
    s3 = boto3.client('s3')
    
    formatted_date = dataframe[datetime_col].loc[0].strftime("%Y-%m-%d")
    new_path_with_filename = f"{target_path_transformed}{file_type}_{formatted_date}.csv"
        
    upload_dataframe_to_s3(bucket = bucket, dataframe = dataframe, path = new_path_with_filename)
        
        
    s3.copy_object(
        Bucket = bucket,
        CopySource = {'Bucket': bucket, 'Key':f"{source_path}{filename}"},
        Key = f"{target_path_raw}{filename}"
    )
        
    s3.delete_object(Bucket = bucket, Key = f"{source_path}{filename}")

#    
#
#  MAIN FUNKTION
#
#

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    bucket = 'cubix-chicago-taxi-rr'
    
    raw_weather_folder = 'raw_data/to_processed/weather_data/'
    raw_taxi_trip_folder ='raw_data/to_processed/taxi_data/'
    
    target_taxi_trips_folder = 'raw_data/processed/taxi_data/'
    target_weather_folder = 'raw_data/processed/weather_data/'
    
    transformed_taxi_trips_folder = 'transformed_data/taxi_trips/'
    transformed_weather_folder = 'transformed_data/weather/'
    
    test = s3.list_objects(Bucket=bucket, Prefix=raw_weather_folder)['Contents']
    payment_type_master_folder = 'transformed_data/payment_type/'
    company_master_folder = 'transformed_data/company/'
    
    payment_type_master_file_name = 'payment_type_master.csv'
    company_master_file_name = 'company_master.csv'
    
    
    payment_type_master = read_csv_from_s3(bucket = bucket, path = payment_type_master_folder, filename = payment_type_master_file_name)
    company_master = read_csv_from_s3(bucket = bucket, path = company_master_folder, filename = company_master_file_name)
    

    # TAXI DATA TRANSFORMATION AND LOADING
    for file in s3.list_objects(Bucket=bucket, Prefix=raw_taxi_trip_folder)['Contents']:
        taxi_trip_key = file ['Key']
    
        if taxi_trip_key.split("/")[-1].strip() !='':
            if taxi_trip_key.split('.')[1] == 'json':
                
                filename = taxi_trip_key.split("/")[-1]
                
                response = s3.get_object(Bucket=bucket, Key=taxi_trip_key)
                content = response['Body']
                taxi_trips_data_json = json.loads(content.read())
                        
                taxi_trips_data_raw =pd.DataFrame(taxi_trips_data_json)
                taxi_trips_transformed = taxi_trips_transformations(taxi_trips_data_raw)  
                    
                    
                company_master_update = update_master(taxi_trips_transformed, company_master, 'company_id','company')
                payment_type_master_update = update_master(taxi_trips_transformed, payment_type_master, 'payment_type_id','payment_type')
                    
                    
                taxi_trips = update_taxi_trips_with_master_data(taxi_trips_transformed,payment_type_master_update,company_master_update)
                    
                upload_and_move_file_on_s3(
                        dataframe = taxi_trips, 
                        datetime_col = 'datetime_for_weather', 
                        bucket = bucket, 
                        file_type = 'taxi',
                        filename = filename,
                        source_path = raw_taxi_trip_folder,
                        target_path_raw = raw_taxi_trip_folder,
                        target_path_transformed = transformed_taxi_trips_folder
                    )
                        
                print('taxi_trips is uploaded and moved.')
                    
                
                upload_master_data_to_s3(bucket = bucket, path = payment_type_master_folder, file_type = 'payment_type', dataframe = payment_type_master_update)
                print('payment_type_master has been updated')
                    
                upload_master_data_to_s3(bucket = bucket, path = company_master_folder, file_type = 'company', dataframe = company_master_update)
                print('company_master has been updated')
                    
                    #   upload taxi_trips to s3 funktion
    
    # WEATHER DATA TRANSFORMATION AND LOADING
    for file in s3.list_objects(Bucket=bucket, Prefix=raw_weather_folder)['Contents']:
        weather_key = file['Key']
        
        if weather_key.split("/")[-1].strip() !='':
            if weather_key.split('.')[1] == 'json':
                
                filename = weather_key.split('/')[-1]
                
                response = s3.get_object(Bucket=bucket, Key=weather_key)
                content = response['Body']
                weather_data_json = json.loads(content.read())
                   
                   
                weather_data = transform_weather_data(weather_data_json)
                    
                upload_and_move_file_on_s3(
                    dataframe=weather_data, 
                    datetime_col ='datetime', 
                    bucket=bucket, 
                    file_type='weather', 
                    filename=filename, 
                    source_path=raw_weather_folder, 
                    target_path_raw=target_weather_folder, 
                    target_path_transformed=transformed_weather_folder
                )
                   
                print('weather is uploaded and moved')
                    
                            #  upload to s3 funktion 