import pandas as pd
import numpy as np
import socket
from tqdm import tqdm
import ipaddress
import json
import advertools as adv


def get_ips(cidr):
    network = ipaddress.ip_network(cidr)
    return [str(ip) for ip in network.hosts()]


if __name__ == '__main__':

    #Read the CSV file
    #Change the file name to the one you want to use
    df = pd.read_csv('union_whois.csv')

    #Remove any IPs that are residential, keep a list of cidrs and then keep a list of all the rdns names
    #rdns names , why all? we need one info in that cidr, random selection might miss it
    #Send all the rdns names to hoiho
    #Send the filtered IP/ CIDRs to tracerotues

    #Removing IPs that are not under charter(spectrum) or At&t
    filtered_nets = []

    print('Filtering the IPs')
    for i in range(len(df)):
        current = str(df['Orgnames'][i]).lower()
        #Change based on the library
        if 'xfinity' in current or 'comcast' in current:
            filtered_nets.append(df['Subnet'][i])

    #Outputting to a text file
    with open('filtered_cidrs.txt', 'w') as f:
        for net in filtered_nets:
            f.write(net + '\n')
            
    #Getting rdns for the filtered IPs

    filtered_ips = [get_ips(net) for net in filtered_nets]
    #USe ADVERTOOLS for this
    print('Getting RDNS')
    rdns_list = []        
    for ips in tqdm(filtered_ips):
        rdns_lookup = adv.reverse_dns_lookup(ips)
        rdns_list.append(rdns_lookup['aliaslist'].to_list())
            
    #Saving the RDNS to text file
    print('Saving RDNS')
    data = {'IP':filtered_ips,'RDNS':rdns_list,'CIDR':filtered_nets}
    with open('rdns_info.json', 'w') as f:
        json.dump(data, f)
            
    print('Finished the process')