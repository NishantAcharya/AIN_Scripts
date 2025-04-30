from ripe.atlas.cousteau import (
  Ping,
  Traceroute,
    AtlasSource,
    AtlasResultsRequest,
    AtlasCreateRequest,
    AtlasStopRequest,
    Measurement
)
import pandas as pd
import numpy as np
import ast
from tqdm import tqdm
from random import sample
from datetime import datetime,timedelta,timezone
from ipaddress import ip_address,ip_network,ip_interface
import time
import json
import threading
import math
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import random
import json
import csv
import os
from datetime import date
import socket
import geoip2.database
import requests
import sys
import ipaddress

def stop__measurement(msm_id,secure_key):
    split_key = secure_key.split('-')
    key = '-'.join(split_key[1:-1])
    atlas_request = AtlasStopRequest(msm_id=msm_id, key=key)

    (is_success, response) = atlas_request.create()

    try:
        if is_success:
            print(f"Measurement {msm_id} stopped successfully.")
        else:
            print(f"Failed to stop measurement {msm_id}. Response: {response}")
    except Exception as e:
        print(f"An error occurred while stopping measurement {msm_id}: {e} -- Please check Response {response}")

secure_key = '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'
start_ip = 99349373
end_ip = 99350661

for i in range(start_ip, end_ip):
    stop__measurement(i,secure_key)
    time.sleep(1)