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


#Change the trace type to one time measurement, if that doesn't work increase the trace time from 5 to 10 minutes
def create_trace(probe_ids,ip,key):
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
        start_time=datetime.now(timezone.utc)+timedelta(minutes=1),
        #stop_time=datetime.now(timezone.utc)+timedelta(minutes=6),
        key=key,
        measurements=[trace],
        sources=[source],
        is_oneoff=True
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
    while(Measurement(id=msm).status != "Stopped"):
        if(Measurement(id=msm).status == "No suitable probes" or Measurement(id=msm).status == "Failed" or Measurement(id=msm).status == "Archived"):
            break
        print("--Waiting for the Measurement : ", msm, " --")
        time.sleep(180) #Sleeping for 3 minutes
    print("--Recieved Measurement--")
    
    

    is_success, results = AtlasResultsRequest(**kwargs).create()
    
    if(Measurement(id=msm).status == "No suitable probes" or Measurement(id=msm).status == "Failed" or Measurement(id=msm).status == "Archived"):
        is_success = False
    

    return results

# Shared Memory variables
CAPACITY = 2500
buffer = []
in_index = 0
out_index = 0
 
# Declaring Semaphores
mutex = threading.Semaphore()
empty = threading.Semaphore(CAPACITY)
full = threading.Semaphore(0)
    

#Run Script with threads
#One producer that produces the data
#The consumer checks the buffer, if nothing is available to consume, then wait for 3 minutes

#Probes, before running dobule check if these probes are active     
probes = []
#Get the IPs from the CSV file
#



#Alex's key handle with care
secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'
#key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv' #Add your RIPE Atlas API key here
#key = '12c3gh-e190d841-2aa2-4477-b714-2c9e440385eb-kKlm9'

#secure_key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv'
#split_key = secure_key.split('-')
#key = '-'.join(split_key[1:-1])

script_data = [probes,ips]
run_script(script_data,secure_key)
#msm = create_trace(probes,'12.207.142.65',key)
#output = retreive_msm(msm)
#print(output)
print('\n------Done------\n')


#The measurement worked, no idea why it was not working before.. 
#Probably the deprecated utcnow() function
#Will launch once I hit davis