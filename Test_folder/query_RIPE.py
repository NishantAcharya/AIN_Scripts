#Send pings
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
import ipaddress

def read_n_lines_no_newlines(filename, n):
  """
  Reads the first n lines from a file and removes all newline characters ('\n') from each line.

  Args:
    filename: The name of the file to read.
    n: The number of lines to read.

  Returns:
    A list of strings, where each string is a line from the file without newline characters.
  """

  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file.readlines()[:n]]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  

def read_n_lines_from_line(filename, start_line, n):
  """
  Reads n lines from a given line in a file.

  Args:
    filename: The name of the file to read.
    start_line: The line number to start reading from (1-indexed).
    n: The number of lines to read.

  Returns:
    A list of strings, where each string is a line from the file.
  """
  try:
    with open(filename, 'r') as file:
      f_lines = file.readlines()
      lines = [line.strip() for line in f_lines]
      if start_line < 1 or start_line > len(lines):
        raise ValueError(f"Invalid start line: {start_line}")
      end_line = min(start_line + n - 1, len(lines))
      return lines[start_line - 1:end_line]
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  except ValueError as e:
    print(e)
    return []
  

  
def count_lines_in_file(filename):
  """
  Counts the total number of lines in a given file.

  Args:
    filename: The name of the file to count lines in.

  Returns:
    The total number of lines in the file.
  """
  try:
    with open(filename, 'r') as file:
      return sum(1 for _ in file)  # Efficiently count lines using generator expression
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return 0
  
#TODO: Check if multiple measurements can be made at once here
def create_trace(probe_ids,ip,key,st,et):

    if ip == None or ip == 'None':
        return '?1'


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
        start_time=st,
        stop_time=et,
        key=key,
        measurements=[trace],
        sources=[source],
        is_oneoff=False
    )

    (is_success, response) = atlas_request.create()
    if not is_success:
        raise Exception("Measurement Not Created, Please check reponse\n \t"+str(response))

    return response['measurements'][0]

def create_trace_test(probe_ids,ips,key,st,et):
    #grabbing all the probe_ids:
    
    probes = ""
    for probe in probe_ids:
        probes+= str(probe)+","
    
    probes = probes[:-1]
    traces = []
    for ip in ips:
       current_name = ip+'-'+'AIN'
       trace = Traceroute(af=4, target=ip, description=current_name,packets=1,protocol="ICMP")
       traces.append(trace)
    source = AtlasSource(
        type="probes",
        value=probes,
        requested = len(probe_ids),
        tags={"include":["system-ipv4-works"]}
    )
    atlas_request = AtlasCreateRequest(
        start_time=st,
        stop_time=et,
        key=key,
        measurements=traces,
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

""""98.232.25.1-98.232.25.0/26
98.232.25.93-98.232.25.64/26
98.232.25.177-98.232.25.128/26
98.232.25.208-98.232.25.192/26
98.232.26.2-98.232.26.0/26
98.232.26.117-98.232.26.64/26
98.232.26.168-98.232.26.128/26
"""
def main():
    #probes = [21003,55451,1009747,10342,1145,52574,53097,55692,1008382,30350]
    #ips = ['98.232.25.1','98.232.25.93','98.232.25.177','98.232.25.208','98.232.26.168']

    #secure_key = '1c3d00e0-cd3b-46eb-916a-33d0396750ec'

    #st = datetime.now(timezone.utc)+timedelta(minutes=1)
    #et = datetime.now(timezone.utc)+timedelta(minutes=11)
    #msms = create_trace_test(probes,ips,secure_key,st,et)

    #print(msms)
    print(retreive_msm(87628980))
    print('status:',Measurement(id=87628980).status)

main()