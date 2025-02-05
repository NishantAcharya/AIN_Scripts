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

def retreive_msm(msm):
    kwargs = {
        "msm_id": msm
    }
    #Checking if the measurement stopped
    #status = Measurement(id=msm).status
    #while(status != "Stopped"):
    #    if(status == "No suitable probes" or status == "Failed" or status == "Archived"):
    #        break
    #    print("--Waiting for the Measurement : ", msm, " --")
        #time.sleep(120) #Sleeping for 2 minutes
    #print("--Recieved Measurement--")
    
    

    is_success, results = AtlasResultsRequest(**kwargs).create()
    
    if(Measurement(id=msm).status == "No suitable probes" or Measurement(id=msm).status == "Failed" or Measurement(id=msm).status == "Archived"):
        is_success = False
    

    print(Measurement(id=msm).status)
    print(Measurement(id=msm).start_time)
    print(Measurement(id=msm).stop_time)
    print(results)

#retreive_msm(86678278)

def create_trace(probe_ids,ip,key,st):

  if ip == None or ip == 'None':
    return '?1'

  #grabbing all the probe_ids:
  
  probes = ""
  for probe in probe_ids:
      probes+= str(probe)+","
  
  probes = probes[:-1]
  
  current_name = ip+'-'+'AIN-PING'

  ping = Ping(
      af=4,
      target=ip,
      description=current_name
  )

  source = AtlasSource(
      type="probes",
      value=probes,
      requested = len(probe_ids),
      tags={"include":["system-ipv4-works"]}
  )
  atlas_request = AtlasCreateRequest(
      start_time=datetime.now(timezone.utc)+timedelta(minutes=st+1),
      stop_time=datetime.now(timezone.utc)+timedelta(minutes=st+11),
      key=key,
      measurements=[ping],
      sources=[source],
      is_oneoff=False
  )

  (is_success, response) = atlas_request.create()
  if not is_success:
      raise Exception("Measurement Not Created, Please check reponse\n \t"+str(response))

  return response['measurements'][0]


probes = []
data = []
with open('JSON/grouped_probes.json') as f:
    data = json.load(f)

for key in data.keys():
    group = data[key]
    for dist in group.keys():
        probes.append(data[key][dist])

print(probes)
msm = create_trace(probes,'174.61.188.144','',3)
print(msm)