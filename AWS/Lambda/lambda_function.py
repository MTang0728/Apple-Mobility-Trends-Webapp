import boto3
import botocore
from io import StringIO

import pandas as pd
import numpy as np

import os
import urllib
import urllib3
from urllib.request import urlopen
import json
import requests

import logging

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)

#S3 BUCKET
REGION = "us-east-1"
BUCKET = "applemobilitytrends"

def get_apple_link():
    """Get link of Apple Mobility Trends report file
    Output:
        data_link (str): link of Apple Mobility Trends report file
        data_name (str): name of Apple Mobility Trends report file
    """
    # get link via API
    link = "https://covid19-static.cdn-apple.com/covid19-mobility-data/current/v3/index.json"
    with urlopen(link) as url:
        json_data = json.loads(url.read().decode())
        pass
    # get link components from json dictionary
    basePath = json_data["basePath"]
    csvPath = json_data["regions"]["en-us"]["csvPath"]
    # aggregate to produce file link
    file_link = ("https://covid19-static.cdn-apple.com" + basePath + csvPath)
    # get file name
    # file_name = file_link.rsplit('/', 1)[-1]
    file_name = 'applemobilitytrends.csv'

    return file_link, file_name

def write_s3(file_link, bucket, file_name):
    """Write S3 Bucket
    Input:
        file_link (string): url link to csv data
        bucket (string): S3 bucket name
        file_name (string): file name to be saved as in S3
    """

    # instantiate s3 resource
    s3=boto3.resource('s3')
    # instantiate poolmanager
    http=urllib3.PoolManager()
    # Provide URL
    urllib.request.urlopen(file_link)
    # save file to s3 bucket
    s3.meta.client.upload_fileobj(http.request('GET', file_link, preload_content=False), bucket, file_name)

    LOG.info(f"result of write to bucket: {bucket}")


def lambda_handler(event, context):
    """Entry Point for Lambda"""

    data_link, data_name = get_apple_link()

    LOG.info(f"SURVEYJOB LAMBDA, event {event}, context {context}")

    # Write result to S3
    write_s3(file_link=data_link, bucket=BUCKET, file_name=data_name)
