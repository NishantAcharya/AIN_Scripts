import pyasn
import linecache
from pathlib import Path
import os
import csv
import json
from tqdm import tqdm
import ipaddress



#Files, may need to modify the file path
dat_file = "whois_data/cidr.dat"
csv_file = "whois_data/cidr_greater_25.csv"

asndb = pyasn.pyasn(str(dat_file))
directory = './Library_Static_Data_og/'



def query_org(IP):
    csv_line_num = asndb.lookup(IP)
    #print(csv_line_num)
    csv_line = linecache.getline(str(csv_file), int(csv_line_num[0])).strip()
    fields = csv_line.split(",")
    if len(fields) < 3:
        print(f"Warning: Not enough fields for IP {IP} - (fields: {len(fields)}) (line: '{csv_line}')")
        return None, None, None
    return fields[0], fields[1], fields[2]

#Get all folders in the directory
folders = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]

for folder in folders:
    #Get all files in the folder
    #test = 'Results_LINCON_COUNTY_LIBRARY_ALUM_CREEK'
    #if folder != test:
    #    continue
    folder_path = os.path.join(directory, folder)
    files = [file for file in os.listdir(folder_path)]
    if 'Trace_data.json' not in files or 'final_filtered.txt' not in files:
        continue
    print(f'Processing folder: {folder}')
    with open(os.path.join(folder_path, 'Trace_data.json'), 'r') as f:
        trace_data = json.load(f)

    with open(os.path.join(folder_path, 'final_filtered.txt'), 'r') as f:
        lines = f.readlines()

    providers = []
    for line in tqdm(lines):
        line = line.strip()
        if not line:
            continue
        ip = line.split('/')[0]
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            print(f"Invalid IP address: {ip}")
            continue
        
        #Get the provider of the IP
        cidr, netrange, org_name = query_org(ip)
        providers.append(org_name)

    #Remove all nones and empty strings from the providers list
    providers = list(set([provider for provider in providers if provider is not None and provider != '']))
    print(providers)

    provider_set = []
    full_provider_set = []
    for ip_key in tqdm(trace_data):
        trace_info = trace_data[ip_key]
        last_orgs = []
        second_last_orgs = []
        for probe_key in trace_info:
            if not isinstance(probe_key, int) and not (isinstance(probe_key, str) and probe_key.isdigit()):
                continue
            probe_info = trace_info[probe_key]

            last_hop = probe_info['Last_Hop_IP']
            second_last_hop = probe_info['Second_Last_Hop']
            if last_hop != None and last_hop != '' and last_hop != '*':
                last_hop_provider = query_org(last_hop)[2]
                last_orgs.append(last_hop_provider)

            if second_last_hop != None and second_last_hop != '' and second_last_hop != '*':
                second_last_hop_provider = query_org(second_last_hop)[2]
                second_last_orgs.append(second_last_hop_provider)

        
        last_orgs = list(set(last_orgs))
        second_last_orgs = list(set(second_last_orgs))
        #Assuming if one of them reached the provider at the last hop, it will be in that set
        if bool(set(providers) & set(last_orgs)) or bool(set(providers) & set(second_last_orgs)):
            provider_set.append(ip_key)

        #Saving the provider list
        temp = []
        temp.extend(last_orgs)
        temp.extend(second_last_orgs)
        temp = list(set(temp))
        full_provider_set.extend(temp)

    #Saving provider set to a file
    with open(os.path.join(folder_path, 'provider_set.txt'), 'w') as f:
        full_provider_set = list(set(full_provider_set))
        for provider in full_provider_set:
            f.write(provider + '\n')

    #Write the providers to a file
    with open(os.path.join(folder_path, 'provider_ips.txt'), 'w') as f:
        for provider in provider_set:
            f.write(provider + '\n')

    

    # Print the total number of providers found
    print(f'Total number of providers found for {folder}: {len(provider_set)}')













