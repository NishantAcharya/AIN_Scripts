# Enhanced version of provider_as_information.py with CIDR-ASN mapping
import os
import pandas as pd
import ipaddress
import json
from tqdm import tqdm
import multiprocessing
from collections import defaultdict
import radix

directory = './Library_Static_Data/'
input_file = 'validation_input.txt'
prefix_2_as_file = './Data_set/Prefix_AS.pfx2as'

def load_prefix_to_as_mapping_optimized(file_path):
    """Load prefix to AS mapping using radix tree for O(log n) lookups"""
    rtree = radix.Radix()
    
    print("Loading prefix to AS mapping...")
    with open(file_path, 'r') as f:
        for line in tqdm(f, desc="Loading prefixes"):
            parts = line.strip().split()
            if len(parts) >= 3:
                net_ip = parts[0]
                prefix = parts[1]
                asn = parts[2]
                try:
                    # Add to radix tree
                    rnode = rtree.add(f"{net_ip}/{prefix}")
                    rnode.data["asn"] = asn
                except:
                    continue
    
    print(f"Loaded {len(rtree.nodes())} prefixes into radix tree")
    return rtree

def get_asn_from_cidr_optimized(cidr, rtree):
    """Fast ASN lookup using radix tree - O(log n) complexity"""
    try:
        # Find the best matching prefix
        rnode = rtree.search_best(cidr)
        if rnode and "asn" in rnode.data:
            return rnode.data["asn"]
    except:
        pass
    return None

def process_cidrs_batch(cidrs, rtree):
    """Process a batch of CIDRs to find their ASNs and return mapping"""
    asn_set = set()
    cidr_asn_mapping = {}
    
    for cidr in cidrs:
        asn = get_asn_from_cidr_optimized(cidr, rtree)
        cidr_ip = cidr.split('/')[0]  # Get the base IP address without prefix
        if asn:
            asn_set.add(asn)
            cidr_asn_mapping[cidr_ip] = asn
        else:
            cidr_asn_mapping[cidr_ip] = None
    
    return asn_set, cidr_asn_mapping

def process_folder_optimized(args):
    folder, rtree = args
    path = os.path.join(directory, folder, 'final_filtered.txt')
    if not os.path.exists(path):
        print(f"File {path} does not exist, skipping...")
        return

    output_file = os.path.join(directory, folder, 'asn_list.txt')
    mapping_file = os.path.join(directory, folder, 'cidr_asn_mapping.json')
    print(output_file, mapping_file)

    # Read all CIDRs at once
    with open(path, 'r') as f:
        cidrs = [line.strip() for line in f if line.strip()]

    print(f"Processing folder: {folder}, CIDRs found: {len(cidrs)}")

    # Process in batches for better memory management
    batch_size = 10000
    all_asns = set()
    complete_mapping = {}

    for i in tqdm(range(0, len(cidrs), batch_size), desc=f"Processing {folder}"):
        batch = cidrs[i:i + batch_size]
        batch_asns, batch_mapping = process_cidrs_batch(batch, rtree)
        all_asns.update(batch_asns)
        complete_mapping.update(batch_mapping)

    asn_list = list(all_asns)

    # Save the ASN list to a text file (not JSON)
    with open(output_file, 'w') as f:
        for asn in asn_list:
            f.write(asn + '\n')

    # Save the complete CIDR-ASN mapping as JSON
    with open(mapping_file, 'w') as f:
        json.dump(complete_mapping, f, indent=2)
    

def main():
    # Load validation libraries
    with open(input_file, 'r') as f:
        lines = f.readlines()
        val_libs = ['Results_'+line.strip().split('~')[2].strip().replace(' ','_') for line in lines]

    # Get input folders
    input_folders = []
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)) and folder in val_libs:
            input_folders.append(folder)
    
    print(f"Found {len(input_folders)} folders to process")
    

    rtree = load_prefix_to_as_mapping_optimized(prefix_2_as_file)
    
    # Use multiprocessing with shared radix tree
    with multiprocessing.Pool() as pool:
        args = [(folder, rtree) for folder in input_folders]
        pool.map(process_folder_optimized, args)
    
    
    

if __name__ == '__main__':
    main()
