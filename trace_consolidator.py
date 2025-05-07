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

def reverse_dns_lookup(ip):
    try:
        result = socket.gethostbyaddr(ip)
        return {ip: result[0]}  # Return the hostname
    except:
        return {ip: None}  # Return None if no hostname is found
    
def perform_lookups(ip_list):
    with multiprocessing.Pool() as pool:
        results = pool.map(reverse_dns_lookup, ip_list)
    return dict(item for result in results for item in result.items())


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
def read_traceroute(folder_names, dest_file, probe_data, lat_lon):
    data = {}
    data_lines = []
    folder_count = 0
    weird_count = 0
    data_count = 0
    ips_t = set()
    for folder in folder_names:
        #Walking through files in the folder
        files = get_all_files_in_folder(folder)
        network_error_count = 0
        for file in tqdm(files):
            folder_count += 1
            if '.json' not in file:
                weird_count += 1
                continue
            
            file_path = folder+'/'+file
            with open(file_path, 'r') as f:
               temp = json.load(f)

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
                #The probes update every day so we will have to update this everyday too
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
                      break
                prb_item['Second_Last_Hop'] = second_last_hop
                prb_item['Second_Last_RTT'] = second_last_rtt
                
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
                  item = prb_item['Final_Hop_Differences'][d_key]
                except KeyError:
                  prb_item['Final_Hop_Differences'][d_key] = []
                prb_item['Final_Hop_Differences'][d_key].append(difference)

                id = item['prb_id']
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
                if len(difference_data[key]) == 1:
                    min_difference_data[key] = difference_data[key][0]
                else:
                    min_difference_data[key] = min([x for x in difference_data[key] if x is not None and x > 0])
            ip_data['Min_lhop_difference'] = min_difference_data


            #Going over the probes, and updating the usable_last hop IP
            #If the difference is more than distance*0.001 + 14.75, then use the second last hop RTT
            for key in ip_data:
              if type(key) != int:
                continue
              prb_item = ip_data[key]
              differ_key = list(prb_item['Final_Hop_Differences'].keys())[0]
              final_hop_differences = prb_item['Final_Hop_Differences'][differ_key][0] # Only 1 value will be here, maybe update in Future?
              if final_hop_differences < 0:
                #Negative ones are avoided
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
                continue
              current_hop_differ = ip_data['Min_lhop_difference'][differ_key]
              if final_hop_differences > current_hop_differ:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Second_Last_RTT'] + current_hop_differ
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']
              else:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Last_Hop_IP']

              #Checking if second last RTT is massively smaller than last RTT
              distance = prb_item['Distance Destination']
              max_rtt_expected = 14.75 + 0.015 * distance
              if prb_item['Usable_Last_Hop_RTT'] > max_rtt_expected:
                ip_data[key]['Usable_Last_Hop_RTT'] = prb_item['Second_Last_RTT']
                ip_data[key]['Usable_Last_Hop_IP'] = prb_item['Second_Last_Hop']

              ip_data['Last_Hops_final'].append(ip_data[key]['Usable_Last_Hop_IP'])
              
            #Calculate the rdns of the last hop IPs, then do a hoiho reuqest and map the lat,long to domain to probe
            #If the distance beween the lat,long (this and library) is closer than 25 Km, update the geoloc boolean
            ip_data['Last_Hops_final'] = list(set(ip_data['Last_Hops_final']))
            domains_dict = perform_lookups(ip_data['Last_Hops_final'])
            

            domain_list = []
            for ip in ip_data['Last_Hops_final']:
                domain = domains_dict[ip]
                if domain is not None:
                    domain_list.append(domain)
                else:
                    domain_list.append('*') #Placeholder for no domain found
            #Not needed after this
            ip_data['Last_Hops_final'] = domains_dict
            #Querying Hoiho
            data = domain_list
            url = 'https://api.hoiho.caida.org/lookups'
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print("Request was successful.")
                response_data = response.json()
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
                reponse_data = None #Make sure you handle this

            #Parsing the response data
            

               

            #Get the smallest rtt probes
            
            
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
    info_file = 'test_file.txt'
    directory = './Library_Static_Data/'
    folders = os.listdir(directory)
    #Compare_name
    with open(info_file, 'r') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        comp_lines = [line.split('~')[2] for line in lines]

    for folder in folders:
      current_path = os.path.join(directory, folder)
      json_path = os.path.join(current_path, 'JSON')
      probe_path = os.path.join(current_path, 'grouped_probes.json')
      probe_directory = os.path.join(current_path, 'Past_probes')
      #check if Json path exists
      if not os.path.exists(json_path):
          continue
      folder_names = os.listdir(json_path)
      folder_names = [os.path.join(json_path, folder) for folder in folder_names]
      dest_file = os.path.join(current_path, 'meta.txt')
      
      name = folder.split('Results_')[1]
      name = name.replace('?','/')
      name = name.replace('_',' ')
      if name not in comp_lines:
        continue
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
      data = read_traceroute(folder_names, dest_file, probe_data, (lat,lon))
      dest_folder = os.path.join(current_path, 'Trace_data.json')
      #Check if the folder exists
      with open(dest_folder, 'w') as f:
          json.dump(data, f, indent=4)

      #Checking last mile latencies --- THE IDEA
      #Store the second last and last hop IPs as pairs for only the traces whose destination replied (otherwise we can't really say anything for access net)
      #The dicrionary will store the difference between those two pairs for that library group
      #Question? --> What if we just foudn them on bad day? -- high RTT difference? -- can't do much that's an issue
      #If the last mile latency, if there is a lower difference, use that
      #If there is only one difference, then we need a threshold -- (avg RTT based on distance 14.75+0.015*dist) with a RMSE of 12ms(cite)
      #Based on this it should not be going further than the neasrest high pop density region
      ## Use burlington's example to say that the last mile latency may be going though the nearest metro region
      ## Assumtion is that the last hop differnce should not be higher than the average RTT between the probe and the destination
      break

main()

