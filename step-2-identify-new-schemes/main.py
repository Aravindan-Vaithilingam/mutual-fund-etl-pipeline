import json
from datetime import datetime
from io import StringIO

import requests
import pandas as pd
import boto3
import os
import time
import logging
from athena_helper import execute_query
s3_client = boto3.client('s3')
BUCKET_NAME = os.getenv('BUCKET_NAME')
KEY_PREFIX = os.getenv('KEY_PREFIX')
athena_client = boto3.client('athena')
sqs_client = boto3.client('sqs')
queue_url = "https://sqs.ap-south-1.amazonaws.com/642484605414/mutual-fund-historical-data-crawl-schemes"

def lambda_handler(context, event):

    # Define the query
    query = ("""
    SELECT DISTINCT s.scheme_code, hds.crawled_historical_data FROM mutual_fund_db.schemes AS s LEFT JOIN
     mutual_fund_db.historical_data_status AS hds ON hds.scheme_code = s.scheme_code LIMIT 50;
     """)
    output_location = 's3://aravindan-dev-space/temp-athena-results/'

    result_set = execute_query(athena_client, query, output_location)
    for row in result_set:
        print(row)
        scheme_code_data = row['Data'][0]['VarCharValue']
        scheme_historical_data_flag = True if row['Data'][1].get('VarCharValue', None) else False
        if scheme_code_data != 'scheme_code':
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(
                    {"scheme_code": scheme_code_data, "crawl_historical": not scheme_historical_data_flag}), )

            print(response)

    # Define the output location in S3

    #
    # # Start the query execution
    # response = athena_client.start_query_execution(
    #     QueryString=query,
    #     ResultConfiguration={
    #         'OutputLocation': output_location,
    #     }
    # )
    #
    # # Get the query execution ID
    # query_execution_id = response['QueryExecutionId']
    #
    # # Wait for the query to complete
    # while True:
    #     response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
    #     status = response['QueryExecution']['Status']['State']
    #     if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
    #         break
    #     time.sleep(5)
    #
    # # Check if the query succeeded
    # if status == 'SUCCEEDED':
    #     # Fetch the results
    #     result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id)
    #     for row in result_response['ResultSet']['Rows']:
    #         print(row)
    #         scheme_code_data = row['Data'][0]['VarCharValue']
    #         scheme_historical_data_flag = True if row['Data'][1].get('VarCharValue', None) else False
    #         if scheme_code_data != 'scheme_code':
    #             response = sqs_client.send_message(
    #                 QueueUrl=queue_url,
    #                 MessageBody=json.dumps({"scheme_code": scheme_code_data, "crawl_historical": not scheme_historical_data_flag}),)
    #
    #             print(response)
    # else:
    #     print(f"Query failed with status: {status}")

if __name__ == '__main__':
    lambda_handler("", "")
