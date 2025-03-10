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

        distance = geodesic(lib_geoloc, lat_long).miles
        if distance > 45:
            continue
        if len(close_group) < 10:
            close_group[id] = distance
        else:
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
            if len(metro_group) < 50:
                metro_group[id] = metro_distance
            else:
                if distance < max(metro_group.values()):
                    metro_group.pop(max(metro_group,key=metro_group.get))
                    metro_group[id] = metro_distance
        
    
    return close_group,metro_group

geolocs = [('48.474422','-122.323685'),('36.122069','-82.818696'),('25.944307327270508','-97.50846862792969'),('30.68833351135254','-88.04679870605469'),('36.909472','-95.963552'),('32.7784456','-79.93269'),('38.9911446','-77.0765288'),('41.595119','-102.851207'),('39.745185','-105.000679'),('30.237029','-90.91548')]
library_names = ['Burlington Public Library, WA','Huntsville Public Library, TN','Brownsville Public Library, TX','Mobile Public Library, AL','Iowa Tribe of Oklahoma Public Library, OK','Charleston Library Society, SC','Chevy Chase Community Branch Library,MD','Broadwater Public Library, NE','Auraria Library, CO','River Parishes Community College Library, LA']
#[s,s,l,l,s,s,l,s,l,s] --> Area description, l --> bigger/richer
states = ['Washington','Tennessee','Texas','Alabama','Oklahoma','South Carolina','Maryland','Nebraska','Colorado','Louisiana']

for i in range(len(library_names)):
    library_name = library_names[i]
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