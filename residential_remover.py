import numpy as np
import pandas as pd
import json

#Read the JSON File and remove the residential IPs, then coagulate under CIDRs and select 1 IP per CIDR
with open('rdns_info.json', 'r') as f:
    data = json.load(f)
    
ips = data['IP']
rdns = data['RDNS']
cidrs = data['CIDR']

for i in range(len(rdns)):
    for j in range(len(rdns[i])):
        if rdns[i][j] is not None and ('residential' in rdns[i][j].lower() or 'res' in rdns[i][j].lower()):
            ips[i].remove(ips[i][j])
            cidrs.remove(cidrs[i])
            
filtered_ips = []
filtered_cidrs = []

for i in range(len(ips)):
    if len(ips[i]) > 0:
        idx = np.random.randint(0,len(ips[i]))
        filtered_ips.append(ips[i][idx])
        filtered_cidrs.append(cidrs[i])
            
with open('filtered_ips.txt', 'w') as f:
    for i in range(len(filtered_ips)):
        ip = filtered_ips[i]
        cidr = filtered_cidrs[i]
        f.write(ip +'-'+cidr+ '\n')