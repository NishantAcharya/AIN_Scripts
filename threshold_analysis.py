from ripe.atlas.cousteau import (
  Ping,
  Traceroute,
    AtlasSource,
    AtlasResultsRequest,
    AtlasCreateRequest,
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

def get_file_names():
    json_folder = '/home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/JSON'
    files = []
    for filename in os.listdir(json_folder):
        if 'grouped_probes_' in filename:
            files.append(filename)
    return files

def create_pings_file(file,secure_key):
    split_key = secure_key.split('-')
    d_key = '-'.join(split_key[1:-1])
    with open(f'/home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/JSON/{file}', 'r') as f:
        data = json.load(f)
        close_probes = list(data['Close'].keys())
        metro_probes = list(data['Metro'].keys())

        close_ips = []
        for probe in close_probes:
            try:
                ip = data['Close'][probe][1]
                if ip is None:
                    ip = data['Close'][probe][2]
                if ip is None:
                    continue
                close_ips.append(ip)
            except:
                print(data['Close'][probe])
                raise Exception('Error')

        #Grabbing all sources for this ping -- metro to close
        probes = ','.join(metro_probes)
        source = AtlasSource(type='probes',value=probes, requested=len(metro_probes))


        #Pinging all close probes from metro probes for a day
        probes = ','.join(metro_probes)
        current_name = file.split('_')[2]
        start_time = datetime.now(timezone.utc)+timedelta(minutes=15)
        stop_time = start_time+timedelta(days=1)
        pings = []

        for ip in close_ips:
            ping = Ping(
                af=4,
                target=ip,
                description=f'Threshold Analysis Ping {current_name} to {ip}',
                resolve_on_probe=True,
                interval=3600,
                packets=3
            )
            pings.append(ping)
        
        atlas_request = AtlasCreateRequest(
            start_time=start_time,
            stop_time=stop_time,
            key=d_key,
            measurements=pings,
            sources=[source],
            is_oneoff=False
        )

        (is_success, response) = atlas_request.create()
        if not is_success:
            print(f'Failed to create pings for {file}')
            print(response)
            return
        
        #Calculating measurements per ip
        msm_id = int(response['measurements'][0])
        msms = [msm_id]
        for i in range(1,len(response['measurements'])):
            msms.append(int(response['measurements'][i]))

        #Calculating close probe measurements
        close_msms = []
        probes = ','.join(close_probes)
        source = AtlasSource(type='probes',value=probes, requested=len(close_probes))
        atlas_request = AtlasCreateRequest(
            start_time=start_time,
            stop_time=stop_time,
            key=d_key,
            measurements=pings,
            sources=[source],
            is_oneoff=False
        )

        (is_success, response) = atlas_request.create()
        if not is_success:
            print(f'Failed to create pings for {file}')
            print(response)
            return
        
        #Calculating measurements per ip
        msm_id = int(response['measurements'][0])
        close_msms.append(msm_id)
        for i in range(1,len(response['measurements'])):
            close_msms.append(int(response['measurements'][i]))
        
        #INCLUDES THE ORIGINAL PROBE WE ARE PINGING< REMOVE TO AVOID OUTLIERS
        return msms,close_msms

def main():
    #secure_key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv'
    secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'
    files = get_file_names()
    for file in files:
        print(f'Create Measurement for {file}')
        check = False
        with open('msms.txt','r') as f:
            lines = f.readlines()
            for line in lines:
                if file in line:
                    print(f'{file} already created')
                    check = True
                    break
        if check:
            continue
        msms,close_msms = create_pings_file(file,secure_key)

        #Saving to a text file
        with open('msms.txt','a') as f:
            f.write(f'{str(msms)}-{file}\n')
        with open('close_msms.txt','a') as f:
            f.write(f'{str(close_msms)}-{file}\n')

main()
