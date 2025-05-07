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
def read_traceroute(folder_names, dest_file):
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
            
            ip_data = {'Failed': False, 'CIDR' :cidr.replace("?","/").split(".")[0],'MSM_ID': msm_id, 'Last_Hop_Second_Last_Hop_Difference':{}}

            if ip not in temp.keys():
               print(f'IP {ip} not in file {file}')
               ip_data['Failed'] = True
               data[ip] = ip_data
               continue

            #Getting the traceroutes and last_hop_ip per prb
            for item in temp[ip]:
                #The probes update every day so we will have to update this everyday too
                prb_item = {'Traceroute':[], 'Last_Hop_IP':None, 'Dest_Replied':False, 'RTTs':[], 'Second_Last_Hop':None, 'Last_RTT':None, 'Second_Last_RTT':None,'Final_Hop_Differences':{}}
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
                
                if second_last_rtt != math.inf and last_hop_rtt != math.inf:
                  d_key = f'{last_hop_ip}-{second_last_hop}'
                  difference = last_hop_rtt - second_last_rtt
                
                try:
                  item = prb_item['Final_Hop_Differences'][d_key]
                except KeyError:
                  prb_item['Final_Hop_Differences'][d_key] = []
                prb_item['Final_Hop_Differences'][d_key].append(difference)
                  
                ip_data[item['prb_id']] = prb_item
                #TODO
                #Store info for all last-second last hops -- check if this is true
                #
                # Get the probe lat,long here -- if not found -- which should not be the case
                #for same day measurements (Save all grouped probes based on the date!)
                #Then find the distance and update the latency
                #Also at the end get the domain name using rdns on the last and second last domain
                #Once all the above is done, get the lowest 3 RTTs in order per IP
                ##This will be used for CBG analysis
                #Test for boston public library
                
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
    write_lines_to_file(dest_file, data_lines)
    print(f'Network Errors: {network_error_count}')
    print(f'Folder Count: {folder_count}')
    print(f'Weird Count: {weird_count}')
    print(f'Data Count: {data_count}')
    print(f'IPs: {len(ips_t)}')#Some IPs are overlapping from the original CIDRs sepration -- probably due to there being a /28 and a /26
    #From two datasets
    return data

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
      #,probe_path,(lat,lon)
      print(f'Lat: {lat}, Lon: {lon}')
      data = read_traceroute(folder_names, dest_file)
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

