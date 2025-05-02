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

    if int(day) <= 0:
        day = 28
        month = today.month-1
        if month <= 0:
            month = 12
            year = today.year-1

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

    if int(day) <= 0:
        day = 28
        month = today.month-1
        if month <= 0:
            month = 12
            year = today.year-1

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

    if count < 7:
        #Get the closest 7 probes
        boundary_dist = temp_distance[4]
    
    #Get the closest probes
    close_group = {}
    close_count = 0
    for i in range(len(values)):
        if close_count > 6:
            break
        if values[i][0] <= boundary_dist:
            id = ids[i]
            distance = values[i][0]
            lat_long = values[i][1]
            ip_v4 = values[i][2]
            ip_v6 = values[i][3]
            close_group[id] = (distance,lat_long,ip_v4,ip_v6)
            close_count += 1

    #Get the closest 3 probes from the closest metro region

    return close_group

def main_m(metro_geolocs,close_keys,c_dense):
    #Run after main() so file is loaded
    data = load_file()
    violating_probes_df = pd.read_csv('CSV/violating_probes_paper.csv')
    violating_probes = violating_probes_df['ProbeID'].tolist()

    #Getting the top 3 metro geolocs based on density
    temp = sorted(zip(c_dense, metro_geolocs), key=lambda x: x[0], reverse=True)
    _,dense_geolocs = zip(*temp)
    top_3_locs = []
    for i in range(len(dense_geolocs)):
        if i > 2:
            break
        top_3_locs.append(dense_geolocs[i])

    metro_dict = {}
    for metro_geoloc in metro_geolocs:
        metro_dict[metro_geoloc] = []

    for probe in tqdm(data):
        if probe['id'] in violating_probes or probe['id'] in close_keys:
            continue
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']), str(probe['longitude'])
        id = probe['id']
        ip_v4 = probe['address_v4']
        ip_v6 = probe['address_v6']
        for metro_geoloc in metro_geolocs:
            distance = geodesic(metro_geoloc, lat_long).miles
            metro_dict[metro_geoloc].append((distance, id, lat_long, ip_v4, ip_v6))

    #Sort the metro_dict by distance
    for metro_geoloc in metro_geolocs:
        metro_dict[metro_geoloc].sort(key=lambda x: x[0])
    
    metro_group = {}
    for item in metro_dict.keys():
        if item not in top_3_locs:
            continue
        id = metro_dict[item][0][1] #Check the tuple above for reference
        distance = metro_dict[item][0][0]
        lat_long = metro_dict[item][0][2]
        ip_v4 = metro_dict[item][0][3]
        ip_v6 = metro_dict[item][0][4]
        metro_group[id] = (distance, lat_long, ip_v4, ip_v6)
    
    return metro_group


    


library_name = str(sys.argv[1])
lat = sys.argv[2]
lon = sys.argv[3]
geoloc = (str(lat), str(lon))

print(f"Processing {library_name}")

close_group = main(geoloc)
print(f"Close Group: {len(close_group)}")
data = {'Close':close_group}

#Saving the data -- will rewrite the file
with open(f'./Library_Static_Data/Results_{library_name}/grouped_probes.json', 'w') as f:
    json.dump(data, f, indent=4)

state = sys.argv[4]
#Loading the metro data

with open('Probe_files/state_geoloc_density.json', 'r') as f:
    metro_data = json.load(f)

#Checking if the state is in the metro data
metro_keys = metro_data.keys()
for key in metro_keys:
    if key.upper() == state:
        state_data = metro_data[key]
        break

#Find at most the closest 5 metro from the lib_geolocation
# number of metros [96, 159, 145, 94, 183, 188, 67, 1, 12, 46, 74, 63, 90, 47, 13, 53, 108, 42, 28, 97, 125, 77, 68, 79, 3, 50, 33, 83, 18, 55, 48, 59, 59, 51, 47, 102, 73, 62, 23, 65, 15, 42, 35, 4, 40, 6, 48, 43, 49, 7, 10, 20]
metro_distances = []
metro_geolocs = []
metro_dense = []
geolocations = state_data['top_density_geoloc']
density = state_data['top_density']
for i in range(len(geolocations)):
    geolocation = geolocations[i]
    metro_lat = str(geolocation[0])
    metro_lon = str(geolocation[1])
    distance = geodesic(geoloc, (metro_lat, metro_lon)).miles
    metro_distances.append(distance)
    metro_geolocs.append((metro_lat, metro_lon))
    metro_dense.append(float(density[i]))

combined = sorted(zip(metro_distances, metro_geolocs,metro_dense), key=lambda x: x[0])
metro_distances, metro_geolocs, metro_dense = zip(*combined)
c_geolocs = []
c_dense = []
for i in range(len(metro_distances)):
    if i > 5:
        break
    c_geolocs.append(metro_geolocs[i])
    c_dense.append(metro_dense[i])
###############################

close_keys = list(close_group.keys())
metro_group = main_m(c_geolocs,close_keys,c_dense)
print(f"Metro Group: {len(metro_group)}")
data['Metro'] = metro_group

#Saving the data -- will rewrite the file
#TODO: Save the date of the probe selection!!
#Check if the save folder exists
if not os.path.exists(f'./Library_Static_Data/Results_{library_name}/Past_probes'):
    os.makedirs(f'./Library_Static_Data/Results_{library_name}/Past_probes')

#Check if the file exists
if os.path.exists(f'./Library_Static_Data/Results_{library_name}/grouped_probes.json'):
    os.rename(
        f'./Library_Static_Data/Results_{library_name}/grouped_probes.json',
        f'./Library_Static_Data/Results_{library_name}/Past_probes/grouped_probes_{date.today()}.json'
    )
with open(f'./Library_Static_Data/Results_{library_name}/grouped_probes.json', 'w') as f:
    json.dump(data, f, indent=4)



