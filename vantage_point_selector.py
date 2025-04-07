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

def main(lib_geoloc,metro_geolocs):
    data = get_file()
    close_group = {}
    metro_group = {}

    #Rewrite this to get the 5 closest probes to the library and the 5 closest probes to the metro area
    for probe in tqdm(data):
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']),str(probe['longitude'])
        id = probe['id']
        ip_v4 = probe['address_v4']
        ip_v6 = probe['address_v6']
#Make sure the metro and the close probes are taking the smallest possible ones
#Currently we are just taking the max for the close probes for some reason
        distance = geodesic(lib_geoloc, lat_long).miles
        if distance > 35:
            continue
        if len(close_group) < 10:
            close_group[id] = distance
        else:
            #Check this
            if distance < max(close_group.values()):
                close_group.pop(max(close_group,key=close_group.get))
                close_group[id] = distance

    for probe in tqdm(data):
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']),str(probe['longitude'])
        id = probe['id']

        
        for metro in metro_geolocs:
            metro_dist = str(metro[0]),str(metro[1])
            metro_distance = geodesic(metro_dist, lat_long).miles
            #Aleady got the closest possbile 10 probes in a 45 mile radius
            if id in close_group.values() or metro_distance > 30:
                continue
            if len(metro_group) < 40:
                metro_group[id] = metro_distance
            else:
                if distance < max(metro_group.values()):
                    metro_group.pop(max(metro_group,key=metro_group.get))
                    metro_group[id] = metro_distance

    #Getting the IPs
    for probe in tqdm(data):
        country = probe['country_code']
        if country != 'US' or probe['status_name'] != 'Connected' or probe['is_public'] == False:
            continue
        lat_long = str(probe['latitude']),str(probe['longitude'])
        id = probe['id']
        ip_v4 = probe['address_v4']
        ip_v6 = probe['address_v6']

        if id in close_group.keys():
            close_group[id] = (close_group[id],ip_v4,ip_v6)
        if id in metro_group.keys():
            metro_group[id] = (metro_group[id],ip_v4,ip_v6)
        
    
    return close_group,metro_group
#Pobe existence (at least 3 nearby probes) is a factor in library selection
geolocs = [('42.2450259','-84.7458006'),('44.9731694','-93.243012'),('48.474422','-122.323685'), ('36.909472','-95.963552'), ('32.7784456','-79.93269'), 
           ('38.9911446','-77.0765288'), ('39.745185','-105.000679'), ('30.237029','-90.91548'),('40.829202','-84.925192'),('40.39101791381836','-111.91393280029297')]
library_names = ['Stockwell-Mudd Libraries','Elmer L. Andersen Library','Burlington Public Library, WA', 'Iowa Tribe of Oklahoma Public Library, OK', 
                 'Charleston Library Society, SC', 'Chevy Chase Community Branch Library, MD', 
                 'Auraria Library, CO', 'River Parishes Community College Library, LA', 'Adams Public Library, IN','Saratoga Springs Public Library, UT']
states = ['Michigan','Minnesota','Washington', 'Oklahoma', 'South Carolina', 'Maryland', 'Colorado', 'Louisiana', 'Indiana','Utah']



for i in range(len(library_names)):
    library_name = library_names[i]
    print(f"Processing {library_name}")
    state = states[i]
    geoloc = geolocs[i]
    with open('Probe_files/state_geoloc_density.json') as f:
        try:
            state_data = json.load(f)[state]
        except KeyError:
            print(f"Error: No data for {state}")

        metro_geoloc = state_data['top_density_geoloc']

    close_group,metro_group = main(geoloc,metro_geoloc)
    print(f"Close Group: {len(close_group)}")
    print(f"Metro Group: {len(metro_group)}")
    data = {'Close':close_group,'Metro':metro_group}

    #Use this to create a trace vantage selector from an area close to the library and the nearest metropolitan area
    #That is not the current metro(if current is a metropolitan area)
    #Use the CDC data, and find the median population desnity in each city per state, keep a record of all the 
    ## cities over the median range of pop density -- get their geolocation
    #Find a probe close to each of these metropolitan areas and 5 closest probes near the city -- make sure no repeat happens

    #Saving the data
    with open(f'JSON/grouped_probes_{library_name}.json', 'w') as f:
        json.dump(data, f, indent=4)