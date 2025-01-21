#Receive's pings

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
  

def read_all_lines_no_newlines(filename):
  """
  Reads all lines from a file and removes all newline characters ('\n') from each line.

  Args:
    filename: The name of the file to read.

  Returns:
    A list of strings, where each string is a line from the file without newline characters.
  """
  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []

def check_status(msm):
    status = Measurement(id=msm).status
    return status

def retreive_msm(msm):
    kwargs = {
        "msm_id": msm
    }

    is_success, results = AtlasResultsRequest(**kwargs).create()
    return results

def save_to_file(key_ip,msm,ip,cidr,probe,data):
   #Saving the trace                 
    today = date.today()
    date_t = today.strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H-%M-%S")

    #Make sure there is a JSON folder in the same place as this script
    dirname = "JSON/"+date_t+"/"

    os.makedirs(os.path.dirname(dirname), exist_ok=True)
    filename = dirname+current_time+'-'+str(key_ip)+ '-'+str(probe)+'-'+str(ip)+'-'+str(cidr).replace('/','?')+'-'+str(msm)+".json"
    with open(filename, "w+") as outfile: 
        json.dump(data, outfile)



def main(buffer_size, producer_file, consumer_file, inpt_file,secure_key):
  #The script will go through the  producer file and read the inputs there
  #Wait (This part will signify us checking the status of the items)
  #If the status is completed, then download, which will be another sleep here
  ## And then add to consumer, else keep looping
  # Stop when the size of the consumer file is the same as the inpts file

  print('Starting consumer...')

  consumed = 0
  exists_producer = False

  #Checking if the main IP file exists
  if not os.path.exists(inpt_file):
      raise Exception(f"Error: File '{inpt_file}' not found.")
  
  #Checking if the producer file exists
  if not os.path.exists(producer_file):
      print(f"Warning: File '{producer_file}' not found. Producer to assumer 0 consumed")
  else:
      exists_producer = True

  #Checking if the consumer file exists
  if not os.path.exists(consumer_file):
      print(f"Warning: File '{consumer_file}' not found. Making consumer file.")
      fd = open(consumer_file, 'w')
      fd.close()
      exists_consumer = True

  inpts = count_lines_in_file(inpt_file)

  while consumed < inpts:
      #Reading the producer file
      if os.path.exists(producer_file):
        p_lines = read_all_lines_no_newlines(producer_file)
      else:
          print(f"Warning: File '{producer_file}' not found. Producer to assumed 0 consumed")
          p_lines = []
      c_lines = read_all_lines_no_newlines(consumer_file)

      #All elements that have been produced but not consumed yet
      f_lines = [x for x in p_lines if x not in set(c_lines)]

      if len(f_lines) == 0:
          print(f"Nothing to consume, Sleeping")
          time.sleep(120) #Sleep for a longer time than producer
          continue
      
      print('Passing through the produced items')
      for item in tqdm(f_lines):
            values = item.split('-')
            msm = values[-1]
            key_ip = values[0]
            probe = values[1]
            ip = values[2]
            cidr = values[3]
            if msm == '?1':
              print(f'No suitable hop to hit: {ip}')
              save_to_file(key_ip,msm,ip,cidr,probe,{'Failed':True})
              with open(consumer_file, 'a') as file:
                    file.write(item + '\n')
              consumed += 1

            status = check_status(msm)
            if status == "Stopped" or status == "No suitable probes" or status == "Failed" or status == "Archived":
                print("Downloading the results")
                results = retreive_msm(msm)
                save_to_file(key_ip,msm,ip,cidr,probe,results)
                with open(consumer_file, 'a') as file:
                    file.write(item + '\n')
                consumed += 1
            elif status == "No suitable probes" or status == "Failed" or status == "Archived":
                print(f'Measurement Failed: {ip}')
                save_to_file(key_ip,msm,ip,cidr,probe,{'Failed':True})
                with open(consumer_file, 'a') as file:
                    file.write(item + '\n')
                consumed += 1

          
      #Sleep for a short time
      print('Pass Ended, Sleeping before next pass')
      time.sleep(90)

#My Key
#secure_key = '1HHbx12-1c3d00e0-cd3b-46eb-916a-33d0396750ec-JggFtv'

#Alex's Key
secure_key =  '1002abbbeg-42f5aee4-e4d0-4570-a5cf-b31384860e44-Xyzngo'

main(1000,'producer.txt','consumer.txt','ping_inpt.txt',secure_key)