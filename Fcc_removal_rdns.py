import pandas as pd
import numpy as np
import socket
from tqdm import tqdm
import ipaddress
import json
import advertools as adv
import sys
import subprocess
import signal
import sys
import re
import socket
from netaddr import *
import netaddr
import argparse
import random

def get_ips(cidr):
    network = ipaddress.ip_network(cidr)
    return [str(ip) for ip in network.hosts()]

def iterate_ip_subnet(subnet):
    ips = []
    domains = []
    servers = ['8.8.8.8','8.26.56.26','45.90.29.77','185.228.168.9'
               ,'9.9.9.9','204.194.232.200','67.210.146.50','96.7.136.90','71.78.212.171','96.73.116.29']
    query_count = {server: 0 for server in servers}
    current_server_index = 0

    try:
        ip_range = IPNetwork(subnet)
        for ip in ip_range:
            server = servers[current_server_index]
            output = resolve_ptr(ip, server)
            query_count[server] += 1

            if query_count[server] >= 10:
                current_server_index = (current_server_index + 1) % len(servers)
                query_count[server] = 0

            ips.append(output[0])
            domains.append(output[1])
    except netaddr.core.AddrFormatError:
        print("\nError: Invalid IP Network entered.")
        print("Try again.")
        sys.exit(0)
    return ips, domains
def resolve_ptr(ip,server):
    cmd = "host -W 0.005 %s %s" % (ip, server)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0]
    p = p.decode('utf-8')

    match_found = re.search('name pointer', p)
    if match_found:
        return (ip, p.strip('\n').split(' ')[-1])
    
    return (ip, '')


if __name__ == '__main__':

    #Read the CSV file
    #Change the file name to the one you want to use
    #df = pd.read_csv('union_whois.csv')

    #Remove any IPs that are residential, keep a list of cidrs and then keep a list of all the rdns names
    #rdns names , why all? we need one info in that cidr, random selection might miss it
    #Send all the rdns names to hoiho
    #Send the filtered IP/ CIDRs to tracerotues

    #Removing IPs that are not under charter(spectrum) or At&t
    #filtered_nets = []

    #print('Filtering the IPs')
    #for i in range(len(df)):
    #    current = str(df['Orgnames'][i]).lower()
    #    #Change based on the library
    #    if 'xfinity' in current or 'comcast' in current:
    #        filtered_nets.append(df['Subnet'][i])

    #Outputting to a text file
    #with open('filtered_cidrs.txt', 'w') as f:
    #    for net in filtered_nets:
    #        f.write(net + '\n')
            
    #Getting rdns for the filtered IPs

    file_path = sys.argv[1] #Results_{lib_name}/outputs/final_cidrs.txt
    output_path = sys.argv[2] #Results_{lib_name}/rdns_info.json

    #Remove space from the file path
    file_path = file_path.replace(" ", "\ ")
    output_path = output_path.replace(" ", "\ ")

    with open(file_path, 'r') as f:
        filtered_nets = [line.strip() for line in f.readlines()]

    filtered_ips = [get_ips(net) for net in filtered_nets]
    #USe ADVERTOOLS for this
    print('Getting RDNS')
    rdns_list = []        
    for ips in tqdm(filtered_ips):
        rdns_lookup = adv.reverse_dns_lookup(ips,max_workers=20)
        rdns_list.append(rdns_lookup['hostname'].to_list())
            
    #Saving the RDNS to text file
    print('Saving RDNS')
    data = {'IP':filtered_ips,'RDNS':rdns_list,'CIDR':filtered_nets}
    with open(output_path, 'w') as f:
        json.dump(data, f)
    
