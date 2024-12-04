import json
import time
from datetime import datetime
from io import StringIO

import requests
import pandas as pd
import boto3
import os
import logging
from datetime import date
from athena_helper import execute_query
from numpy.ma.core import compressed
# Chang An
s3_client = boto3.client('s3')
athena_client = boto3.client('athena')
BUCKET_NAME = os.getenv('BUCKET_NAME') or 'aravindan-dev-space'
KEY_PREFIX = os.getenv('KEY_PREFIX') or 'mutual-fund-data-pipeline/nav_history_raw/to_processed'
BACKUP_KEY_PREFIX = os.getenv('BACKUP_KEY_PREFIX') or 'mutual-fund-data-pipeline/nav_history_raw/processed'

METADATA_OUTPUT_KEY_PREFIX =  os.getenv('METADATA_OUTPUT_KEY_PREFIX') or 'mutual-fund-data-pipeline/mutual-fund-meta-data'
NAV_OUTPUT_KEY_PREFIX =  os.getenv('NAV_OUTPUT_KEY_PREFIX') or 'mutual-fund-data-pipeline/mutual-fund-nav-history'
QUERY = os.getenv('QUERY') or """
INSERT INTO mutual_fund_db.historical_data_status
VALUES ({0},{1});
"""
OUTPUT_LOCATION = os.getenv('OUTPUT_LOCATION') or 's3://aravindan-dev-space/temp-athena-results/'

# def extract_meta_data():
#     pass
# def extract_nav_history():
#     pass

def lambda_handler(context, event):
    try:
        for file in s3_client.list_objects(Bucket = BUCKET_NAME, Prefix = KEY_PREFIX)['Contents']:
            file_key = file['Key']
            if file_key.split('.')[-1] == 'json':

                response = s3_client.get_object(Bucket= BUCKET_NAME, Key=file_key)
                content = response['Body']
                jsonObject = json.loads(content.read())

                print(jsonObject.get('meta'))
                nav_history_df = pd.DataFrame.from_records(jsonObject.get('data'))
                scheme_meta_data_df = pd.DataFrame([jsonObject.get('meta')])
                # scheme_code = file_key.split('/')[-1].split('.')[-2]
                scheme_code = scheme_meta_data_df['scheme_code'][0]

                nav_history_df['scheme_code'] = scheme_code

                nav_history_df = nav_history_df[['scheme_code', 'date', 'nav']]
                nav_history_df.rename(columns={'date': 'nav_date'}, inplace=True)
                nav_history_df['nav_date'] = pd.to_datetime(nav_history_df['nav_date'], format='%d-%m-%Y').dt.strftime('%Y-%m-%d')

                # Create IO Buffer of NAV values
                nav_history_buffer = StringIO()
                nav_history_df.to_csv(nav_history_buffer, index=False)

                nav_history_content = nav_history_buffer.getvalue()


                nav_history_filename = f'/nav_history_{scheme_code}.csv'
                scheme_meta_data_filename =  f'/scheme_metadata_{scheme_code}.csv'

                # Only store the scheme's metadata when doing the historical crawling
                if file_key.split('.')[-2] == 'live':
                    scheme_code = file_key.split('/')[-1].split('_')[0]
                    nav_history_filename = f'/nav_history_{scheme_code}_{date.today().strftime("%Y-%m-%d")}.live.csv'
                else:
                    # Create IO Buffer for Scheme Metadata

                    scheme_meta_data_buffer = StringIO()
                    scheme_meta_data_df.to_csv(scheme_meta_data_buffer, index=False)
                    scheme_meta_data_content = scheme_meta_data_buffer.getvalue()

                    s3_client.put_object(Bucket=BUCKET_NAME, Key=METADATA_OUTPUT_KEY_PREFIX+ scheme_meta_data_filename , Body=scheme_meta_data_content)

                s3_client.put_object(Bucket=BUCKET_NAME, Key=NAV_OUTPUT_KEY_PREFIX + nav_history_filename , Body=nav_history_content)

                # Backup and delete the raw data
                copy_source = {
                    "Bucket": BUCKET_NAME,
                    "Key": file_key
                }
                s3_client.copy(copy_source, BUCKET_NAME, BACKUP_KEY_PREFIX +'/'+ file_key.split("/")[-1])
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_key)

                # Define the output location for query results
                print(QUERY.format( scheme_code, True))

                response = execute_query(athena_client, QUERY.format( scheme_code, True), OUTPUT_LOCATION)
                if response:
                    logging.info("Updated athena table")
                else:
                    logging.error("Error in query execution")

    except Exception as e:
        logging.error(e, exc_info=True)

            # print(jsonObject)
    return "{'Status': 'Failed'}"
if __name__ == '__main__':
    lambda_handler("", "")