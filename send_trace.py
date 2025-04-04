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
  
#Check if multiple measurements can be made at once here
#Yeah this can be done, will be much faster to do bulk set ups
#Schedule the first bulk for 30 minutes, 5 minutes in advance
#Wait until at least 500 are cleared up and then schedule them together
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

def create_trace_bulk(probe_ids,ips,key,st,et):


    


    #grabbing all the probe_ids:

    probes = ""
    for probe in probe_ids:
        probes+= str(probe)+","

    probes = probes[:-1]

    source = AtlasSource(
        type="probes",
        value=probes,
        requested = len(probe_ids),
        tags={"include":["system-ipv4-works"]}
    )

    

    traces = []
    for ip in ips:
      if ip == None or ip == 'None':
        return '?1'
      current_name = ip+'-'+'AIN'
       
      trace = Traceroute(af=4, target=ip, description=current_name,packets=1,protocol="ICMP")
    
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


def main(buffer_size, producer_file, consumer_file, inpt_file,secure_key,prbs):
    print('Starting producer...')
  
    consumed = 0
    produced = 0
    exists_consumer = False

    #Checking if the main IP file exists
    if not os.path.exists(inpt_file):
        raise Exception(f"Error: File '{inpt_file}' not found.")

    if not os.path.exists(producer_file):
        print(f"Warning: File '{producer_file}' not found. Making producer file.")
        fd = open(producer_file, 'w')
        fd.close()
        exists_producer = True

    inpts = count_lines_in_file(inpt_file)

    #Current File line
    current_line = count_lines_in_file(producer_file) + 1
    while produced < inpts:
        if not os.path.exists(consumer_file):
          print(f"Warning: File '{consumer_file}' not found. Producer to assumer 0 consumed")
        else:
            consumed = count_lines_in_file(consumer_file)
            print(f'Consumed: {consumed}')
        
        produced = count_lines_in_file(producer_file)
        print(f'Produced: {produced} -- Inpts: {inpts}')

        if produced - consumed >= buffer_size:
           print('Buffer full...')
           time.sleep(300)
           continue
        
        to_read = abs(buffer_size - abs(produced - consumed))
        print(f'To read: {to_read}')
        
        print('Producing...')
        lines = read_n_lines_from_line(inpt_file, current_line, to_read)
        current_line += to_read
        #Extract the IPs from the line, but not the CIDRs
        ips = [line.strip().split('-')[0] for line in lines]
        split_key = secure_key.split('-')
        key = '-'.join(split_key[1:-1])

        #Change this to not be adaptive and just use 2K requests but 30 minutes in advance
        #Also adjust the start and the end time here to be 30 minutes in advance
        #Any susbequent ones get scheduled 10 minutes from current time and end in 30 minutes from current time

        #The start time deviation
        start_time = datetime.now(timezone.utc)+timedelta(minutes=15)
        end_time = datetime.now(timezone.utc)+timedelta(minutes=40)
        for i in range(len(ips)):
            ip = ips[i]
            probe = prbs
            line = lines[i]
            msm = create_trace(probe,ip,key,start_time,end_time)

            new_line = line + '-' + str(msm) + '\n'

            with open(producer_file, 'a') as file:
              file.write(new_line)     

#My Key
secure_key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv'

#Alex's Key
#secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'

#probes = [21003,55451,1009747,10342,1145,52574,53097,55692,1008382,30350]
#Redo Probe collection here, only select the unqiue probes
probes = []
data = []
with open('JSON/grouped_probes.json') as f:
    data = json.load(f)

for key in data.keys():
    group = data[key]
    for dist in group.keys():
        probes.append(data[key][dist])

probes = list(set(probes))

main(2000,'producer_trace.txt','consumer_trace.txt','filtered_ips.txt',secure_key,probes)