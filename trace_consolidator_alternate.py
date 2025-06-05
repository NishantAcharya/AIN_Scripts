#Need a piece of code that consolidates the tracesrutes for each IP, multipe IPs will be in another set under it
# {Dest IP: Probe ID: {Traceroute: [Hops], last hop ip, pings: [], bdrmapit ASes:[], Direct AS Path:[]}}}
#Need a text file that has 1 line in the format : Dest IP -- Probe ID -- Last hop IP#

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
from concurrent.futures import ThreadPoolExecutor
import threading
import pickle
import hashlib
import re

def is_ip_in_cidr(ip, cidr):
  try:
    ip_obj = ipaddress.ip_address(ip)
    network = ipaddress.ip_network(cidr, strict=False)
    return ip_obj in network
  except ValueError:
    return False

# Persistent DNS cache to avoid repeated lookups across runs
_dns_cache = {}
_cache_lock = threading.Lock()
_cache_file = 'dns_cache.pkl'

def load_dns_cache():
    """Load DNS cache from disk"""
    global _dns_cache
    try:
        with open(_cache_file, 'rb') as f:
            _dns_cache = pickle.load(f)
        print(f"Loaded {len(_dns_cache)} DNS entries from cache")
    except (FileNotFoundError, pickle.PickleError):
        _dns_cache = {}
        print("Starting with empty DNS cache")

def save_dns_cache():
    """Save DNS cache to disk"""
    try:
        with open(_cache_file, 'wb') as f:
            pickle.dump(_dns_cache, f)
        print(f"Saved {len(_dns_cache)} DNS entries to cache")
    except Exception as e:
        print(f"Warning: Could not save DNS cache: {e}")

def is_private_or_invalid_ip(ip):
    """Quick check for private/invalid IPs to skip DNS lookup"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_multicast
    except ValueError:
        return True

def reverse_dns_lookup_single(ip, timeout=1.5):
    """Single IP reverse DNS lookup with caching and ultra-short timeout"""
    # Skip private/invalid IPs
    if is_private_or_invalid_ip(ip):
        return {ip: None}
    
    # Check cache first
    with _cache_lock:
        if ip in _dns_cache:
            return {ip: _dns_cache[ip]}
    
    try:
        # Set socket timeout for DNS lookup
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        
        result = socket.gethostbyaddr(ip)
        hostname = result[0]
        
        # Cache the result
        with _cache_lock:
            _dns_cache[ip] = hostname
            
        return {ip: hostname}
    except:
        # Cache negative results too
        with _cache_lock:
            _dns_cache[ip] = None
        return {ip: None}
    finally:
        # Restore original timeout
        socket.setdefaulttimeout(old_timeout)

def perform_lookups(ip_list, max_workers=1000, timeout=2, batch_delay=0.005):
    """
    Ultra-optimized reverse DNS lookup with multiple strategies to avoid blocking:
    - Persistent caching across runs
    - Skip private/invalid IPs
    - Reduced timeout (1.5s)
    - Small batch sizes (15) with micro-delays
    - Rate limiting to be DNS-friendly
    - Progress tracking
    """
    if not ip_list:
        return {}
    
    # Remove duplicates and filter out private IPs
    unique_ips = []
    seen = set()
    for ip in ip_list:
        if ip not in seen and not is_private_or_invalid_ip(ip):
            unique_ips.append(ip)
            seen.add(ip)
    
    # Check cache first for all IPs
    results = {}
    uncached_ips = []
    
    with _cache_lock:
        for ip in unique_ips:
            if ip in _dns_cache:
                results[ip] = _dns_cache[ip]
            else:
                uncached_ips.append(ip)
    
    #print(f"DNS: {len(results)} cached, {len(uncached_ips)} new lookups from {len(ip_list)} total IPs")
    
    if not uncached_ips:
        return results
    
    # Process uncached IPs in small batches to be DNS-friendly
    #batch_size = min(max_workers, 20)  # Even smaller batches
    batch_size = max_workers
    
    #with tqdm(total=len(uncached_ips), desc="DNS Lookups", unit="IPs") as pbar:
    for i in range(0, len(uncached_ips), batch_size):
        batch = uncached_ips[i:i + batch_size]
        
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            # Submit batch tasks
            future_to_ip = {
                executor.submit(reverse_dns_lookup_single, ip, timeout): ip 
                for ip in batch
            }
            
            # Collect results as they complete
            for future in future_to_ip:
                try:
                    result = future.result(timeout=timeout + 0.5)
                    results.update(result)
                except Exception as e:
                    ip = future_to_ip[future]
                    results[ip] = None
                    # Cache negative result
                    with _cache_lock:
                        _dns_cache[ip] = None
                
                #pbar.update(1)
        
        # Micro-delay between batches to be DNS-friendly
        if i + batch_size < len(uncached_ips):
                time.sleep(batch_delay)
    
    return results


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

#This function will read a traceroute and get the IPs in a traceroute, given the a folder_set with the trace data
#,probe_path, lat_lon
def read_traceroute(folder_names, dest_file, probe_data, lat_lon,cidrs,lib_name):
    data = {}
    data_lines = []
    folder_count = 0
    weird_count = 0
    data_count = 0
    ips_t = set()
    dup_selection = {}
    #This is a temp solution to hoiho being down
    json_path = './Data_set/Identification_Codes.json'

    print(f'Library Name: {lib_name}')
    with open(json_path, 'r') as f:
        id_data = json.load(f)

    iata_codes = id_data[lib_name]['iata_code']
    city_abbvrs = id_data[lib_name]['city_abbvr']
    lib_abbvrs = id_data[lib_name]['lib_abbvr']
    ##


    for folder in folder_names:
        #Walking through files in the folder
        #Will check if the current file IP is in the CIDR list

        #If the it's not a folder, skip it
        if not os.path.isdir(folder):
          continue
        temp = get_all_files_in_folder(folder)
        dup_selection = {}
        print(f'Getting File Names in {folder}')
        temp2 = [file.split('-')[-1].split('.json')[0].replace('?','/').strip() for file in temp]
        #find overlap with the CIDR list
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
                #Check if the CIDR is already in the list
                try:
                    _ = dup_selection[temp2[i]]
                except KeyError:
                    dup_selection[temp2[i]] = temp[i]

        files = list(dup_selection.values())
        network_error_count = 0
        for file in tqdm(files):
            folder_count += 1
            if '.json' not in file:
                weird_count += 1
            
            file_path = folder+'/'+file
            with open(file_path, 'r') as f:
               temp = json.load(f)

            if not isinstance(temp, dict):
                print(f"Warning: Expected dict, got {type(temp)} in file {file}")
                continue

            msm_id = file.split('-')[0].strip()
            ip = file.split('-')[1].strip()
            #Remove later
            ips_t.add(ip)
            cidr = file.split('-')[2].strip()
            
            ip_data = {'Failed': False, 'CIDR' :cidr.replace("?","/").split(".")[0],'MSM_ID': msm_id, 'Last_Hop_Second_Last_Hop_Difference':{}, 'Common_IPs':{}, 'Common_CIDRs':{},'Last_Hops_final':[]}
            ip_data['Lat'] = lat_lon[0]
            ip_data['Lon'] = lat_lon[1]
            if ip not in temp.keys():
               print(f'IP {ip} not in file {file}')
               ip_data['Failed'] = True
               data[ip] = ip_data
               continue

            #Getting the traceroutes and last_hop_ip per prb
            for item in temp[ip]:
                if not isinstance(item, dict):
                    print(f"Warning: Expected dict, got {type(item)}: {item}")
                    continue
                prb_item = {'Traceroute':[], 'Last_Hop_IP':None, 'Dest_Replied':False, 'Domain_info_close': False,'RTTs':[], 'Second_Last_Hop':None, 'Last_RTT':None, 'Second_Last_RTT':None,'Final_Hop_Differences':{}}
                prb_item['Dest_Replied'] = item['destination_ip_responded']
                traceroute_full = item['result']
                last_hop_ip = item['src_addr'] #Start with the source address
                last_hop_rtt = math.inf

                try:
                  if ipaddress.ip_address(last_hop_ip).is_private:
                      last_hop_ip = None
                except ValueError:
                   network_error_count += 1
                   prb_item['Dest_Replied'] = False
                   ip_data['Failed'] = True
                   ip_data[item['prb_id']] = prb_item
                   continue
                  
                for hop in traceroute_full:
                    try:
                        rtt = hop['result'][0]['rtt']
                    except KeyError:
                        rtt = '*'

                    try:
                        hop_ip = hop['result'][0]['from'] #Single ping traceroute, for more scan the full list
                        if not ipaddress.ip_address(hop_ip).is_private:
                            last_hop_ip = hop_ip
                            current_cidr = str(ipaddress.ip_network(hop_ip + '/24', strict=False))
                            # Finding common CIDRs and IPs in the traceroute
                            try:
                              temp = ip_data['Common_CIDRs'][str(current_cidr)]
                            except KeyError:
                              ip_data['Common_CIDRs'][current_cidr] = []

                            ip_data['Common_CIDRs'][current_cidr].append(item['prb_id'])

                            try:
                              temp = ip_data['Common_IPs'][hop_ip]
                            except KeyError:
                              ip_data['Common_IPs'][hop_ip] = []
                            ip_data['Common_IPs'][hop_ip].append(item['prb_id'])
                            #############
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
                #Finding the second last hop IP
                second_last_hop = None
                second_last_rtt = math.inf
                for i in range(len(prb_item['Traceroute'])-1, -1, -1):
                    if prb_item['Traceroute'][i] == last_hop_ip:
                      if i-1 < 0: #Only one hop found -- we will get a difference of 0
                        second_last_hop = last_hop_ip
                        second_last_rtt = last_hop_rtt
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
                prb_item['Second_Last_RTT'] = float(second_last_rtt)
                
                #Saving RTT differences between the final two hops -- slightly crude since we don't check for full networks
                difference = math.inf
                
                d_key = f'{last_hop_ip}-{second_last_hop}'
                if second_last_rtt != math.inf and last_hop_rtt != math.inf:
                  if last_hop_rtt == '*':
                    last_hop_rtt = math.inf
                  if second_last_rtt == '*':
                    second_last_rtt = math.inf
                  difference = last_hop_rtt - second_last_rtt

                
                #Cleaning -- no math.inf -- changed to None
                if difference == math.inf:
                  difference = None
                
                if second_last_rtt == math.inf:
                  prb_item['Second_Last_RTT'] = None

                if last_hop_rtt == math.inf:
                  prb_item['Last_RTT'] = None
                
                try:
                  temp = prb_item['Final_Hop_Differences'][d_key]
                except KeyError:
                  prb_item['Final_Hop_Differences'][d_key] = []
                prb_item['Final_Hop_Differences'][d_key].append(difference)

                id = item['prb_id']
                if str(id) not in probe_data:
                    #print(f"Warning: Probe ID {id} not found in probe_data. Skipping.")
                    continue
                probe_lat_lon = tuple(probe_data[str(id)][1])
                prb_item['Lat,Long'] = probe_lat_lon
                # Calculate the distance between the probe and the destination
                prb_item['Distance Destination'] = geodesic(probe_lat_lon, (lat_lon[0], lat_lon[1])).kilometers

                
                  
                ip_data[item['prb_id']] = prb_item
                
                #Consolidating the final differences
                for entry in prb_item['Final_Hop_Differences'].keys():
                  try:
                    temp = ip_data['Last_Hop_Second_Last_Hop_Difference'][entry]
                  except KeyError:
                    ip_data['Last_Hop_Second_Last_Hop_Difference'][entry] = []

                  ip_data['Last_Hop_Second_Last_Hop_Difference'][entry].extend(prb_item['Final_Hop_Differences'][entry])


                #Adding the file lines
                data_lines.append(f'{ip}-{item["prb_id"]}-{last_hop_ip}-{cidr.replace("?","/").split(".json")[0]}')
            
            data[ip] = ip_data
            data_count += 1
            # Remove duplicates from the lists in Common_IPs and Common_CIDRs
            for k in ip_data['Common_IPs']:
                ip_data['Common_IPs'][k] = list(set(ip_data['Common_IPs'][k]))
            for k in ip_data['Common_CIDRs']:
                ip_data['Common_CIDRs'][k] = list(set(ip_data['Common_CIDRs'][k]))
            
            # Remove items from Common_IPs and Common_CIDRs with len(values) <= 1
            ip_data['Common_IPs'] = {k: v for k, v in ip_data['Common_IPs'].items() if len(v) > 1}
            ip_data['Common_CIDRs'] = {k: v for k, v in ip_data['Common_CIDRs'].items() if len(v) > 1}

            #Find the lowest +ve RTT difference for each last hop - second last hop pair, apply that to the final hop rtt
            #If only 1 then, check if over avg RTT between prbe and destination, if yes, use the second last hop RTT
            difference_data = ip_data['Last_Hop_Second_Last_Hop_Difference']
            min_difference_data = {}
            for key in difference_data.keys():
                valid_differences = [x for x in difference_data[key] if x is not None]
                if valid_differences:
                    temp = min(valid_differences)
                    if temp < 0:
                        temp = 0
                    min_difference_data[key] = temp #The idea is to make sure that if the difference is less than 0, there is no difference
                else:
                    #print(f"Warning: No valid differences for key {key}. Setting to None.")
                    min_difference_data[key] = None  # Or set a default value, e.g., `math.inf`
            
            ip_data['Min_lhop_difference'] = min_difference_data


            #Going over the probes, and updating the usable_last hop IP
            #If the difference is more than distance*0.001 + 14.75, then use the second last hop RTT
            for key in ip_data:
              
              if type(key) != int:
                continue
              prb_item = ip_data[key]

              try:
                differ_key = list(prb_item['Final_Hop_Differences'].keys())[0]
                final_hop_differences = prb_item['Final_Hop_Differences'][differ_key][0] # Only 1 value will be here, maybe update in Future?
              except:
                final_hop_differences = None
              if final_hop_differences is None:
                 final_hop_differences = math.inf #None happens when math.inf happens
              if final_hop_differences < 0:
                #Negative ones are avoided
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
                ip_data['Last_Hops_final'].append(ip_data[key]['Usable_Last_Hop_IP'])
                continue
              ############### Checking if the last hop difference is less than the second last hop difference
              try:
                current_hop_differ = ip_data['Min_lhop_difference'][differ_key]
              except KeyError:
                current_hop_differ = None
              if current_hop_differ is None:
                current_hop_differ = math.inf #None happens when math.inf happens
              
              if final_hop_differences != math.inf and current_hop_differ != math.inf:
                if final_hop_differences > current_hop_differ:
                  ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Second_Last_RTT'] + current_hop_differ
                  ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
                else:
                  ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                  ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
              else:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']

              #Checking if second last RTT difference is massively smaller than last RTT
              try:
                distance = prb_item['Distance Destination']
              except KeyError:
                 distance = math.inf
              max_rtt_expected = 14.75 + 0.015 * distance
              temp_s_last = prb_item['Second_Last_RTT']
              temp_last = prb_item['Last_RTT']
              if temp_s_last is None:
                temp_s_last = math.inf
              if temp_last is None:
                temp_last = math.inf
              try:
                comp_rtt = temp_last - temp_s_last
              except:
                 print(f"Error: {temp_last} - {temp_s_last}")
                 raise Exception("Error: RTT calculation failed")
              if comp_rtt is None:
                comp_rtt = math.inf
              if comp_rtt > max_rtt_expected:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Second_Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Second_Last_Hop']
              
              ip_data['Last_Hops_final'].append(ip_data[key]['Usable_Last_Hop_IP'])
              
            #Calculate the rdns of the last hop IPs, then do a hoiho reuqest and map the lat,long to domain to probe
            #If the distance beween the lat,long (this and library) is closer than 40 Km, update the geoloc boolean
            ip_data['Last_Hops_final'] = list(set(ip_data['Last_Hops_final']))
            try:
              domains_dict = perform_lookups(ip_data['Last_Hops_final'])
            except Exception as e:
              print(f"Error during reverse DNS lookup: {e}")
              domains_dict = {}
            

            domain_list = []
            for ip in ip_data['Last_Hops_final']:
                domain = domains_dict.get(ip)
                if domain is not None:
                    domain_list.append(domain)
                else:
                    domain_list.append('*')  # Placeholder for no domain found
            #Not needed after this
            ip_data['Last_Hops_final'] = domains_dict
            for key in ip_data:
              if type(key) != int:
                  continue
              
              prb_item = ip_data[key]
              domain = domains_dict.get(prb_item['Usable_Last_Hop_IP'])
              ip_data[key]['Domain'] = domain
              if domain is None:
                  continue
              
              domain = domain.lower()
              for iata in iata_codes:
                chunks = domain.split('.')
                pattern = re.compile(r'\d*' + re.escape(iata.lower()) + r'\d*')
                if any(pattern.fullmatch(chunk) for chunk in chunks):
                  #print(f"Found IATA code {iata} in domain {domain} for probe {key}")
                  ip_data[key]['Domain_info_close'] = True
                  break
              
              #These not following the above pattern due to haveing more info
              if not ip_data[key].get('Domain_info_close', False):
                  for abbvr in city_abbvrs:
                      if abbvr.lower() in domain:
                          #print(f"Found city abbreviation {abbvr} in domain {domain} for probe {key}")
                          ip_data[key]['Domain_info_close'] = True
                          break
                      
              if not ip_data[key].get('Domain_info_close', False):
                  for abbvr in lib_abbvrs:
                      if abbvr.lower() in domain:
                          #print(f"Found library abbreviation {abbvr} in domain {domain} for probe {key}")
                          ip_data[key]['Domain_info_close'] = True
                          break
                


            #Get the smallest rtt probes
            smallest_rtt_probes = []
            # Find the probes with the three lowest RTTs
            rtt_probe_pairs = []
            for key in ip_data:
              if isinstance(key, int):  # Ensure the key is a probe ID
                prb_item = ip_data[key]
                try:
                  if prb_item['Usable_Last_Hop_RTT'] is not None and (prb_item['Dest_Replied'] == True or prb_item['Domain_info_close'] == True):
                    rtt_probe_pairs.append((prb_item['Usable_Last_Hop_RTT'], key))
                except KeyError:
                   print(prb_item.keys())
                   raise Exception("KeyError: Usable_Last_Hop_RTT not found")
            
            # Sort by RTT and take the three lowest
            rtt_probe_pairs.sort()
            smallest_rtt_probes = [probe_id for _, probe_id in rtt_probe_pairs[:3]]
            ip_data['Smallest_RTT_Probes'] = smallest_rtt_probes
      
    write_lines_to_file(dest_file, data_lines)
    print(f'Network Errors: {network_error_count}')
    print(f'Folder Count: {folder_count}')
    print(f'Weird Count: {weird_count}')
    print(f'Data Count: {data_count}')
    print(f'IPs: {len(ips_t)}')#Some IPs are overlapping from the original CIDRs sepration -- probably due to there being a /28 and a /26
    #From two datasets
    return data

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