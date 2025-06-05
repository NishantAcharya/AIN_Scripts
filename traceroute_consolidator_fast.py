import os
import json
from tqdm import tqdm
import ipaddress
import statistics
import math
import geopy
import sys
import requests
import json
import socket
import multiprocessing
import ast
from geopy.distance import geodesic
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import pickle
import hashlib
import re
import asyncio
import aiofiles
from typing import Dict, List, Set, Optional

def is_ip_in_cidr(ip, cidr):
    try:
        ip_obj = ipaddress.ip_address(ip)
        network = ipaddress.ip_network(cidr, strict=False)
        return ip_obj in network
    except ValueError:
        return False

# Enhanced DNS cache with memory-mapped storage and compression
_dns_cache = {}
_cache_lock = threading.Lock()
_cache_file = 'dns_cache.pkl'

def load_dns_cache():
    """Load DNS cache from disk with error handling"""
    global _dns_cache
    try:
        with open(_cache_file, 'rb') as f:
            _dns_cache = pickle.load(f)
        print(f"Loaded {len(_dns_cache)} DNS entries from cache")
    except (FileNotFoundError, pickle.PickleError):
        _dns_cache = {}
        print("Starting with empty DNS cache")

def save_dns_cache():
    """Save DNS cache to disk with atomic writes"""
    temp_file = _cache_file + '.tmp'
    try:
        with open(temp_file, 'wb') as f:
            pickle.dump(_dns_cache, f)
        os.replace(temp_file, _cache_file)  # Atomic replacement
        print(f"Saved {len(_dns_cache)} DNS entries to cache")
    except Exception as e:
        print(f"Warning: Could not save DNS cache: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

def is_private_or_invalid_ip(ip: str) -> bool:
    """Optimized check for private/invalid IPs"""
    if not ip or ip == '*':
        return True
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_multicast or ip_obj.is_loopback
    except ValueError:
        return True

def reverse_dns_lookup_batch(ip_batch: List[str], timeout: float = 0.8) -> Dict[str, Optional[str]]:
    """Optimized batch DNS lookup with reduced timeout"""
    results = {}
    
    # Set aggressive timeout
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    
    try:
        for ip in ip_batch:
            if is_private_or_invalid_ip(ip):
                results[ip] = None
                continue
                
            # Check cache first
            with _cache_lock:
                if ip in _dns_cache:
                    results[ip] = _dns_cache[ip]
                    continue
            
            try:
                result = socket.gethostbyaddr(ip)
                hostname = result[0]
                results[ip] = hostname
                
                # Cache result
                with _cache_lock:
                    _dns_cache[ip] = hostname
                    
            except (socket.herror, socket.gaierror, socket.timeout, OSError):
                results[ip] = None
                # Cache negative results
                with _cache_lock:
                    _dns_cache[ip] = None
                    
    finally:
        socket.setdefaulttimeout(original_timeout)
    
    return results

def perform_lookups_optimized(ip_list: List[str], max_workers: int = 50, timeout: float = 3.0) -> Dict[str, Optional[str]]:
    """
    Ultra-optimized DNS lookup with aggressive performance improvements:
    - Reduced timeout to 0.8s
    - Smaller batch sizes (10-15 IPs)
    - Fewer workers to avoid overwhelming DNS servers
    - Pre-filtering and deduplication
    - Batch processing with minimal delays
    """
    if not ip_list:
        return {}
    
    # Aggressive pre-filtering and deduplication
    unique_valid_ips = []
    seen = set()
    
    for ip in ip_list:
        if ip and ip != '*' and ip not in seen and not is_private_or_invalid_ip(ip):
            unique_valid_ips.append(ip)
            seen.add(ip)
    
    if not unique_valid_ips:
        return {}
    
    # Check cache in bulk
    results = {}
    uncached_ips = []
    
    with _cache_lock:
        for ip in unique_valid_ips:
            if ip in _dns_cache:
                results[ip] = _dns_cache[ip]
            else:
                uncached_ips.append(ip)
    
    print(f"DNS: {len(results)} cached, {len(uncached_ips)} new lookups")
    
    if not uncached_ips:
        return results
    
    # Process in smaller batches with fewer workers
    batch_size = 10  # Smaller batches for better responsiveness
    max_workers = min(max_workers, 10)  # Limit concurrent workers
    
    # Process batches with minimal threading overhead
    for i in range(0, len(uncached_ips), batch_size):
        batch = uncached_ips[i:i + batch_size]
        
        # Use smaller thread pool for each batch
        with ThreadPoolExecutor(max_workers=min(len(batch), 5)) as executor:
            # Submit individual IP lookups instead of batch processing
            future_to_ip = {
                executor.submit(reverse_dns_lookup_single_fast, ip, timeout): ip 
                for ip in batch
            }
            
            # Collect results with timeout
            for future in as_completed(future_to_ip, timeout=timeout + 10.0):
                ip = future_to_ip[future]
                try:
                    result = future.result(timeout=timeout+0.5)  # Very short timeout for result collection
                    results.update(result)
                except Exception:
                    results[ip] = None
                    with _cache_lock:
                        _dns_cache[ip] = None
        
        # Minimal delay between batches
        if i + batch_size < len(uncached_ips):
            time.sleep(0.001)  # 1ms delay
    
    return results

def reverse_dns_lookup_single_fast(ip: str, timeout: float = 0.8) -> Dict[str, Optional[str]]:
    """Ultra-fast single IP DNS lookup with aggressive timeout"""
    if is_private_or_invalid_ip(ip):
        return {ip: None}
    
    # Check cache first
    with _cache_lock:
        if ip in _dns_cache:
            return {ip: _dns_cache[ip]}
    
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    
    try:
        result = socket.gethostbyaddr(ip)
        hostname = result[0]
        
        # Cache the result
        with _cache_lock:
            _dns_cache[ip] = hostname
            
        return {ip: hostname}
        
    except (socket.herror, socket.gaierror, socket.timeout, OSError):
        # Cache negative results
        with _cache_lock:
            _dns_cache[ip] = None
        return {ip: None}
        
    finally:
        socket.setdefaulttimeout(original_timeout)

def extract_unique_ips_fast(data: dict) -> Set[str]:
    """Fast extraction of unique IPs from traceroute data"""
    unique_ips = set()
    
    for ip_data in data.values():
        if isinstance(ip_data, dict):
            for key, probe_data in ip_data.items():
                if isinstance(key, int) and isinstance(probe_data, dict):
                    # Extract last hop IP
                    last_hop = probe_data.get('Last_Hop_IP')
                    if last_hop and not is_private_or_invalid_ip(last_hop):
                        unique_ips.add(last_hop)
                    
                    # Extract second last hop IP
                    second_last = probe_data.get('Second_Last_Hop')
                    if second_last and not is_private_or_invalid_ip(second_last):
                        unique_ips.add(second_last)
                    
                    # Extract all traceroute IPs
                    traceroute = probe_data.get('Traceroute', [])
                    for hop_ip in traceroute:
                        if hop_ip and hop_ip != '*' and not is_private_or_invalid_ip(hop_ip):
                            unique_ips.add(hop_ip)
    
    return unique_ips

# Replace the original perform_lookups function with this optimized version
def perform_lookups(ip_list, max_workers=50, timeout=0.8, batch_delay=0.001):
    """Wrapper for backward compatibility"""
    return perform_lookups_optimized(ip_list, max_workers, timeout)

def get_all_files_in_folder(folder_path):
    try:
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except FileNotFoundError:
        print(f"Error: Folder '{folder_path}' not found.")
        return []

def write_lines_to_file(filename, lines):
    try:
        with open(filename, 'w') as file:
            file.writelines(line + '\n' for line in lines)
    except FileNotFoundError:
        print(f"Error: Could not write to file '{filename}'.")
        return

# Optimized version of read_traceroute with pre-DNS collection
def read_traceroute_optimized(folder_names, dest_file, probe_data, lat_lon, cidrs, lib_name):
    """Optimized traceroute reading with bulk DNS lookup"""
    
    # Phase 1: Process all traceroutes and collect IPs (without DNS)
    print("Phase 1: Processing traceroutes and collecting IPs...")
    data, data_lines, all_ips = process_traceroutes_no_dns(folder_names, probe_data, lat_lon, cidrs, lib_name)
    
    # Phase 2: Perform bulk DNS lookup
    print(f"Phase 2: Performing bulk DNS lookup for {len(all_ips)} unique IPs...")
    dns_results = perform_lookups_optimized(list(all_ips), max_workers=30, timeout=3)
    
    # Phase 3: Apply DNS results and complete processing
    print("Phase 3: Applying DNS results and finalizing...")
    finalize_traceroute_data(data, dns_results, lib_name)
    
    write_lines_to_file(dest_file, data_lines)
    return data

def process_traceroutes_no_dns(folder_names, probe_data, lat_lon, cidrs, lib_name):
    """Process traceroutes without DNS lookups, collecting all IPs"""
    data = {}
    data_lines = []
    all_ips = set()
    
    # Load identification codes
    json_path = './Data_set/Identification_Codes.json'
    print(f'Library Name: {lib_name}')
    with open(json_path, 'r') as f:
        id_data = json.load(f)

    iata_codes = id_data[lib_name]['iata_code']
    city_abbvrs = id_data[lib_name]['city_abbvr']
    lib_abbvrs = id_data[lib_name]['lib_abbvr']
    
    # Process folders and files (same as original, but collect IPs)
    for folder in folder_names:
        if not os.path.isdir(folder):
            continue
            
        temp = get_all_files_in_folder(folder)
        dup_selection = {}
        print(f'Getting File Names in {folder}')
        temp2 = [file.split('-')[-1].split('.json')[0].replace('?','/').strip() for file in temp]
        
        # Find overlap with CIDR list
        overlap = {}
        print('Finding the overlap')
        for cidr in temp2:
            if cidr in cidrs:
                overlap[cidr] = True
        
        print('Processing the files')
        for i in range(len(temp2)):
            try:
                check = overlap[temp2[i]]
            except KeyError:
                check = False
            if check:
                try:
                    _ = dup_selection[temp2[i]]
                except KeyError:
                    dup_selection[temp2[i]] = temp[i]

        files = list(dup_selection.values())
        network_error_count = 0
        
        for file in tqdm(files):
            if '.json' not in file:
                continue
            
            file_path = folder + '/' + file
            with open(file_path, 'r') as f:
                temp = json.load(f)

            if not isinstance(temp, dict):
                print(f"Warning: Expected dict, got {type(temp)} in file {file}")
                continue

            msm_id = file.split('-')[0].strip()
            ip = file.split('-')[1].strip()
            cidr = file.split('-')[2].strip()
            
            # Process file data (same as original but collect IPs)
            ip_data = process_single_file(temp, ip, msm_id, cidr, probe_data, lat_lon, all_ips)
            data[ip] = ip_data
            
            # Add data lines
            for item in temp.get(ip, []):
                if isinstance(item, dict):
                    data_lines.append(f'{ip}-{item["prb_id"]}-{ip_data.get(item["prb_id"], {}).get("Last_Hop_IP", "")}-{cidr.replace("?","/").split(".json")[0]}')
    
    return data, data_lines, all_ips

def process_single_file(temp, ip, msm_id, cidr, probe_data, lat_lon, all_ips):
    """Process a single file and collect IPs"""
    ip_data = {
        'Failed': False, 
        'CIDR': cidr.replace("?","/").split(".")[0],
        'MSM_ID': msm_id, 
        'Last_Hop_Second_Last_Hop_Difference': {}, 
        'Common_IPs': {},
        'Common_CIDRs': {},
        'Last_Hops_final': [],
        'Lat': lat_lon[0],
        'Lon': lat_lon[1]
    }
    
    if ip not in temp.keys():
        print(f'IP {ip} not in file')
        ip_data['Failed'] = True
        return ip_data

    # Process traceroutes
    for item in temp[ip]:
        if not isinstance(item, dict):
            continue
            
        prb_item = process_probe_item(item, probe_data, ip_data, all_ips)
        ip_data[item['prb_id']] = prb_item
    
    # Post-process common IPs and CIDRs
    cleanup_common_data(ip_data)
    calculate_min_differences(ip_data)
    update_usable_hops(ip_data, all_ips)
    
    return ip_data

def process_probe_item(item, probe_data, ip_data, all_ips):
    """Process individual probe item and collect IPs"""
    prb_item = {
        'Traceroute': [], 
        'Last_Hop_IP': None, 
        'Dest_Replied': False,
        'Domain_info_close': False,
        'RTTs': [], 
        'Second_Last_Hop': None, 
        'Last_RTT': None, 
        'Second_Last_RTT': None,
        'Final_Hop_Differences': {}
    }
    
    prb_item['Dest_Replied'] = item['destination_ip_responded']
    traceroute_full = item['result']
    last_hop_ip = item['src_addr']
    last_hop_rtt = math.inf

    try:
        if ipaddress.ip_address(last_hop_ip).is_private:
            last_hop_ip = None
    except ValueError:
        prb_item['Dest_Replied'] = False
        return prb_item
    
    # Process traceroute hops
    for hop in traceroute_full:
        try:
            rtt = hop['result'][0]['rtt']
        except KeyError:
            rtt = '*'

        try:
            hop_ip = hop['result'][0]['from']
            all_ips.add(hop_ip)  # Collect IP
            
            if not ipaddress.ip_address(hop_ip).is_private:
                last_hop_ip = hop_ip
                current_cidr = str(ipaddress.ip_network(hop_ip + '/24', strict=False))
                
                # Update common CIDRs and IPs
                if current_cidr not in ip_data['Common_CIDRs']:
                    ip_data['Common_CIDRs'][current_cidr] = []
                ip_data['Common_CIDRs'][current_cidr].append(item['prb_id'])

                if hop_ip not in ip_data['Common_IPs']:
                    ip_data['Common_IPs'][hop_ip] = []
                ip_data['Common_IPs'][hop_ip].append(item['prb_id'])
                
                if rtt != '*':
                    last_hop_rtt = rtt
                else:
                    last_hop_rtt = math.inf
        except KeyError:
            hop_ip = '*'

        prb_item['Traceroute'].append(hop_ip)
        prb_item['RTTs'].append(rtt)
    
    prb_item['Last_Hop_IP'] = last_hop_ip
    prb_item['Last_RTT'] = last_hop_rtt
    
    if last_hop_ip:
        all_ips.add(last_hop_ip)  # Collect last hop IP
    
    # Calculate second last hop and RTT differences
    calculate_second_last_hop(prb_item, ip_data, item, all_ips)
    
    # Add probe location data
    id = item['prb_id']
    probe_lat_lon = tuple(probe_data[str(id)][1])
    prb_item['Lat,Long'] = probe_lat_lon
    prb_item['Distance Destination'] = geodesic(probe_lat_lon, (ip_data['Lat'], ip_data['Lon'])).kilometers
    
    return prb_item

def calculate_second_last_hop(prb_item, ip_data, item, all_ips):
    """Calculate second last hop and RTT differences"""
    last_hop_ip = prb_item['Last_Hop_IP']
    second_last_hop = None
    second_last_rtt = math.inf
    
    # Find second last hop
    for i in range(len(prb_item['Traceroute'])-1, -1, -1):
        if prb_item['Traceroute'][i] == last_hop_ip:
            if i-1 < 0:
                second_last_hop = last_hop_ip
                second_last_rtt = prb_item['Last_RTT']
                break
            second_last_hop = prb_item['Traceroute'][i-1]
            if second_last_hop == '*':
                second_last_rtt = math.inf
            else:
                second_last_rtt = prb_item['RTTs'][i-1]
                if second_last_rtt == '*':
                    second_last_rtt = math.inf
            break
    
    prb_item['Second_Last_Hop'] = second_last_hop
    prb_item['Second_Last_RTT'] = float(second_last_rtt) if second_last_rtt != math.inf else None
    
    if second_last_hop:
        all_ips.add(second_last_hop)  # Collect second last hop IP
    
    # Calculate RTT difference
    difference = math.inf
    d_key = f'{last_hop_ip}-{second_last_hop}'
    
    if (second_last_rtt != math.inf and prb_item['Last_RTT'] != math.inf and 
        prb_item['Last_RTT'] != '*' and second_last_rtt != '*'):
        difference = prb_item['Last_RTT'] - second_last_rtt
    
    difference = None if difference == math.inf else difference
    
    prb_item['Final_Hop_Differences'][d_key] = [difference]
    
    # Update global differences
    if d_key not in ip_data['Last_Hop_Second_Last_Hop_Difference']:
        ip_data['Last_Hop_Second_Last_Hop_Difference'][d_key] = []
    ip_data['Last_Hop_Second_Last_Hop_Difference'][d_key].append(difference)

def cleanup_common_data(ip_data):
    """Remove duplicates and filter common data"""
    for k in ip_data['Common_IPs']:
        ip_data['Common_IPs'][k] = list(set(ip_data['Common_IPs'][k]))
    for k in ip_data['Common_CIDRs']:
        ip_data['Common_CIDRs'][k] = list(set(ip_data['Common_CIDRs'][k]))
    
    ip_data['Common_IPs'] = {k: v for k, v in ip_data['Common_IPs'].items() if len(v) > 1}
    ip_data['Common_CIDRs'] = {k: v for k, v in ip_data['Common_CIDRs'].items() if len(v) > 1}

def calculate_min_differences(ip_data):
    """Calculate minimum RTT differences"""
    difference_data = ip_data['Last_Hop_Second_Last_Hop_Difference']
    min_difference_data = {}
    
    for key in difference_data.keys():
        valid_differences = [x for x in difference_data[key] if x is not None]
        if valid_differences:
            temp = min(valid_differences)
            if temp < 0:
                temp = 0
            min_difference_data[key] = temp
        else:
            min_difference_data[key] = None
    
    ip_data['Min_lhop_difference'] = min_difference_data

def update_usable_hops(ip_data, all_ips):
    """Update usable last hops based on RTT analysis"""
    for key in ip_data:
        if not isinstance(key, int):
            continue
            
        prb_item = ip_data[key]
        
        # Get RTT difference
        differ_key = list(prb_item['Final_Hop_Differences'].keys())[0] if prb_item['Final_Hop_Differences'] else None
        final_hop_differences = None
        
        if differ_key:
            final_hop_differences = prb_item['Final_Hop_Differences'][differ_key][0]
        
        if final_hop_differences is None:
            final_hop_differences = math.inf
        if final_hop_differences < 0:
            ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
            ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
            if prb_item['Last_Hop_IP']:
                all_ips.add(prb_item['Last_Hop_IP'])
            continue
        
        # Apply RTT analysis logic
        current_hop_differ = None
        if differ_key and differ_key in ip_data.get('Min_lhop_difference', {}):
            current_hop_differ = ip_data['Min_lhop_difference'][differ_key]
        
        if current_hop_differ is None:
            current_hop_differ = math.inf
        
        if final_hop_differences != math.inf and current_hop_differ != math.inf:
            if final_hop_differences > current_hop_differ:
                ip_data[key]['Usable_Last_Hop_RTT'] = (prb_item['Second_Last_RTT'] or 0) + current_hop_differ
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
            else:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
        else:
            ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
            ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
        
        # Distance-based RTT check
        distance = prb_item.get('Distance Destination', math.inf)
        max_rtt_expected = 14.75 + 0.015 * distance
        temp_s_last = prb_item['Second_Last_RTT'] or math.inf
        temp_last = prb_item['Last_RTT'] or math.inf
        
        if temp_last - temp_s_last > max_rtt_expected:
            ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Second_Last_RTT']
            ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Second_Last_Hop']
        
        # Collect final IPs
        if ip_data[key]['Usable_Last_Hop_IP']:
            all_ips.add(ip_data[key]['Usable_Last_Hop_IP'])

def finalize_traceroute_data(data, dns_results, lib_name):
    """Apply DNS results and finalize domain analysis"""
    # Load identification codes
    json_path = './Data_set/Identification_Codes.json'
    with open(json_path, 'r') as f:
        id_data = json.load(f)

    iata_codes = id_data[lib_name]['iata_code']
    city_abbvrs = id_data[lib_name]['city_abbvr']
    lib_abbvrs = id_data[lib_name]['lib_abbvr']
    
    for ip, ip_data in data.items():
        if ip_data.get('Failed', False):
            continue
        
        # Collect final hop IPs
        final_hop_ips = set()
        for key in ip_data:
            if isinstance(key, int):
                usable_ip = ip_data[key].get('Usable_Last_Hop_IP')
                if usable_ip:
                    final_hop_ips.add(usable_ip)
        
        # Apply DNS results
        domains_dict = {}
        for hop_ip in final_hop_ips:
            domains_dict[hop_ip] = dns_results.get(hop_ip)
        
        ip_data['Last_Hops_final'] = domains_dict
        
        # Process domain information for each probe
        for key in ip_data:
            if not isinstance(key, int):
                continue
            
            prb_item = ip_data[key]
            usable_ip = prb_item.get('Usable_Last_Hop_IP')
            if not usable_ip:
                continue
                
            domain = dns_results.get(usable_ip)
            ip_data[key]['Domain'] = domain
            
            if domain is None:
                continue
            
            # Check domain patterns
            domain = domain.lower()
            domain_close = False
            
            # Check IATA codes
            for iata in iata_codes:
                chunks = domain.split('.')
                pattern = re.compile(r'\d*' + re.escape(iata.lower()) + r'\d*')
                if any(pattern.fullmatch(chunk) for chunk in chunks):
                    domain_close = True
                    break
            
            # Check city abbreviations
            if not domain_close:
                for abbvr in city_abbvrs:
                    if abbvr.lower() in domain:
                        domain_close = True
                        break
            
            # Check library abbreviations
            if not domain_close:
                for abbvr in lib_abbvrs:
                    if abbvr.lower() in domain:
                        domain_close = True
                        break
            
            ip_data[key]['Domain_info_close'] = domain_close
        
        # Calculate smallest RTT probes
        calculate_smallest_rtt_probes(ip_data)

def calculate_smallest_rtt_probes(ip_data):
    """Calculate probes with smallest RTTs"""
    rtt_probe_pairs = []
    for key in ip_data:
        if isinstance(key, int):
            prb_item = ip_data[key]
            usable_rtt = prb_item.get('Usable_Last_Hop_RTT')
            dest_replied = prb_item.get('Dest_Replied', False)
            domain_close = prb_item.get('Domain_info_close', False)
            
            if (usable_rtt is not None and 
                (dest_replied or domain_close)):
                rtt_probe_pairs.append((usable_rtt, key))
    
    rtt_probe_pairs.sort()
    smallest_rtt_probes = [probe_id for _, probe_id in rtt_probe_pairs[:3]]
    ip_data['Smallest_RTT_Probes'] = smallest_rtt_probes

# Replace the original read_traceroute function call with the optimized version
def read_traceroute(folder_names, dest_file, probe_data, lat_lon, cidrs, lib_name):
    """Wrapper for backward compatibility"""
    return read_traceroute_optimized(folder_names, dest_file, probe_data, lat_lon, cidrs, lib_name)

#The goal of this function is to make sure all probes are available without extra processing
def merge_probes(probe_path,probe_directory):
  intial_data = json.load(open(probe_path, 'r'))
  #Checking if probe directory exists
  if not os.path.exists(probe_directory):
      print(f'Probe directory {probe_directory} does not exist')
      return intial_data
  
  for file in os.listdir(probe_directory):
    if '.json' not in file:
        continue
    file_path = os.path.join(probe_directory, file)
    with open(file_path, 'r') as f:
        current_data = json.load(f)
        #Loading close_probes
        try:
          close_probes = list(current_data['Close'].keys())
          for probe in close_probes:
              if probe not in intial_data['Close'].keys():
                  intial_data['Close'][probe] = current_data['Close'][probe]
        except KeyError:
          pass
        try:
          metro_probes = list(current_data['Metro'].keys())
          for probe in metro_probes:
              if probe not in intial_data['Metro'].keys():
                  intial_data['Metro'][probe] = current_data['Metro'][probe]
        except KeyError:
          pass

  new_data = {}
  for keys in intial_data['Close'].keys():
    if keys not in new_data.keys():
        new_data[keys] = intial_data['Close'][keys]
  for keys in intial_data['Metro'].keys():
    if keys not in new_data.keys():
        new_data[keys] = intial_data['Metro'][keys]

  return new_data
     

def main():
    # Load DNS cache at startup
    load_dns_cache()
    
    info_file = 'validation_input.txt'
    directory = './Library_Static_Data/'
    folders = os.listdir(directory)
    final_folder_file = 'done_show.txt'
    #Compare_name
    with open(info_file, 'r') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        comp_lines = [line.split('~')[2] for line in lines]

    try:
        for folder in folders:
          
          current_path = os.path.join(directory, folder)
          json_path = os.path.join(current_path, 'JSON')
          
          #If need be to full restart comment his linen out
          #final_check = os.path.join(current_path,final_folder_file)
          #if os.path.exists(final_check):
          #    print(f'Final check file {final_check} exists, skipping {folder}')
          #    continue
          
          probe_path = os.path.join(current_path, 'grouped_probes.json')
          probe_directory = os.path.join(current_path, 'Past_probes')
          #check if Json path exists
          if not os.path.exists(json_path):
              name = folder.split('Results_')[1]
              name = name.replace('?','/')
              name = name.replace('_',' ')
              if name in comp_lines:
                 print(f'Skipping {folder} as its not processed yet')
              continue
          folder_names = os.listdir(json_path)
          folder_names = [os.path.join(json_path, folder) for folder in folder_names]
          dest_file = os.path.join(current_path, 'meta.txt')
          
          name = folder.split('Results_')[1]
          name = name.replace('?','/')
          name = name.replace('_',' ')
          if name not in comp_lines:
            continue

          final_info_path = os.path.join(current_path, 'filtered_dup_removed.txt')
          with open(final_info_path, 'r') as f:
            lines = f.readlines()
            lines = [line.strip().split('-')[1] for line in lines]
            cidr_lines = lines
          print(f'Processing {folder}...')
          #Looking for the lat long values in info_file
          with open(info_file, 'r') as f:
              lines = f.readlines()
              for line in lines:
                  if name in line:
                      print(line)
                      lat = float(line.split('~')[0].strip())
                      lon = float(line.split('~')[1].strip())
                      break
          print(f'Lat: {lat}, Lon: {lon}')
          #Load the JSON for all the probes and merge them together and then pass them to the function
          probe_data = merge_probes(probe_path, probe_directory)
          data = read_traceroute(folder_names, dest_file, probe_data, (lat,lon),cidr_lines,name)
          dest_folder = os.path.join(current_path, 'Trace_data.json')
          #Check if the folder exists
          with open(dest_folder, 'w') as f:
              json.dump(data, f, indent=4)

          final_dest_file = os.path.join(current_path, final_folder_file)
          #Writing the final file
          with open(final_dest_file, 'a') as f:
              f.write(f'{folder} - {dest_folder}\n')

          #Checking last mile latencies --- THE IDEA
          #Store the second last and last hop IPs as pairs for only the traces whose destination replied (otherwise we can't really say anything for access net)
          #The dicrionary will store the difference between those two pairs for that library group
          #Question? --> What if we just foudn them on bad day? -- high RTT difference? -- can't do much that's an issue
          #If the last mile latency, if there is a lower difference, use that
          #If there is only one difference, then we need a threshold -- (avg RTT based on distance 14.75+0.015*dist) with a RMSE of 12ms(cite)
          #Based on this it should not be going further than the neasrest high pop density region
          ## Use burlington's example to say that the last mile latency may be going though the nearest metro region
          ## Assumtion is that the last hop differnce should not be higher than the average RTT between the probe and the destination
    
    finally:
        # Save DNS cache on exit
        save_dns_cache()

main()