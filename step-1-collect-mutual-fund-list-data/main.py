from datetime import datetime
from io import StringIO

import requests
import pandas as pd
import boto3
import os
import logging

from numpy.ma.core import compressed

s3_client = boto3.client('s3')
BUCKET_NAME = os.getenv('BUCKET_NAME') or 'aravindan-dev-space'
KEY_PREFIX = os.getenv('KEY_PREFIX') or 'mutual-fund-data-pipeline/scheme_list_data'


def lambda_handler(context, event):
    resp = requests.get('https://api.mfapi.in/mf')
    if resp.status_code == 200:
        scheme_list_df = pd.DataFrame.from_records(resp.json())
        scheme_list_buffer = StringIO()
        scheme_list_df.to_csv(scheme_list_buffer, index=False)
        scheme_list_content = scheme_list_buffer.getvalue()
        today = datetime.now()
        key_name = KEY_PREFIX + '/mutual_fund_list.csv'
        s3_client.put_object(Bucket=BUCKET_NAME, Key=key_name, Body=scheme_list_content)
        return "{'Status': 'Success'}"
    else:
        logging.log('ERROR',"Got invalid HTTP response code")

    return "{'Status': 'Failed'}"
if __name__ == '__main__':
    lambda_handler("", "")