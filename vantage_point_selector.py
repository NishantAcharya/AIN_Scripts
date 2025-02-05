from geopy.geocoders import Nominatim
import numpy as np
import pandas as pd
from tqdm import tqdm
import ipaddress
import ast
import socket
import requests
from datetime import date
import json
import bz2
import sys
import math
from statistics import mean,mode,median
import os
from geopy.distance import geodesic

#Grabbing the file
def get_file():
    today = date.today()
    year = today.year
    month = today.month
    day = today.day-1
    if int(day) < 10:
        str_day = '0'+str(day)
    else:
        str_day = str(day)
    if int(month) < 10:
        str_month = '0'+str(month)
    else:
        str_month = str(month)
    
    filename = str(year)+str_month+str_day+'.json.bz2'

    url = 'https://ftp.ripe.net/ripe/atlas/probes/archive/'+str(year)+'/'+str_month+'/'+filename
    file_save = 'Probe_files/'+filename
    os.makedirs(os.path.dirname(file_save), exist_ok=True)
    response = requests.get(url)

    with open(file_save, 'wb') as f:
        f.write(response.content)
    
    zipfile = bz2.BZ2File(file_save)
    data = zipfile.read()
    newfilepath = file_save[:-4]

    with open(newfilepath, 'wb') as f:
        f.write(data)

    with open(newfilepath, 'r') as f:
        data = json.load(f)

    return data['objects']

def main(lib_geoloc):
    data = get_file()
    close_group = {}
    far_group = {}
    mid_group = {}
    close_max = math.inf
    far_min = -1

    country_codes = set()
    for probe in tqdm(data):
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']),str(probe['longitude'])
        id = probe['id']

        distance = geodesic(lib_geoloc, lat_long).km
        if distance < close_max:
            curr_keys = list(close_group.keys())
            curr_keys.append(distance)
            close_max = max(curr_keys)
            close_group[distance] = id

            #The 4 here is for a max of 3 items in the group
            if len(close_group.keys()) >= 11:
                close_group.pop(close_max)
        
        if distance > far_min:
            curr_keys = list(far_group.keys())
            curr_keys.append(distance)
            far_min = min(curr_keys)
            far_group[distance] = id

            #The 4 here is for a max of 3 items in the group
            if len(far_group.keys()) >= 11:
                far_group.pop(far_min)

        if distance > 2*close_max and distance < 0.5*far_min and len(mid_group.keys()) < 10:
            mid_group[distance] = id
        
    return close_group,far_group,mid_group

geoloc = ('48.474422','-122.323685')
library_name = 'Burlington Public Library, WA'

close_group,far_group,mid_group = main(geoloc)
print(f"Close Group: {close_group}")
print(f"Far Group: {far_group}")
print(f"Mid Group: {mid_group}")
data = {'Close':close_group,'Far':far_group,'Mid':mid_group}

#Saving the data
with open('JSON/grouped_probes.json', 'w') as f:
    json.dump(data, f, indent=4)