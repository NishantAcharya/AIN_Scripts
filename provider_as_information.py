# Optimized version of provider_as_information.py
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
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists, skipping...")
        return
    
    # Read all CIDRs at once
    with open(path, 'r') as f:
        cidrs = [line.strip() for line in f if line.strip()]
    
    print(f"Processing folder: {folder}, CIDRs found: {len(cidrs)}")
    
    # Process in batches for better memory management
    batch_size = 10000
    all_asns = set()
    
    for i in tqdm(range(0, len(cidrs), batch_size), desc=f"Processing {folder}"):
        batch = cidrs[i:i + batch_size]
        batch_asns,btach_cidrs = process_cidrs_batch(batch, rtree)
        all_asns.update(batch_asns)
    
    asn_list = list(all_asns)
    
    # Save the ASN list to a JSON file
    with open(output_file, 'w') as f:
        json.dump(asn_list, f)
    
    print(f"Processed {folder}: {len(asn_list)} ASNs found and saved to {output_file}")

# Alternative implementation without radix tree (if py-radix not available)
def load_prefix_to_as_mapping_alternative(file_path):
    """Alternative optimized loading using sorted prefixes"""
    prefixes = []
    
    print("Loading prefix to AS mapping...")
    with open(file_path, 'r') as f:
        for line in tqdm(f, desc="Loading prefixes"):
            parts = line.strip().split()
            if len(parts) >= 3:
                net_ip = parts[0]
                prefix = parts[1]
                asn = parts[2]
                try:
                    network = ipaddress.ip_network(f"{net_ip}/{prefix}")
                    prefixes.append((network, asn))
                except:
                    continue
    
    # Sort by network address for faster lookups
    prefixes.sort(key=lambda x: (x[0].network_address, x[0].prefixlen))
    print(f"Loaded {len(prefixes)} prefixes")
    return prefixes

def get_asn_from_cidr_alternative(cidr, sorted_prefixes):
    """Alternative ASN lookup using binary search on sorted prefixes"""
    try:
        target_network = ipaddress.ip_network(cidr, strict=False)
        
        # Find best matching prefix (longest prefix match)
        best_match = None
        best_prefix_len = -1
        
        for network, asn in sorted_prefixes:
            if target_network.overlaps(network):
                if network.prefixlen > best_prefix_len:
                    best_match = asn
                    best_prefix_len = network.prefixlen
        
        return best_match
    except:
        return None

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
    
    # Try to use radix tree first, fall back to alternative if not available
    try:
        rtree = load_prefix_to_as_mapping_optimized(prefix_2_as_file)
        
        # Use multiprocessing with shared radix tree
        with multiprocessing.Pool() as pool:
            args = [(folder, rtree) for folder in input_folders]
            pool.map(process_folder_optimized, args)
            
    except ImportError:
        print("py-radix not available, using alternative method...")
        sorted_prefixes = load_prefix_to_as_mapping_alternative(prefix_2_as_file)
        
        def process_folder_alternative(folder):
            path = os.path.join(directory, folder, 'final_filtered.txt')
            if not os.path.exists(path):
                print(f"File {path} does not exist, skipping...")
                return
            
            output_file = os.path.join(directory, folder, 'asn_list.txt')
            if os.path.exists(output_file):
                print(f"Output file {output_file} already exists, skipping...")
                return
            
            with open(path, 'r') as f:
                cidrs = [line.strip() for line in f if line.strip()]
            
            asn_set = set()
            print(f"Processing folder: {folder}, CIDRs found: {len(cidrs)}")
            
            for cidr in tqdm(cidrs, desc=f"Processing {folder}"):
                asn = get_asn_from_cidr_alternative(cidr, sorted_prefixes)
                if asn:
                    asn_set.add(asn)
            
            asn_list = list(asn_set)
            
            with open(output_file, 'w') as f:
                json.dump(asn_list, f)
            
            print(f"Processed {folder}: {len(asn_list)} ASNs found and saved to {output_file}")
        
        # Process folders sequentially for alternative method
        for folder in input_folders:
            process_folder_alternative(folder)

if __name__ == '__main__':
    main()

