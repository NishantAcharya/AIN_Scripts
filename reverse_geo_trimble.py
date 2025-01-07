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

#Get the geolocation of trimble county library and save it
trimble_geoloc = (38.58325,-85.318154) #From Google Maps

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

#Go through the maxmind and check which addresses have the lat long in a distance of 25 KM

print('GETTING MAXMIND 25 KM CIDRS\n')
maxmind = pd.read_csv('CSV/GeoLite2-City-Blocks-IPv4.csv', low_memory=False)
maxmind_25 = []

for i in tqdm(range(maxmind['latitude'].size)):
    try:
        distance = hs.haversine(trimble_geoloc,(maxmind['latitude'][i],maxmind['longitude'][i]),unit=Unit.KILOMETERS)
    except:
        continue
    if  distance <= 25:
        maxmind_25.append(maxmind['network'][i])

print('GETTING MAXMIND 25 KM IPS\n')
maxmind_25_ips = []
for i in tqdm(maxmind_25):
    maxmind_25_ips.extend(get_ips_in_cidr(i))
##
maxmind_25_ips = list(set(maxmind_25_ips))
print('Maxmind 25 KM CIDRs:',len(maxmind_25))
print('Maxmind 25 KM IPs:',len(maxmind_25_ips))
print('-----------------------------------\n')

#Then go through IPinfo and check which addresses have the lat long is a distance of 25 KM
ipinfo_25 = []
#start_ip,end_ip,join_key,city,region,country,latitude,longitude,postal_code,timezone

print('GETTING IPINFO 25 KM CIDRS\n')
with open('CSV/standard_location.csv') as f:
    count = 0
    for line in tqdm(f):
        csv_line = line.split(',')
        country = csv_line[5]
        if country != 'US':
            continue

        try:
            distance = hs.haversine(trimble_geoloc,(float(csv_line[6]),float(csv_line[7])),unit=Unit.KILOMETERS)
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
                
            
        
                

print('GETTING IPINFO 25 KM IPS\n')
ipinfo_25_ips = []
for i in tqdm(ipinfo_25):
    ipinfo_25_ips.extend(get_ips_in_cidr(i))
ipinfo_25_ips = list(set(ipinfo_25_ips))
print('IPinfo 25 KM CIDRs:',len(ipinfo_25))
print('IPinfo 25 KM IPs:',len(ipinfo_25_ips))
print('-----------------------------------\n')

#Create a union and create an intersection of these two sets
maxmind_25_set = set(maxmind_25_ips)
ipinfo_25_set = set(ipinfo_25_ips)

intersection = maxmind_25_set.intersection(ipinfo_25_ips)
union = maxmind_25_set.union(ipinfo_25_ips)

print('Intersection CIDRs:',len(intersection))
print('Union CIDRs:',len(union))
print('-----------------------------------\n')

#Record the number of CIDRs not in intersection but in union
not_intersection = union - intersection
print('Not in Intersection CIDRs:',len(not_intersection))
print('-----------------------------------\n')

#Put the intersection and union in a file
with open('intersection.txt','w') as f:
    for i in intersection:
        f.write(i+'\n')

with open('union.txt','w') as f:
    for i in union:
        f.write(i+'\n')

print('Done!')