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

#Before optimizing, figure out the None traceroute issue -- take None out of retrience trace
## Experimtent with increasing the trace time
## Check if the ones that send None are responsive hosts or not
## Esentially what can cause a non succesul trece on ripe
## More likeley than not this is caused by easurement scheduling as Alex mentioned use the mpakit CTI scheduling code
#Optimize with a bounded buffer

#Add a check log here -- if the measurement is stopped it can be restarted
#Add the check when the measurement is created, remove when the measurement is retrieced succesfully

def create_trace(probe_ids,ip,key,st):
    #grabbing all the probe_ids:
    
    probes = ""
    for probe in probe_ids:
        probes+= str(probe)+","
    
    probes = probes[:-1]
    
    current_name = ip+'-'+'AIN'

    trace = Traceroute(af=4, target=ip, description=current_name,packets=1,protocol="ICMP")
    source = AtlasSource(
        type="probes",
        value=probes,
        requested = len(probe_ids),
        tags={"include":["system-ipv4-works"]}
    )
    atlas_request = AtlasCreateRequest(
        start_time=datetime.now(timezone.utc)+timedelta(minutes=st),
        stop_time=datetime.now(timezone.utc)+timedelta(minutes=st+10),
        key=key,
        measurements=[trace],
        sources=[source],
        is_oneoff=False
    )

    (is_success, response) = atlas_request.create()
    if not is_success:
        raise Exception("Measurement Not Created, Please check reponse\n \t"+str(response))

    return response['measurements'][0]

def retreive_msm(msm):
    kwargs = {
        "msm_id": msm
    }
    #Checking if the measurement stopped
    status = Measurement(id=msm).status
    while(status != "Stopped"):
        if(status == "No suitable probes" or status == "Failed" or status == "Archived"):
            break
        print("--Waiting for the Measurement : ", msm, " --")
        time.sleep(180) #Sleeping for 3 minutes
        status = Measurement(id=msm).status
    print("--Recieved Measurement--")
    
    

    is_success, results = AtlasResultsRequest(**kwargs).create()
    
    if(Measurement(id=msm).status == "No suitable probes" or Measurement(id=msm).status == "Failed" or Measurement(id=msm).status == "Archived"):
        is_success = False
    

    return results
    
#Save the msm values in a csv
def run_script(data,secure_key):
    #######Bounded Buffer start########
    #Setting up the buffer
    CAPACITY = 1000
    buffer = []
    
    probe_data = data[0]
    ip_data = data[1]
    cidr_data = data[2]

    items_produced = 0
    while items_produced < len(ip_data):

        if len(probe_data) == 0:
            items_produced += 1
            continue

        print('Start Sending ....')

        ip = ip_data[items_produced]
        cidr = cidr_data[items_produced]
        file_path="ip_list.txt"
        with open(file_path, 'r+') as file:
            lines = file.readlines()
            if ip + '\n' in lines:
                items_produced += 1
                continue
        
        split_key = secure_key.split('-')
        key = '-'.join(split_key[1:-1])
        
        file_path="ip_list.txt"
        #if buffer is full wait
        if len(buffer) >= CAPACITY:
            print("Buffer Full, waiting for consumer to consume... \n Buffer Size: ", len(buffer))
            while len(buffer) > 0:
                print("Starting retrieving...")
                item = buffer.pop(0)
                entry_msm = item[0]
                entry_ip = item[1]
                entry_cidr = item[2]
                just_msms = {}
                just_msms[entry_ip] = retreive_msm(entry_msm)
                print("GOT MSM: ", entry_msm) #Value can be None if the trace doesn't go off

                #Saving the trace                 
                today = date.today()
                date_t = today.strftime("%b-%d-%Y")

                #Make sure there is a JSON folder in the same place as this script
                dirname = "JSON/"+date_t+"/"

                os.makedirs(os.path.dirname(dirname), exist_ok=True)
                filename = dirname+ str(entry_msm)+ '-'+str(entry_ip)+'-'+str(entry_cidr).replace('/','?')+".json"
                with open(filename, "w+") as outfile: 
                    json.dump(just_msms, outfile)
                file_path="ip_list.txt"
                with open(file_path, 'a+') as file:
                    file.write(entry_ip + '\n')
        #creating

        #Open the sent file, if ip is in it then add it to buffer
        #then continue

        msm = create_trace(probe_data,ip,key,items_produced%84)
        buffer.append([msm,ip,cidr])
        print("SENT MSM: ", msm)


        items_produced += 1

    #if buffer is full wait
    print("Consuming Leftovers...")
    while len(buffer) > 0:
        print("Starting retrieving...")
        item = buffer.pop(0)
        entry_msm = item[0]
        entry_ip = item[1]
        entry_cidr = item[2]
        just_msms = {}
        just_msms[entry_ip] = retreive_msm(entry_msm)
        print("GOT MSM: ", entry_msm) #Value can be None if the trace doesn't go off

        #Saving the trace                 
        today = date.today()
        date_t = today.strftime("%b-%d-%Y")

        #Make sure there is a JSON folder in the same place as this script
        dirname = "JSON/"+date_t+"/"

        os.makedirs(os.path.dirname(dirname), exist_ok=True)
        filename = dirname+ str(entry_msm)+ '-'+str(entry_ip)+'-'+str(entry_cidr).replace('/','?')+".json"
        with open(filename, "w+") as outfile: 
            json.dump(just_msms, outfile)
        file_path="ip_list.txt"
        with open(file_path, 'a+') as file:
            file.write(entry_ip + '\n')

        #Clear the sent file

#Probes, before running dobule check if these probes are active     
#probes = [55451,21003,1009711]
#Loading probes
probes = []
data = []
with open('JSON/grouped_probes.json') as f:
    data = json.load(f)

for key in data.keys():
    group = data[key]
    for dist in group.keys():
        probes.append(data[key][dist])

#Get the IPs from the CSV file

ips = []
cidrs = []

with open('filtered_ips.txt') as f:
    for line in f:
        ip,cidr = line.strip().split('-')
        ips.append(ip)
        cidrs.append(cidr)



#Alex's key handle with care
secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'
#key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv' #Add your RIPE Atlas API key here
#key = '12c3gh-e190d841-2aa2-4477-b714-2c9e440385eb-kKlm9'

#100
#secure_key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv'
#split_key = secure_key.split('-')
#key = '-'.join(split_key[1:-1])

script_data = [probes,ips,cidrs]
start_time = time.time()
run_script(script_data,secure_key)
end_time = time.time()
#Clearing the sent file

print('Time taken:',end_time-start_time)
print('\n------Done------\n')


#The measurement worked, no idea why it was not working before.. 
#Probably the deprecated utcnow() function
#Will launch once I hit davis