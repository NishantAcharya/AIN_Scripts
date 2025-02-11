import numpy as np
import pandas as pd
import json
import ipaddress


#To break down a CIDR into smaller subnets with the specified mask such as 28
def break_cidr(cidr, target_mask):
    network = ipaddress.ip_network(cidr)

    if network.prefixlen >= target_mask:
        return [network]  # No need to break down further

    subnets = []
    for subnet in network.subnets(new_prefix=target_mask):
        subnets.append(subnet)

    return subnets

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
            if len(ips[i]) == 0:
                ips.remove(ips[i])
                cidrs.remove(cidrs[i])
        

#Filter the cidrs and IPs into a mask (for now /26)
masked_ips = []
masked_cidrs = []

mask = 26
for cidr in cidrs:
    subnets = break_cidr(cidr, mask)
    for subnet in subnets:
        masked_cidrs.append(str(subnet))

for i in range(len(ips)):
    seperated_cidr_ips = []
    for ip in ips[i]:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(masked_cidrs[i]):
            seperated_cidr_ips.append(ip)
    masked_ips.append(seperated_cidr_ips)


filtered_ips = []
filtered_cidrs = []

for i in range(len(ips)):
    if len(ips[i]) > 0:
        #Select 1 IP per CIDR (Check the size of the CIDR, then bifurcate into /26 then choose 1 IP from that)
        idx = np.random.randint(0,len(ips[i]))
        filtered_ips.append(ips[i][idx])
        filtered_cidrs.append(cidrs[i])
            
with open('filtered_ips.txt', 'w') as f:
    for i in range(len(filtered_ips)):
        ip = filtered_ips[i]
        cidr = filtered_cidrs[i]
        f.write(ip +'-'+cidr+ '\n')