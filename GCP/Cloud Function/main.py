import os
from google.cloud import storage

import pandas as pd
import numpy as np

import urllib
from urllib.request import urlopen
import json
import requests

bucket_name = os.environ['BUCKET']
trend_file_name = os.environ['TREND_FILE_NAME']

trend_cf_path = '/tmp/{}'.format(trend_file_name)

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
    file_name = file_link.rsplit('/', 1)[-1]

    return file_link, file_name


def save_file(event, context):
    """entry point to cloud function
    """
    # instantiate storage objects
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    # save trends data to a temporary local path
    data_link, _ = get_apple_link()
    urllib.request.urlretrieve(data_link, trend_cf_path)
    # save file to cloud storage
    trend_blob = storage.Blob(trend_file_name, bucket)
    trend_blob.upload_from_filename(trend_cf_path)

    print('this was triggered by messageId {} published at {}'.format(context.event_id, context.timestamp))
