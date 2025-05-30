import numpy as np
import pandas as pd
import json
import ipaddress
from tqdm import tqdm
import time
from bs4 import BeautifulSoup
import requests
import gzip
import shutil
import sys

#Helper
def apply_netmask(ip, mask):
    return str(ipaddress.ip_network(f"{ip}/{mask}", strict=False))

#Meta information
mask = 26
input_file = sys.argv[1] #Results_{lib_name}/filtered_ips.txt
output_path = sys.argv[2] # dup removed
output_path = output_path.replace(" ", "\ ")
cidr_save_path = sys.argv[3] #Results_{lib_name}/filtered_cidrs.txt

with open(input_file, 'r') as f:
    lines = f.readlines()

processed_lines = {}
test_file = 'test.txt'
for line in lines:
  ip = line.strip().split('-')[0].strip()
  try:
    o_cidr = line.strip().split('-')[1].strip().split('/')[1]
  except:
    print(line)
    continue
  if int(o_cidr) < 24:
    continue
  cidr_26 = apply_netmask(ip,mask)
  ########
  #######
  try:
    temp = processed_lines[cidr_26]
  except KeyError:
    processed_lines[cidr_26] = line
  

new_lines = list(processed_lines.values())
with open(output_path, 'w') as f:
    f.writelines(new_lines)

total_cidrs = list(processed_lines.keys())
with open(cidr_save_path, 'w') as f:
    for cidr in total_cidrs:
        f.write(cidr + '\n')
