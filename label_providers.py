import pyasn
import linecache
from pathlib import Path
import os
import csv
import json
from tqdm import tqdm
import ipaddress
import sys

# Files, may need to modify the file path
dat_file = "whois_data/cidr.dat"
csv_file = "whois_data/cidr_greater_25.csv"

asndb = pyasn.pyasn(str(dat_file))
directory = './Library_Static_Data/'

def query_org(IP):
    csv_line_num = asndb.lookup(IP)
    csv_line = linecache.getline(str(csv_file), int(csv_line_num[0])).strip()
    fields = csv_line.split(",")
    if len(fields) < 3:
        print(f"Warning: Not enough fields for IP {IP} - (fields: {len(fields)}) (line: '{csv_line}')")
        return None, None, None
    return fields[0], fields[1], fields[2]

def preprocess_cidrs(lines):
    """Convert CIDR lines to network objects for faster IP matching"""
    networks = []
    individual_ips = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            network = ipaddress.ip_network(line, strict=False)
            if network.num_addresses == 1:
                individual_ips.add(str(network.network_address))
            else:
                networks.append(network)
        except ValueError:
            continue
    
    return networks, individual_ips

def is_ip_in_cidrs(ip_str, networks, individual_ips):
    """Fast check if IP is in any CIDR range"""
    if ip_str in individual_ips:
        return True
    
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for network in networks:
            if ip_obj in network:
                return True
    except ValueError:
        pass
    
    return False

def batch_query_orgs(ips):
    """Query organizations for multiple IPs at once"""
    org_cache = {}
    for ip in ips:
        if ip not in org_cache:
            try:
                org_cache[ip] = query_org(ip)[2]
            except:
                org_cache[ip] = None
    return org_cache

# Get all folders in the directory
folders = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]

for folder in folders:
    folder_path = os.path.join(directory, folder)
    files = [file for file in os.listdir(folder_path)]
    if 'Trace_data.json' not in files or 'final_filtered.txt' not in files:
        continue
    print(f'Processing folder: {folder}')
    
    with open(os.path.join(folder_path, 'Trace_data.json'), 'r') as f:
        trace_data = json.load(f)

    with open(os.path.join(folder_path, 'final_filtered.txt'), 'r') as f:
        lines = f.readlines()

    # Preprocess CIDRs for faster matching
    networks, individual_ips = preprocess_cidrs(lines)
    
    # Extract unique IPs for batch processing
    unique_ips = set()
    for line in tqdm(lines, desc="Extracting IPs"):
        line = line.strip()
        if not line:
            continue
        ip = line.split('/')[0]
        try:
            ipaddress.IPv4Address(ip)
            unique_ips.add(ip)
        except ipaddress.AddressValueError:
            print(f"Invalid IP address: {ip}")
            continue
    
    # Batch query organizations
    print("Batch querying organizations...")
    org_cache = batch_query_orgs(unique_ips)
    
    # Get providers list
    providers = list(set([org for org in org_cache.values() if org is not None and org != '']))
    #print(providers)

    # Saving provider set to a file
    #with open(os.path.join(folder_path, 'provider_set.txt'), 'w') as f:
    #    full_provider_set = list(set(full_provider_set))
    #    for provider in full_provider_set:
    #        f.write(provider + '\n')

    # Write the providers to a file
    #with open(os.path.join(folder_path, 'provider_ips.txt'), 'w') as f:
    #    for provider in provider_set:
    #        f.write(provider + '\n')

    # Print the total number of providers found
    print(f'Total number of providers found for {folder}: {len(provider_set)}')













