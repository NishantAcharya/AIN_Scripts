#Need a piece of code that consolidates the tracesrutes for each IP, multipe IPs will be in another set under it
# {Dest IP: Probe ID: {Traceroute: [Hops], last hop ip, pings: [], bdrmapit ASes:[], Direct AS Path:[]}}}
#Need a text file that has 1 line in the format : Dest IP -- Probe ID -- Last hop IP#

import os
import json
from tqdm import tqdm
import ipaddress

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
    for folder in folder_names:
        #Walking through files in the folder
        files = get_all_files_in_folder(folder)
        for file in tqdm(files):
            if '.json' not in file:
                continue
            
            file_path = folder+'/'+file
            with open(file_path, 'r') as f:
               temp = json.load(f)

            msm_id = file.split('-')[0].strip()
            ip = file.split('-')[1].strip()
            cidr = file.split('-')[2].strip()
            
            ip_data = {'Failed': False, 'CIDR' :cidr.replace("?","/").split(".")[0],'MSM_ID': msm_id}

            if ip not in temp.keys():
               ip_data['Failed'] = True
               continue

            #Getting the traceroutes and last_hop_ip per prb
            for item in temp[ip]:
                prb_item = {'Traceroute':[], 'Last_Hop_IP':None, 'Dest_Replied':False, 'RTTs':[]}
                prb_item['Dest_Replied'] = item['destination_ip_responded']
                traceroute_full = item['result']
                last_hop_ip = item['src_addr'] #Start with the source address

                if ipaddress.ip_address(last_hop_ip).is_private:
                    last_hop_ip = None

                for hop in traceroute_full:
                    try:
                        hop_ip = hop['result'][0]['from'] #Single ping traceroute, for more scan the full list
                        if not ipaddress.ip_address(hop_ip).is_private:
                            last_hop_ip = hop_ip
                    except KeyError:
                        hop_ip = '*'

                    try:
                        rtt = hop['result'][0]['rtt']
                    except KeyError:
                        rtt = '*'
                        

                    prb_item['Traceroute'].append(hop_ip)
                    prb_item['RTTs'].append(rtt)
                
                prb_item['Last_Hop_IP'] = last_hop_ip
            
                ip_data[item['prb_id']] = prb_item

                #Adding the file lines
                data_lines.append(f'{ip}-{item["prb_id"]}-{last_hop_ip}-{cidr.replace("?","/").split(".json")[0]}')


            
            data[ip] = ip_data
    write_lines_to_file(dest_file, data_lines)
    return data

def main():
    folder_names = ['JSON/Jan-08-2025']
    dest_file = 'ping_inpt.txt'
    data = read_traceroute(folder_names, dest_file)
    #In Future need a way to keep track of the library name
    with open('Trace_data/Burlington.json', 'w') as f:
        json.dump(data, f, indent=4)


main()

