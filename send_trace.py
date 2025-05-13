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

#Files
produce_file = str(sys.argv[1])
consume_file = str(sys.argv[2])
inpt_file = str(sys.argv[3])

def read_n_lines_no_newlines(filename, n):
  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file.readlines()[:n]]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  

def read_n_lines_from_line(filename, start_line, n):
  try:
    with open(filename, 'r') as file:
      f_lines = file.readlines()
      lines = [line.strip() for line in f_lines]
      if start_line < 1 or start_line > len(lines):
        print("No more items left : Stopping...")
        exit(0)
      end_line = min(start_line + n - 1, len(lines))
      return lines[start_line - 1:end_line]
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  except ValueError as e:
    print(e)
    return []
  

  
def count_lines_in_file(filename):
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


def create_trace_bulk(probe_ids,ips,key):

  #grabbing all the probe_ids:
###################################################
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
##############################################
  traces_inpt = []
  traces = []

  #Creating the measurements
  for i in range(len(ips)):
    ip = ips[i]
    if ip == None or ip == 'None':
        traces.append('?1')
        continue
    current_name = ip+'-'+'AIN'

    trace = Traceroute(af=4, target=ip, description=current_name,packets=1,protocol="ICMP")

    traces_inpt.append(trace)
    traces.append(0)

  st = datetime.now(timezone.utc)+timedelta(minutes=1)
  et = datetime.now(timezone.utc)+timedelta(minutes=11)
  atlas_request = AtlasCreateRequest(
      start_time=st,
      stop_time=et,
      key=key,
      measurements=traces_inpt,
      sources=[source],
      is_oneoff=False
  )

  (is_success, response) = atlas_request.create()
  if not is_success:
      print(len(ips))
      print(len(traces_inpt))
      print(probes)
      print(key)
      raise Exception("Measurement Not Created, Please check reponse\n \t"+str(response))


  inital_msms = response['measurements']
  msms = []
  count = 0
  i = 0
  while count < len(traces):
    if traces[i] == '?1':
      msms.append('?1')
    else:
      msms.append(inital_msms[count])
      count += 1

    i += 1
  return msms
    


def main(max_buffer_size, producer_file, consumer_file, inpt_file,secure_key):
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
    buffer_size = max_buffer_size
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
        #IP-CIDR-DIRECTORY
        #Check if the line split length is more than 3 elements
        probe_locations = []
        for line in lines:
          if len(line.strip().split('-')) == 3:
            probe_locations.append('-'.join(line.strip().split('-')[2:]))
          elif len(line.strip().split('-')) > 3:
            print(f'Library has - as a seprator {line[2:]}')
            probe_locations.append('-'.join(line.strip().split('-')[2:]))
          else:
            print(f"Error: Line '{line}' does not have enough elements to split.")
            with open('error_log.txt', 'a') as error_file:
              error_file.write(f"Error: Line '{line}' does not have enough elements to split.\n")
            continue

        probe_dict = {}
        for i in range(len(probe_locations)):
          try:
              temp = probe_dict[probe_locations[i]]
          except KeyError:
              probe_dict[probe_locations[i]] = []
          probe_dict[probe_locations[i]].append(ips[i])

        line_dict = {}
        for i in range(len(probe_locations)):
          try:
            temp = line_dict[probe_locations[i]]
          except KeyError:
            line_dict[probe_locations[i]] = []
          line_dict[probe_locations[i]].append(lines[i])
           

        for name in probe_dict.keys():
          #probe location is just the name -- this script should be run from the base directory
          probe_location = f'./Library_Static_Data/{name}/grouped_probes.json'
          ad_ips = probe_dict[name]
          ad_lines = line_dict[name]
          with open(probe_location) as f:
              data = json.load(f)

          key1 = list(data['Close'].keys())
          key2 = list(data['Metro'].keys())
          prbs = []
          prbs.extend(key1)
          prbs.extend(key2)

          
          #Creating the measurement -- add end time here  

          #Bulk traceroute
          msms = []
          CHUNK_SIZE = 1
          SLEEP_TIME = 1.8 #8.6 #7 measurements per minute
          #Change this to 1.7 for Alex's API
          #Dividing into smaller chunks
          for i in range(0, len(ad_ips), CHUNK_SIZE):
            chunk = ad_ips[i:i + CHUNK_SIZE]
            chunk_lines = ad_lines[i:i + CHUNK_SIZE]
            
            inter_msm = create_trace_bulk(prbs,chunk,key)
            msms.extend(inter_msm)
            
            new_lines = []
            for i in range(len(chunk)):
              new_line = chunk_lines[i] + '-' + str(inter_msm[i]) + '\n'
              new_lines.append(new_line)
            #Writing the new lines to the producer file
            with open(producer_file, 'a') as file:
              file.writelines(new_lines)

            #Waiting to make sure the measurement doesn't get overloaded
            time.sleep(SLEEP_TIME)
          #new_lines = []
          #for i in range(len(ad_ips)):
          #  new_line = lines[i] + '-' + str(msms[i]) + '\n' # IP-CIDR-DIRECTORY-MSM
          #  new_lines.append(new_line)

          #Writing the new lines to the producer file
          #with open(producer_file, 'a') as file:
          #  file.writelines(new_lines)

#My Key
#secure_key = '1HHbx12-dd8a740b-2855-4e45-9595-e8a4524d8924-JggFtv'

#My other key
#secure_key = 'oppA12-7e706d8e-8447-49fe-baf5-705d893c5aba-1dcb12'

#Alex's Key
secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'

#Vijeth Key
#secure_key = 'jj8080-4d020a05-6bf9-4871-b36f-9b05fc6b8a38-1bd34'

#probes = [21003,55451,1009747,10342,1145,52574,53097,55692,1008382,30350]
#Redo Probe collection here, only select the unqiue probes

#arg1 --> producer file, arg2 --> consumer file, arg3 --> inpt file
#Use 1000 as buffer size
main(2000,produce_file,consume_file,inpt_file,secure_key)