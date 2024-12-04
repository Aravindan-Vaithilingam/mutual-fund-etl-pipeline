import json
from datetime import datetime, date
from fileinput import filename
from io import StringIO

import requests
import pandas as pd
import boto3
import os
import time
import logging

s3_client = boto3.client('s3')
BUCKET_NAME = os.getenv('BUCKET_NAME') or 'aravindan-dev-space'
KEY_PREFIX = os.getenv('KEY_PREFIX') or 'mutual-fund-data-pipeline/nav_history_raw/to_processed'
athena_client = boto3.client('athena')
sqs_client = boto3.client('sqs')
queue_url = os.getenv('QUEUE_URL') or "https://sqs.ap-south-1.amazonaws.com/642484605414/mutual-fund-historical-data-crawl-schemes"
nav_history_api = 'https://api.mfapi.in/mf/{}'
nav_live_api = 'https://api.mfapi.in/mf/{}/latest'

def crawl_mutual_fund_data(message):
    try:
        if message.get('crawl_historical') == True:
            response = requests.get(nav_history_api.format(
                message.get('scheme_code')))
            if response.status_code == 200:
                return response.json(), "success"
        else:
            response = requests.get(nav_live_api.format(
                message.get('scheme_code')))
            if response.status_code == 200:
                return response.json(), "success"
    except Exception as e:
        logging.error(e, exc_info=True)
    return [], 'failed'

def lambda_handler(context, event):


    response = sqs_client.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,  # Adjust as needed
        VisibilityTimeout= 600
    )
    if 'Messages' in response:
        print(len(response['Messages']))
        for message in response['Messages']:
            print(f"Message Body: {message['Body']}")
            print(f"Receipt Handle: {message['ReceiptHandle']}")
            message_body = json.loads(message['Body'])
            mutual_fund_data, status = crawl_mutual_fund_data(message_body)
            print(mutual_fund_data, status)
            if message_body.get('crawl_historical') == True:
                filename = f'{message_body.get("scheme_code")}.json'
            else:
                filename = f'{message_body.get("scheme_code")}_{date.today().strftime("%Y-%m-%d")}.live.json'
            if status == 'success':
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=f'{KEY_PREFIX}/{filename}',
                    Body=json.dumps(mutual_fund_data)
                )

            # Delete the message from the queue
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            print('Message deleted')

if __name__ == '__main__':
    lambda_handler("", "")
