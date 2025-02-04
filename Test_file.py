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
    print(results)

retreive_msm(86623325)