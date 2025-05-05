#Receive's pings

from ripe.atlas.cousteau import (
  Ping,
  Traceroute,
    AtlasSource,
    AtlasResultsRequest,
    AtlasCreateRequest,
    AtlasStopRequest,
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
import multiprocessing


#Files
#consume_file = sys.argv[1]
#output_file = sys.argv[2] #Remember to create the Folder if it does not exist

def read_n_lines_no_newlines(filename, n):
  try:
    with open(filename, 'r') as file:
      lines = [line.strip() for line in file.readlines()[:n]]
    return lines
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  
def count_lines_in_file(filename):
  try:
    with open(filename, 'r') as file:
      return sum(1 for _ in file)  # Efficiently count lines using generator expression
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return 0
  

def read_all_lines_no_newlines(filename):
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

def save_to_file_ping(data,entry_msm,entry_ip,entry_cidr,name):
    #Saving the trace                 
      today = date.today()
      date_t = today.strftime("%b-%d-%Y")
      current_time = datetime.now().strftime("%H-%M-%S")

      just_msms = {}
      just_msms[entry_ip] = data
  
      #Make sure there is a JSON folder in the same place as this script
      dirname = f"./Library_Static_Data/{name}/JSON/"+date_t+"/"
  
      os.makedirs(os.path.dirname(dirname), exist_ok=True)
      filename = dirname+ str(entry_msm)+ '-'+str(entry_ip)+'-'+str(entry_cidr).replace('/','?')+".json"
      with open(filename, "w+") as outfile: 
          json.dump(just_msms, outfile)

def main(data):
    """
    This function will be executed by each process.
    It receives a single input argument.
    """
    # Get the current process name
    process_name = multiprocessing.current_process().name

    #IP-CIDR-DIRECTORY-MSM
    if len(data.split('-')) < 4:
      with open('error_log.txt', 'a') as error_file:
        error_file.write(f"Error: Data '{data}' does not contain enough parts.\n")
      return
    if len(data.split('-')) == 4:
      ip = data.split('-')[0]
      cidr = data.split('-')[1]
      directory = data.split('-')[2]
      msm = data.split('-')[3]
    else:
      ip = data.split('-')[0]
      cidr = data.split('-')[1]
      msm = data.split('-')[-1]
      
      directory = '-'.join(data.split('-')[2:-1])
      with open('error_log.txt', 'a') as error_file:
        error_file.write(f"Error: Directory has a seprator - '{data}'.\n")
    print(f"Process {process_name} is processing data: {msm}")
    result = retreive_msm(msm)
    print(result)
    save_to_file_ping(result,msm,ip,cidr,directory)
    print(f'-----------------------------------{msm}-----------------------------------')

if __name__ == '__main__':
    consumer_file = sys.argv[1]
    download_file = sys.argv[2]
    input_file = sys.argv[3]
    producer_file = sys.argv[4]

    # Check if the download file exists, if not create it
    if not os.path.exists(download_file):
      print(f"WARNING: File '{download_file}' does not exist. Creating it.")
      with open(download_file, 'w') as file:
        pass  # Create an empty file

    if not os.path.exists(consumer_file):
      print(f"WARNING: File '{consumer_file}' does not exist. Creating it.")
      with open(consumer_file, 'w') as file:
        pass

    if not os.path.exists(input_file):
      raise FileNotFoundError(f"File '{input_file}' does not exist. Please provide a valid file.")
    # Prepare input data
    #Read the consumed file every minute after the downloads are done, parse, then run the following script
    dwnlds = count_lines_in_file(download_file)
    inpt = count_lines_in_file(input_file)
    cnsms = count_lines_in_file(consumer_file)

    while dwnlds < inpt:
      consumed = read_all_lines_no_newlines(consumer_file)
      donwloaded = read_all_lines_no_newlines(download_file)
      data = [x for x in consumed if x not in set(donwloaded)]
      if len(data) <= 0:
        print(f"Nothing to consume, Sleeping")
        time.sleep(400)
        continue

      # Create a Pool with 4 processes
      with multiprocessing.Pool(processes=8) as pool:
          # Use pool.map to apply the worker function to each input
          pool.map(main, data)
      
      for item in data:
        with open(download_file, 'a') as file:
          file.write(item + '\n')
        dwnlds += 1
      
      #Save the read lines to the download file -- because multiple writers can cause issues


    today_date = date.today().strftime("%Y-%m-%d")
    past_meta_dir = "./past_meta_files/"
    os.makedirs(past_meta_dir, exist_ok=True)

    # Define new file paths with today's date
    new_download_file = os.path.join(past_meta_dir, f"{download_file}_{today_date}.txt")
    new_producer_file = os.path.join(past_meta_dir, f"{producer_file}_{today_date}.txt")
    new_consumer_file = os.path.join(past_meta_dir, f"{consumer_file}_{today_date}.txt")

    # Move the files
    os.rename(download_file, new_download_file)
    os.rename(producer_file, new_producer_file)
    os.rename(consumer_file, new_consumer_file)

    print(f"Files moved to '{past_meta_dir}' with today's date.")



