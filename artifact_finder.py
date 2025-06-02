# This file will go through the trace json, and make a dictionary of number of unique artifacts per library and how many traces 
# go through them
import os
import json
import ipaddress
from collections import defaultdict

def preprocess_cidrs(input_ips):
    """Convert CIDR strings to network objects and separate individual IPs for faster matching"""
    networks = []
    individual_ips = set()
    
    for cidr in input_ips:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            if network.num_addresses == 1:
                # Single IP address
                individual_ips.add(str(network.network_address))
            else:
                # Actual network range
                networks.append(network)
        except ValueError:
            print(f"Invalid CIDR: {cidr}")
    
    return networks, individual_ips

def find_matching_ips_optimized(trace_keys, networks, individual_ips):
    """Optimized IP matching using preprocessing"""
    target_keys = set()
    
    # Convert trace keys to IP objects once for network checking
    valid_trace_ips = {}
    for key in trace_keys:
        if key in individual_ips:
            target_keys.add(key)
        else:
            try:
                valid_trace_ips[key] = ipaddress.ip_address(key)
            except ValueError:
                print(f"Invalid IP address: {key}")
    
    # Check remaining IPs against networks
    for key, ip_obj in valid_trace_ips.items():
        for network in networks:
            if ip_obj in network:
                target_keys.add(key)
                break
    
    return target_keys

def process_artifacts_optimized(trace_data, target_keys, max_len=6):
    """Process artifacts with optimized data structures"""
    ip_ingress = set()  # Use set to avoid duplicates
    cidr_ingress = set()
    
    for key in target_keys:
        key_data = trace_data[key]
        common_ips = key_data.get('Common_IPs', {})
        common_cidrs = key_data.get('Common_CIDRs', {})
        
        # Process IPs
        for ip, ip_data in common_ips.items():
            if len(ip_data) >= max_len:
                ip_ingress.add(ip)
        
        # Process CIDRs
        for cidr, cidr_data in common_cidrs.items():
            if len(cidr_data) >= max_len:
                cidr_ingress.add(cidr)
    
    return list(ip_ingress), list(cidr_ingress)

# Main execution
filtered_file = 'final_filtered.txt'
input_file = 'validation_libraries.txt'
directory = './Library_Static_Data_og/'
save_file_name_ip = 'trace_ip_artifacts.txt'
save_file_name_cidr = 'trace_cidr_artifacts.txt'

# Read folders once
try:
    with open(input_file, 'r') as f:
        lines = f.readlines()
    folders = ['Results_' + line.strip().split('~')[2].replace(' ', '_') for line in lines]
except FileNotFoundError:
    print(f"Input file {input_file} not found")
    exit(1)

for folder in folders:
    folder_path = os.path.join(directory, folder)
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist, skipping...")
        continue
    
    filtered_file_path = os.path.join(folder_path, filtered_file)
    if not os.path.exists(filtered_file_path):
        print(f"Filtered file {filtered_file_path} does not exist, skipping...")
        continue
    
    # Read input IPs
    try:
        with open(filtered_file_path, 'r') as f:
            input_ips = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error reading {filtered_file_path}: {e}")
        continue
    
    # Preprocess CIDRs for faster matching
    networks, individual_ips = preprocess_cidrs(input_ips)
    
    # Loading the trace json file
    trace_file_path = os.path.join(folder_path, 'Trace_data.json')
    if not os.path.exists(trace_file_path):
        print(f"Trace file {trace_file_path} does not exist, skipping...")
        continue
    
    try:
        with open(trace_file_path, 'r') as f:
            trace_data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {trace_file_path}: {e}")
        continue

    trace_keys = list(trace_data.keys())

    # Checking which keys are in the input_ips (optimized)
    target_keys = find_matching_ips_optimized(trace_keys, networks, individual_ips)

    print(f"Folder: {folder}, set IPs in trace: {len(target_keys)}")

    # Look through the key common IPs and common CIDRs, pick the ones with the biggest length, for ties select all
    ip_ingress, cidr_ingress = process_artifacts_optimized(trace_data, target_keys, max_len=6)
    
    # Saving the results to files
    save_ip_path = os.path.join(folder_path, save_file_name_ip)
    try:
        with open(save_ip_path, 'w') as f:
            for ip in ip_ingress:
                f.write(ip + '\n')
        print(f"Saved IP ingress data to {save_ip_path}")
    except Exception as e:
        print(f"Error saving IP data to {save_ip_path}: {e}")
    
    save_cidr_path = os.path.join(folder_path, save_file_name_cidr)
    try:
        with open(save_cidr_path, 'w') as f:
            for cidr in cidr_ingress:
                f.write(cidr + '\n')
        print(f"Saved CIDR ingress data to {save_cidr_path}")
    except Exception as e:
        print(f"Error saving CIDR data to {save_cidr_path}: {e}")