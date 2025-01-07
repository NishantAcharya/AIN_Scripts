import pandas as pd
import numpy as np
import ipaddress
import geoip2.database
import json
from ipwhois import IPWhois
import ast
import time
import requests
from tqdm import tqdm
import math
import socket,struct
import random
import geopy.distance
from googlesearch import search
import re
import matplotlib.pyplot as plt
import docx
import whois
import subprocess
from ast import literal_eval

#Takes IP value, returns orgName, ASN, CIDR
'''def ripe_whois_call(ip):
    base_url = 'https://stat.ripe.net/data/whois/data.json?data_overload_limit=ignore&resource='
    query_url = f'{base_url}{ip}&sourceapp=ripe-stat-AIN'
    
    for _ in range(2):
        try:
            response = requests.get(query_url)
            data = response.json()
        except:
            data = {}
            time.sleep(0.5)
        if 'data' in data.keys() and 'records' in data['data'].keys():
            break
        
    if 'data' not in data.keys() or 'records' not in data['data'].keys():
        data = None
        #None return means that the value wasn't fully there
    
    return data

#Testing the function
#entries = ripe_whois_call('76.35.184.150')
#test = entries['data']['records']
#for keys in test:
#    print(keys)
#    print('\n')

#Extracting information from the whois call
#Get NetName, OrgName, Get allocated CIDR, Get ASN
def extract_data(data):
    entries = data['data']['records']
    netnames = [] #The parent one is on the left
    cidrs = []
    orgnames = []
    
    for entry in entries:
        for sbentry in entry:
            if sbentry['key'] == 'NetName':
                netnames.append(sbentry['value'])
            if sbentry['key'] == 'OrgName':
                orgnames.append(sbentry['value'])
            if sbentry['key'] == 'CIDR':
                cidrs.append(sbentry['value'])
                
    return netnames, orgnames, cidrs

#Testing the function
#netnames, orgnames, cidrs = extract_data(entries)
#print(netnames)
#print(orgnames)
#print(cidrs)


######## Local WHOIS ############
def local_whois_call(ip):
    try:
        entries = whois.whois(ip)
    except:
        entries = None
    return entries

def extract_data_local(data):
    netnames = []
    orgnames = []
    cidrs = []
    
    

#Load the values from the text file
with open('intersection.txt', 'r') as f:
    temp = f.readlines()
    inputs = [x.strip() for x in temp]

#Running and saving the files
print('Starting the process')
output = {'IP': [], 'Netnames': [], 'Orgnames': [], 'CIDRs': []}
for input in tqdm(inputs):
    entries = ripe_whois_call(input)
    if entries is not None:
        netnames, orgnames, cidrs = extract_data(entries)
        output['IP'].append(input)
        output['Netnames'].append(netnames)
        output['Orgnames'].append(orgnames)
        output['CIDRs'].append(cidrs)
    else:
        output['IP'].append(input)
        output['Netnames'].append([])
        output['Orgnames'].append([])
        output['CIDRs'].append([])
        
print('Finished the process')

print('Saving the file')
df = pd.DataFrame(output)
df.to_csv('intersection_whois.csv', index = False)
print('File saved')
print('FILE INFO: The left is the parent org')
print('Done')'''

def ip_in_cidr(ip, cidr):
    ip = ipaddress.ip_address(ip)
    network = ipaddress.ip_network(cidr)
    return ip in network

def whois_to_dict(ip):
    """Converts WHOIS output to a dictionary."""

    result = subprocess.run(['whois', ip], capture_output=True, text=True)
    if result.returncode != 0:
        print("WHOIS command failed: {}".format(result.stderr))
        return [],[],[],[]

    netname = []
    orgname = []
    cidr = []
    parent = []
    for line in result.stdout.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            #Assuning there won't be a new netname without a parent
            if key == 'netname':
                netname.append(value)
            elif key == 'parent':
                parent.append(value)
            elif key == 'cidr':
                cidr.append(value)
            elif key == 'organisation' or key == 'organization':
                orgname.append(value)
            

    return parent, netname ,orgname, cidr

if __name__ == "__main__":
    
    #Load the values from the text file
    #Switch to union.txt for the union and intersection.txt for the intersection
    
    library_name = 'Burlington Public Library, WA'
    filename = f'union_{library_name}.txt'
    
    #Expecting IPs here, take a random IP from the CIDR and get the WHOIS infromation
    with open(filename, 'r') as f:
        temp = f.readlines()
        subnets = [x.strip() for x in temp]
        inputs = [x.split('/')[0] for x in subnets]
        
    #Running and saving the files
    print('Starting the process')
    output = {'IP': [], 'Parents': [], 'Netnames': [], 'Orgnames': [], 'CIDRs': [], 'Subnet': []}   
    
    memo = {}
    
    for input in tqdm(inputs):
        #Check in the memo if the CIDR has been checked before(CIDRs)
        
        subnet = subnets[inputs.index(input)]
        keys = list(memo.keys())
        check = False
        bits = -1
        tp,tn,to,tc = None,None,None,None
        for key in keys:
            k_bits = int(key.split('/')[1].strip())
            if ip_in_cidr(input, key) and k_bits > bits:
                bits = k_bits
                check = True
                tp,tn,to,tc = memo[key]
        if check:
            output['IP'].append(input)
            output['Parents'].append(tp)
            output['Netnames'].append(tn)
            output['Orgnames'].append(to)
            output['CIDRs'].append(tc)
            output['Subnet'].append(subnet)
            continue
        
        parent, netnames, orgnames, cidrs = whois_to_dict(input)
        output['IP'].append(input)
        output['Parents'].append(parent)
        output['Netnames'].append(netnames)
        output['Orgnames'].append(orgnames)
        output['CIDRs'].append(cidrs)
        output['Subnet'].append(subnet)
        
        if type(cidrs) == list and len(cidrs) > 0:
            temp = [x.strip() for x in cidrs[0].split(',')]
            for cidr in temp:
                memo[cidr] = (parent, netnames, orgnames, cidrs)
        elif type(cidrs) == str:
            #The pattern for strings (non list) is that the CIDR is on the first entry of the list as a full string
            cidrs = literal_eval(cidrs)
            temp = [x.strip() for x in cidrs[0].split(',')]
            
            for cidr in temp:
                memo[cidr] = (parent, netnames, orgnames, temp)
        
    print('Finished the process')
    
    print('Saving the file')
    
    df = pd.DataFrame(output)
    
    #Switch to union_whois.csv for the union and intersection_whois.csv for the intersection
    df.to_csv('union_whois.csv', index = False)
    
    print('File saved')
    
    print('FILE INFO: The left is the parent org')
    
    print('Done')

    