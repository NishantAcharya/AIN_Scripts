#Need a piece of code that consolidates the tracesrutes for each IP, multipe IPs will be in another set under it
# {Dest IP: Probe ID: {Traceroute: [Hops], last hop ip, pings: [], bdrmapit ASes:[], Direct AS Path:[]}}}
#Need a text file that has 1 line in the format : Dest IP -- Probe ID -- Last hop IP#

import os
import json
from tqdm import tqdm
import ipaddress
import statistics

def get_all_files_in_folder(folder_path):
  """
  Gets a list of all files within a given folder.

  Args:
    folder_path: The path to the folder.

  Returns:
    A list of file names within the folder.
  """
  try:
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
  except FileNotFoundError:
    print(f"Error: Folder '{folder_path}' not found.")
    return []
  
def write_lines_to_file(filename, lines):
  """
  Writes a list of lines to a file.

  Args:
    filename: The name of the file to write to.
    lines: A list of strings, where each string represents a line to be written.
  """
  try:
    with open(filename, 'w') as file:
      file.writelines(line + '\n' for line in lines)
  except FileNotFoundError:
    print(f"Error: Could not write to file '{filename}'.")
    return

#This function will read a traceroute and get the IPs in a traceroute, given the a folder_set with the trace data
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
            
            ip_data = {'Failed': False, 'CIDR' :cidr.replace("?","/").split(".")[0],'MSM_ID': msm_id}

            if ip not in temp.keys():
               print(f'IP {ip} not in file {file}')
               ip_data['Failed'] = True
               data[ip] = ip_data
               continue

            #Getting the traceroutes and last_hop_ip per prb
            for item in temp[ip]:
                prb_item = {'Traceroute':[], 'Last_Hop_IP':[], 'Dest_Replied':False, 'RTTs':[]}
                prb_item['Dest_Replied'] = item['destination_ip_responded']
                traceroute_full = item['result']
                last_hop_ip = item['src_addr'] #Start with the source address

                try:
                  if ipaddress.ip_address(last_hop_ip).is_private:
                      last_hop_ip = None
                except ValueError:
                   network_error_count += 1
                   prb_item['Dest_Replied'] = False
                   ip_data['Failed'] = True
                   ip_data[item['prb_id']] = prb_item
                   continue
                  
                #for hop in traceroute_full:
                #    try:
                #        hop_ip = hop['result'][0]['from'] #Single ping traceroute, for more scan the full list
                #        if not ipaddress.ip_address(hop_ip).is_private:
                #            last_hop_ip = hop_ip
                #    except KeyError:
                #        hop_ip = '*'

                #    try:
                #        rtt = hop['result'][0]['rtt']
                #    except KeyError:
                #        rtt = '*'
                        

                #    prb_item['Traceroute'].append(hop_ip)
                #    prb_item['RTTs'].append(rtt)
                
                #prb_item['Last_Hop_IP'] = last_hop_ip
            
                #ip_data[item['prb_id']] = prb_item

                #Adding the file lines
                #data_lines.append(f'{ip}-{item["prb_id"]}-{last_hop_ip}-{cidr.replace("?","/").split(".json")[0]}')

                #Getting the number of packets
                num_pkts = len(traceroute_full[0]['result'][0]) # Assuming the set of pkts to go out
                for i in range(0,num_pkts-1):
                  traces = []
                  rtts = []
                  lhp = last_hop_ip
                  for hop in traceroute_full:
                      try:
                          hop_ip = hop['result'][i]['from'] #Single ping traceroute, for more scan the full list
                          if not ipaddress.ip_address(hop_ip).is_private:
                              lhp = hop_ip
                      except KeyError:
                          hop_ip = '*'
                      except IndexError:
                         print(hop['result'])
                         print(i)
                         raise
                      try:
                          rtt = hop['result'][i]['rtt']
                      except KeyError:
                          rtt = '*'
                      traces.append(hop_ip)
                      rtts.append(rtt)
                  
                  prb_item['Last_Hop_IP'].append(lhp)
                  prb_item['Traceroute'].append(traces)
                  prb_item['RTTs'].append(rtts)
                ip_data[item['prb_id']] = prb_item
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
    #folder_names = ['JSON/Feb-26-2025_fixed']
    #dest_file = 'ping_inpt.txt'
    directory = './Library_Static_Data/'
    folders = os.listdir(directory)
    for folder in folders:
      current_path = os.path.join(directory, folder)
      json_path = os.path.join(current_path, 'JSON')
      #check if Json path exists
      if not os.path.exists(json_path):
          continue
      folder_names = os.listdir(json_path)
      folder_names = [os.path.join(json_path, folder) for folder in folder_names]
      dest_file = os.path.join(current_path, 'meta.txt')
      data = read_traceroute(folder_names, dest_file)
      dest_folder = os.path.join(current_path, 'Trace_data.json')
      #Check if the folder exists
      with open(dest_folder, 'w') as f:
          json.dump(data, f, indent=4)

      #Checking last mile latencies
      rtt_vals = {}
      for ip in data.keys():
        current_data = data[ip]
        if current_data['Failed']:
              continue
        rtt_vals[ip] = {}
        for item in current_data.keys():
           if type(item) == int:
              prb = current_data[item]
              rtt_vals[ip][item] = {'last_hop': None, 'last_rtt': None, 'second_last_hop': None, 'second_last_rtt': None,'lat_long':None,'min_rtt_devation':None,'min_rtt':None,'min_rtt_hop':None}
              traces = prb['Traceroute']
              rtts = prb['RTTs']
              last_hop = None
              last_rtt = None
              second_last_hop = None
              second_last_rtt = None
              std_devs = []
              for rtt_list in rtts:
                 sanitized_list = [item for item in rtt_list if item != '*']
                 dev = statistics.pstdev(sanitized_list)
                 std_devs.append(dev)
              rtt_vals[ip][item]['min_rtt_devation'] = min(std_devs)
              #Getting Min values
              for k in range(len(traces)):
                trace = traces[k]
                rts = rtts[k]
                for i in range(len(trace)-1,-1,-1):
                  if trace[i] != '*':
                      if last_hop is None:
                        last_hop = trace[i]
                        last_rtt = rts[i]
                        second_last_hop = trace[i-1]
                        second_last_rtt = rts[i-1]
                      else:
                         if last_rtt > rts[i]:
                            last_hop = trace[i]
                            last_rtt = rts[i]
                            second_last_hop = trace[i-1]
                            second_last_rtt = rts[i-1]
                      break
              
              rtt_vals[ip][item]['last_hop'] = last_hop
              rtt_vals[ip][item]['last_rtt'] = last_rtt
              rtt_vals[ip][item]['second_last_hop'] = second_last_hop
              rtt_vals[ip][item]['second_last_rtt'] = second_last_rtt

              if last_rtt - second_last_rtt > min(std_devs):
                  rtt_vals[ip][item]['min_rtt'] = second_last_rtt
                  rtt_vals[ip][item]['min_rtt_hop'] = second_last_hop
              else:
                  rtt_vals[ip][item]['min_rtt'] = last_rtt
                  rtt_vals[ip][item]['min_rtt_hop'] = last_hop

              probe_folder = os.path.join(current_path, 'grouped_probes.json')
              with open(probe_folder) as f:
                  probe_data = json.load(f)

              lat_long = probe_data['Close'][str(item)][1]
              rtt_vals[ip][item]['lat_long'] = lat_long
      
      #Saving the RTT info
      rtt_file = os.path.join(current_path, 'rtt_vals.json')
      with open(rtt_file, 'w') as f:
          json.dump(rtt_vals, f, indent=4)
      

main()

