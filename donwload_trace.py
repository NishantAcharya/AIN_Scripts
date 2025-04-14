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
consume_file = sys.argv[1]
output_file = sys.argv[2] #Remember to create the Folder if it does not exist

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

def save_to_file_ping(data,entry_msm,entry_ip,entry_cidr):
    #Saving the trace                 
      today = date.today()
      date_t = today.strftime("%b-%d-%Y")
      current_time = datetime.now().strftime("%H-%M-%S")

      just_msms = {}
      just_msms[entry_ip] = data
  
      #Make sure there is a JSON folder in the same place as this script
      dirname = "JSON/"+date_t+"/"
  
      os.makedirs(os.path.dirname(dirname), exist_ok=True)
      filename = dirname+ str(entry_msm)+ '-'+str(entry_ip)+'-'+str(entry_cidr).replace('/','?')+".json"
      with open(filename, "w+") as outfile: 
          json.dump(just_msms, outfile)


def main(consumer_file,download_file):
    return None