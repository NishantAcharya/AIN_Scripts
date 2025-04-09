import numpy as np
from matplotlib import pyplot as plt
from geopy.geocoders import Nominatim
import pandas as pd
from googlemaps import Client as GoogleMaps
import googlemaps
import gmaps 
from keplergl import KeplerGl
import geopandas as gpd
import time
from tqdm import tqdm
import geoip2.database
import haversine as hs
import ast
from haversine import Unit
import json
import socket
import ipaddress
import struct
import sys
from pathlib import Path

#Get the geolocation of trimble county library and save it
#boston_geoloc = (42.349396,-71.078369) #From Google Maps
#geoloc = (48.474422,-122.323685)
#geoloc = (34.073620,-118.400352)
#geoloc = (33.705460, -84.461617)
#library_name = 'Atlanta Fulton Public Library System, GA'

csv_file = './CSV/GeoLite2-City-Blocks-IPv4.csv'
file_name = './reverse_geolocation/cidrs_near_library.txt'

##############
#Find out all the geoids in the US from US.txt --> https://www.geonames.org/data-sources.html
#This might miss some, why not just compare the lat,long for now?
##############

#Get the CIDR blocks from the IP ranges
def ip_range_to_cidr(start_ip, end_ip):
    start = ipaddress.ip_address(start_ip)
    end = ipaddress.ip_address(end_ip)
    return [str(x) for x in list(ipaddress.summarize_address_range(start, end))]

# Output Type ['192.168.1.1/32', '192.168.1.2/31','192.168.1.4/30', '192.168.1.8/31','192.168.1.10/32']

def get_ips_in_cidr(cidr):
    network = ipaddress.ip_network(cidr)
    return [str(ip) for ip in network.hosts()]

#To break down a CIDR into smaller subnets with the specified mask such as 28
def break_cidr(cidr, target_mask):
    network = ipaddress.ip_network(cidr)

    if network.prefixlen >= target_mask:
        return [network]  # No need to break down further

    subnets = []
    for subnet in network.subnets(new_prefix=target_mask):
        subnets.append(subnet)

    return subnets

if len(sys.argv) > 2:
    lat = sys.argv[1]
    lon = sys.argv[2]
else:
    print("Lack of lantitude and longtitude.")
geoloc = (float(lat), float(lon))
#Go through the maxmind and check which addresses have the lat long in a distance of 25 KM

print('GETTING MAXMIND 25 KM CIDRS\n')
maxmind = pd.read_csv(csv_file, low_memory=False)
maxmind_25 = []

for i in tqdm(range(maxmind['latitude'].size)):
    try:
        distance = hs.haversine(geoloc,(maxmind['latitude'][i],maxmind['longitude'][i]),unit=Unit.KILOMETERS)
    except:
        continue
    if  distance <= 25:
        maxmind_25.append(maxmind['network'][i])
        

print('GETTING IPINFO 25 KM CIDRS\n')
#Then go through IPinfo and check which addresses have the lat long is a distance of 25 KM
ipinfo_25 = []
#start_ip,end_ip,join_key,city,region,country,latitude,longitude,postal_code,timezone

print('GETTING IPINFO 25 KM CIDRS\n')
with open('./reverse_geolocation/CSV/standard_location.csv') as f:
    for line in tqdm(f):
        csv_line = line.split(',')
        country = csv_line[5]
        if country != 'US':
            continue

        try:
            distance = hs.haversine(geoloc,(float(csv_line[6]),float(csv_line[7])),unit=Unit.KILOMETERS)
        except:
            continue

        if distance <= 25:
            cidrs = ip_range_to_cidr(csv_line[0],csv_line[1])

            for cidr in cidrs:
                try:
                    temp = ipaddress.IPv4Network(cidr)
                    ipinfo_25.append(cidr)
                except ValueError:
                    continue

print('Converting Back to strings\n')              
maxmind_25 = [str(i) for i in maxmind_25]
ipinfo_25 = [str(i) for i in ipinfo_25]


mask = 24
print(f'Get /{mask} CIDRs\n')
#Getting maxmind updated cidrs
maxmind_25_masked = []
for cidr in tqdm(maxmind_25):
    maxmind_25_masked.extend(break_cidr(cidr,mask))

#Getting ipinfo updated cidrs
ipinfo_25_masked = []
for cidr in tqdm(ipinfo_25):
    ipinfo_25_masked.extend(break_cidr(cidr,mask))
    
print('Maxmind 25 KM CIDRs:',len(maxmind_25_masked))
print('IPinfo 25 KM CIDRs:',len(ipinfo_25_masked))

#Getting union of them both
maxmind_25_masked = list(set(maxmind_25_masked))
ipinfo_25_masked = list(set(ipinfo_25_masked))

union_set = list(set(maxmind_25_masked + ipinfo_25_masked))

print('Union of CIDRs:',len(union_set))
print('Converting Back to Strings\n')
union_set = [str(i) for i in union_set]

#Sorting the CIDRs
union_set.sort()


print('Saving CIDRs to file\n')
with open(file_name,'w') as f:
    for i in union_set:
        f.write(i+'\n')

print('Done!')