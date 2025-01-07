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
        time.sleep(120) #Sleeping for 2 minutes
        status = Measurement(id=msm).status
    print("--Recieved Measurement--")
    
    

    results = AtlasResultsRequest(**kwargs).create()
    

    return results

probes = [55451,21003,1009711]
#Get the IPs from the CSV file

ips = ['174.61.177.67']
cidrs = ['test_pls_delete']

#Alex's key handle with care
secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'
split_key = secure_key.split('-')
key = '-'.join(split_key[1:-1])

#Create the trace
#msm = create_trace(probes,ips[0],key,1)
#print(msm)
#Retrieve the trace
results = retreive_msm(85014547)
print(results)

print('Done')