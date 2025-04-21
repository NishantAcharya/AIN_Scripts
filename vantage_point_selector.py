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

#Check if the file exists
def file_exists():
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

    file_path = os.path.join('Probe_files', filename)
    return os.path.exists(file_path)

def load_file():
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

    filename = str(year)+str_month+str_day+'.json'
    file_save = 'Probe_files/'+filename

    with open(file_save, 'r') as f:
        data = json.load(f)

    return data['objects']


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

##TODO: Adjust this to get he max probe value into consideration
#Get the probe and their distances
def main(lib_geoloc):
    if not file_exists():
        data = get_file()
    else:
        data = load_file()

    ids = []
    values = []

    violating_probes_df = pd.read_csv('CSV/violating_probes_paper.csv')
    violating_probes = violating_probes_df['ProbeID'].tolist()

    #Get the distance to the lat long with one loop

    #Then select the closest probes
    temp_distance = []
    for probe in tqdm(data):
        if probe['id'] in violating_probes:
            continue
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']),str(probe['longitude'])
        id = probe['id']
        ip_v4 = probe['address_v4']
        ip_v6 = probe['address_v6']
        distance = geodesic(lib_geoloc, lat_long).miles
        ids.append(id)
        values.append((distance,lat_long,ip_v4,ip_v6))
        temp_distance.append(distance)

    #Find the closest 2th% distance from values
    temp_distance.sort()
    #Get the 2th percentile
    boundary_dist = np.percentile(temp_distance, 2)
    #counting the number of probes in the 2% group
    count = 0
    for i in range(len(temp_distance)):
        if temp_distance[i] > boundary_dist:
            break
        count += 1

    if count < 5:
        #Get the closest 5 probes
        boundary_dist = temp_distance[4]
    
    #Get the closest probes
    close_group = {}
    for i in range(len(values)):
        if values[i][0] <= boundary_dist:
            id = ids[i]
            distance = values[i][0]
            lat_long = values[i][1]
            ip_v4 = values[i][2]
            ip_v6 = values[i][3]
            close_group[id] = (distance,lat_long,ip_v4,ip_v6)

    return close_group

library_name = str(sys.argv[1])
lat = sys.argv[2]
lon = sys.argv[3]
geoloc = (str(lat), str(lon))

print(f"Processing {library_name}")

close_group = main(geoloc)
print(f"Close Group: {len(close_group)}")
data = {'Close':close_group}

#Use this to create a trace vantage selector from an area close to the library and the nearest metropolitan area
#That is not the current metro(if current is a metropolitan area)
#Use the CDC data, and find the median population desnity in each city per state, keep a record of all the 
## cities over the median range of pop density -- get their geolocation
#Find a probe close to each of these metropolitan areas and 5 closest probes near the city -- make sure no repeat happens

#Saving the data
with open(f'./Library_Static_Data/Results_{library_name}/grouped_probes.json', 'w') as f:
    json.dump(data, f, indent=4)