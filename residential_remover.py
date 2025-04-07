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
def get_all_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return links
    except requests.exceptions.RequestException as e:
         print(f"Error fetching URL: {e}")
         return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    
def download_file(url,local_filename):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)



#To break down a CIDR into smaller subnets with the specified mask such as 28
def break_cidr(cidr, target_mask):
    network = ipaddress.ip_network(cidr)

    if network.prefixlen >= target_mask:
        return [network]  # No need to break down further

    subnets = []
    for subnet in network.subnets(new_prefix=target_mask):
        subnets.append(subnet)

    return subnets

def is_subnet(network1_str, network2_str):
  """
  Checks if network1 is a subnet of network2.

  Args:
    network1_str: The first network in CIDR notation (e.g., "192.168.1.0/24").
    network2_str: The second network in CIDR notation (e.g., "192.168.0.0/16").

  Returns:
    True if network1 is a subnet of network2, False otherwise.
  """
  network1 = ipaddress.ip_network(network1_str)
  network2 = ipaddress.ip_network(network2_str)
  return network1.subnet_of(network2)

def apply_netmask(ip, mask):
    """
    Apply a netmask to an IP address.

    Args:
        ip: The IP address to apply the netmask to.
        mask: The netmask to apply to the IP address.

    Returns:
        The IP address with the netmask applied.
    """
    return str(ipaddress.ip_network(f"{ip}/{mask}", strict=False))

#Read the JSON File and remove the residential IPs, then coagulate under CIDRs and select 1 IP per CIDR
with open('rdns_info.json', 'r') as f:
    data = json.load(f)
    
ips = data['IP']
rdns = data['RDNS']
cidrs = data['CIDR']

for i in range(len(rdns)):
    for j in range(len(rdns[i])):
        if rdns[i][j] is not None and ('residential' in rdns[i][j].lower() or 'res' in rdns[i][j].lower()):
            ips[i].remove(ips[i][j])
            if len(ips[i]) == 0:
                ips.remove(ips[i])
                cidrs.remove(cidrs[i])

cidr_data = {}
for i in range(len(ips)):
    cidr_data[cidrs[i]] = ips[i]

with open('JSON/filtered_rdns_info.json', 'w') as f:
    json.dump(cidr_data, f, indent=4)

#Get AS information from prefix 2 AS and AS rank here using the cidr_data keys
# year = time.strftime("%Y")
# month = time.strftime("%m")
# day = time.strftime("%d")
# day = str(int(day)-2)
# if len(day) == 1:
#     day = '0' + day
# match_string = year + month + day
# links = get_all_links('https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/'+ year + '/'+month+'/')
# pf2asgz = 'Probe_files/pf2as.gz'
# try:
#     output = [link for link in links if match_string in link][-1]
# except:
#     new_month = str(int(month)-1)
#     if len(new_month) == 1:
#         new_month = '0' + new_month
#     
#     day = '28'
#     match_string = year + new_month + day
#     output = [link for link in links if match_string in link][-1]
# 
# download_file('https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/'+ year + '/'+month+'/'+output,pf2asgz)
# pf2as = 'Probe_files/pf2as.pfx2as'
# with gzip.open(pf2asgz, 'rb') as f_in:
#     with open(pf2as, 'wb') as f_out:
#         shutil.copyfileobj(f_in, f_out)
# 
# as_map_mid = {}
# Removing duplicates and going for the least specific AS
# with open(pf2as, 'r') as f:
#     lines = f.readlines()
#     for line in lines:
#         parts = line.strip().split('\t')
#         as_map_mid[parts[0]] = [parts[1],parts[2]]
# 
# as_map = {}
# for key in as_map_mid.keys():
#     new_key = key + '/' +as_map_mid[key][0]
#     as_map[new_key] = as_map_mid[key][1]
# 
# all_ases = {}
# cidr_keys = list(cidr_data.keys())
# as_map_keys = list(as_map.keys())
# This piece of code will collect all the ASes that are in the
# print('Generating AS List')
# for cidr in tqdm(as_map_keys):
#     network = ipaddress.ip_network(cidr)
#     
#     for key in cidr_keys:
#         key_net = ipaddress.ip_network(key)
#         if network.overlaps(key_net):
#             try:
#                 check = all_ases[cidr]
#             except KeyError:
#                 all_ases[cidr] = set()
#             all_ases[cidr].add(as_map[key])
#             break #Already found this AS, no need to check further
# 
# Get the AS rank/ get peers
#             
# sys.exit('Checking execution')
    
print('Masking After Residential Filtering')
#Filter the cidrs and IPs into a mask (for now /26)
masked_ips = []
masked_cidrs = []

mask = 26
for cidr in cidrs:
    subnets = break_cidr(cidr, mask)
    for subnet in subnets:
        masked_cidrs.append(str(subnet))

for i in tqdm(range(len(masked_cidrs))):
    network = ipaddress.ip_network(masked_cidrs[i])
    subnet_ips = []
    for j in range(len(ips)):
        for ip in ips[j]:
            if ipaddress.ip_address(ip) in network:
                subnet_ips.append(ip)
    masked_ips.append(subnet_ips)
    

filtered_ips = []
filtered_cidrs = []

#Loading hitlists
with open('JSON/updated_hitlist.json', 'r') as f:
    hitlist = json.load(f)

print('Finding Hitlist IPs')
for i in tqdm(range(len(ips))):
    if len(masked_ips[i]) > 0:
        #If the /26 CIDR is in the updated hitlist, then grab an IP from it
        #If the CIDR is smaller than /26 then run through the list and check if there's an IP match

        net_bits = int(masked_cidrs[i].split('/')[1])
        if net_bits == 26:
            try:
                h_ips = hitlist[masked_cidrs[i]]
                idx = np.random.randint(0,len(h_ips))
                filtered_ips.append(h_ips[idx])
                filtered_cidrs.append(masked_cidrs[i])
            except KeyError:
                idx = np.random.randint(0,len(masked_ips[i]))
                filtered_ips.append(masked_ips[i][idx])
                filtered_cidrs.append(masked_cidrs[i])
        else:
            net_ip = masked_cidrs[i].split('/')[0]
            masked = apply_netmask(net_ip, 26)
            try:
                h_ips = hitlist[masked]
                for ip in masked_ips[i]:
                    if ip in h_ips:
                        filtered_ips.append(ip)
                        filtered_cidrs.append(masked_cidrs[i])
                        break
            except KeyError:
                idx = np.random.randint(0,len(masked_ips[i]))
                filtered_ips.append(masked_ips[i][idx])
                filtered_cidrs.append(masked_cidrs[i])



#Name the output file         
with open('filtered_ips.txt', 'w') as f:
    for i in range(len(filtered_ips)):
        ip = filtered_ips[i]
        cidr = filtered_cidrs[i]
        f.write(ip +'-'+cidr+ '\n')