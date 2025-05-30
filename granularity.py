import os
import csv
import json
import ipaddress
from tqdm import tqdm
import matplotlib.pyplot as plt

#Going over each file in the directory
directory = './Library_Static_Data_og/'

#Getting all the folders in the directory
folders = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
totals = {26:0,27:0,28:0,29:0,30:0,31:0,32:0}
for folder in folders:
    folder_path = os.path.join(directory, folder)
    
    #Get all files in the folder
    files = [file for file in os.listdir(folder_path)]

    if 'final_filtered.txt' not in files or 'final_cidrs.txt' not in files:
        continue

    print(f'Processing folder: {folder}')

    with open(os.path.join(folder_path, 'final_filtered.txt'), 'r') as f:
        lines = f.readlines()

    with open(os.path.join(folder_path, 'final_cidrs.txt'), 'r') as f:
        cidrs = f.readlines()

    subnets = []
    for line in tqdm(lines):
        line = line.strip()
        ip = line.split('/')[0]
        subnet = int(line.strip().split('/')[1])
        if not line:
            continue
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            print(f"Invalid IP address: {ip}")
            continue
        
        #Check if line is any subnets in CIDRs include the above IP, then check if the subnet is larger than the one in CIDR, if yes store it
        for cidr in cidrs:
            cidr = cidr.strip()
            cidr_ip = cidr.split('/')[0]
            cidr_subnet = int(cidr.strip().split('/')[1])
            if not cidr:
                continue
            try:
                #Since the cidr net might be smaller
                network = ipaddress.IPv4Network(cidr, strict=False)
                if ipaddress.IPv4Address(ip) in network:
                    val = max(network.prefixlen, subnet)
                    subnets.append(val)
                    totals[val] += 1
                else:
                    network = ipaddress.IPv4Network(line, strict=True)
                    if ipaddress.IPv4Address(cidr_ip) in network:
                        val = max(network.prefixlen, subnet)
                        subnets.append(val)
                        totals[val] += 1
            except ipaddress.AddressValueError:
                print(f"Invalid CIDR: {cidr}")
                continue
    
    #Write the subnets to a file
    with open(os.path.join(folder_path, 'final_subnets.txt'), 'w') as f:
        for subnet in subnets:
            f.write(f"{subnet}\n")

#Create a bar chart of the totals
plt.bar(totals.keys(), totals.values())
plt.xlabel('Subnet Size')
plt.ylabel('Count')
plt.title('Count of Subnets by Size')
plt.xticks(list(totals.keys()), [f'/{key}' for key in totals.keys()])
plt.savefig('subnet_counts.png')
plt.show()
#Write the totals to a file
with open('subnet_counts.json', 'w') as f:
    json.dump(totals, f, indent=4)



