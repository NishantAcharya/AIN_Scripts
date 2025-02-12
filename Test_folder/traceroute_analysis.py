import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ipwhois import IPWhois
from tqdm import tqdm
import ipaddress

def get_asn(ip):
    obj = IPWhois(ip)
    res = obj.lookup_whois()
    return res['asn'],res['asn_cidr']

#Reading the processes traceroute file
with open('Trace_data/Burlington.json', 'r') as f:
    data = json.load(f)

#Extracting the data
unique_ends_with_starts = {} #last response_ip: [destinations] #
current_hop_len = -1 #-1 will be hop 255, everything else will be from 0 to hop_len -1
fail_count_ips = 0#
fail_count_total = 0#
last_hop_ASNs = {} #ASN: [last_hop_ip]
last_hop_cidr = {} #CIDR: [last_hop_ip]
hop_to_ip = {} #hop: [destination_ip]#
all_rtts = {}#find the max range till 255, like how many before we jump up to 255, then fill each one and get a CSV
#Using that CSV make a graph of the RTT values --> show where the spikes are
#Get the median difference between hops for each row, then anytime the rtt is over the median difference, subtract the difference between the median 
#rtt and the current hop difference, make a sum of all of these and subtract from the last hop rtt --> subtracted rtt

#Use the WHOIS data to get the ASN of the last hop IP and most common hop IP for now until bdrmpait is run

#At the end run bdrmapit to support your claims with ASNs to show that high latency is during AS switches

#Extract the hop ip with the most 

for key in tqdm(data):
    fail_check = True
    for msm in data[key]:
        try:
            check = int(msm)
        except ValueError:
            continue
        
        #If this is true, then no probe replied
        item = data[key][msm]
        try:
            traceroute = item['Traceroute']
        except:
            print(item)
            raise
        current_hop_len = max(len(traceroute), current_hop_len)

        if item['Dest_Replied'] == False:
            fail_count_ips += 1
        else:
            fail_check = False

        #getting the last hop IP
        last_hop_ip = item['Last_Hop_IP']
        if last_hop_ip !='*':
            try:
                temp = unique_ends_with_starts[last_hop_ip]
            except KeyError:
                unique_ends_with_starts[last_hop_ip] = []
            unique_ends_with_starts[last_hop_ip].append(key)

        #Getting WHOis info about the last hop IP ASN
        asn,a_cidr = get_asn(last_hop_ip)
        try:
            temp = last_hop_ASNs[asn]
        except KeyError:
            last_hop_ASNs[asn] = []
        
        last_hop_ASNs[asn].append(last_hop_ip)

        try:
            temp = last_hop_cidr[a_cidr]
        except KeyError:
            last_hop_cidr[a_cidr] = []
        last_hop_cidr[a_cidr].append(last_hop_ip)
        
        #Getting each hop to ip
        for hop_item in traceroute:
            if hop_item != '*':
                try:
                    temp = hop_to_ip[hop_item]
                except KeyError:
                    hop_to_ip[hop_item] = []
                hop_to_ip[hop_item].append(key)
        
        #Getting the RTTs
        rtts = item['RTTs']
        try:
            temp = all_rtts[msm]
        except KeyError:
            all_rtts[msm] = []
        all_rtts[msm].append(rtts)
    
    #Checking if all probes failed
    if fail_check:
        fail_count_total += 1


#Displaying values
print(f'Unique IPs with no response: {fail_count_total}')
print(f'Unique Probe-Destination IP with no response: {fail_count_ips}')
print(f'Unique Last Hop IPs: {len(unique_ends_with_starts.keys())}')
print('-----------------------------------------------------------------\n')

#Finding the most common hop in all traces
most_common_hop = None
common_hops = []
for hop in hop_to_ip.keys():
    if ipaddress.ip_address(hop).is_private == False:
        continue
    if most_common_hop is None:
        most_common_hop = hop
        common_hops.append(hop)
    elif len(hop_to_ip[hop]) > len(hop_to_ip[most_common_hop]):
        most_common_hop = hop
        common_hops = [hop]
    elif len(hop_to_ip[hop]) == len(hop_to_ip[most_common_hop]):
        common_hops.append(hop)

print(f'Most common hop: {common_hops} with {len(hop_to_ip[most_common_hop])} unique IPs')
print('-----------------------------------------------------------------\n')

#Getting the top 5 most common AS and CIDRs in the traceroutes to the location
top_5_ases = []
top_5_ases_length = []
equal_ases = {}
for key in last_hop_ASNs:
    if len(top_5_ases) < 5:
        top_5_ases.append(key)
        top_5_ases_length.append(len(last_hop_ASNs[key]))
    else:
        min_index = top_5_ases_length.index(min(top_5_ases_length))
        if len(last_hop_ASNs[key]) > top_5_ases_length[min_index]:
            top_5_ases[min_index] = key
            top_5_ases_length[min_index] = len(last_hop_ASNs[key])
        elif len(last_hop_ASNs[key]) == top_5_ases_length[min_index]:
            try:
                temp = equal_ases[key]
            except KeyError:
                equal_ases[top_5_ases[min_index]] = []
            equal_ases[top_5_ases[min_index]].append(key)

print(f'Top 5 ASNs: {top_5_ases} with {top_5_ases_length}')
print(f'Equal ASNs: {equal_ases}')
print('-----------------------------------------------------------------\n')

#Getting the top 5 most common CIDRs in the traceroutes to the location
top_5_cidrs = []
top_5_cidrs_length = []
equal_cidrs = {}
for key in last_hop_cidr:
    if len(top_5_cidrs) < 5:
        top_5_cidrs.append(key)
        top_5_cidrs_length.append(len(last_hop_cidr[key]))
    else:
        min_index = top_5_cidrs_length.index(min(top_5_cidrs_length))
        if len(last_hop_cidr[key]) > top_5_cidrs_length[min_index]:
            top_5_cidrs[min_index] = key
            top_5_cidrs_length[min_index] = len(last_hop_cidr[key])
        elif len(last_hop_cidr[key]) == top_5_cidrs_length[min_index]:
            try:
                temp = equal_cidrs[key]
            except KeyError:
                equal_cidrs[top_5_cidrs[min_index]] = []
            equal_cidrs[top_5_cidrs[min_index]].append(key)

print(f'Top 5 CIDRs: {top_5_cidrs} with {top_5_cidrs_length}')
print(f'Equal CIDRs: {equal_cidrs}')
print('-----------------------------------------------------------------\n')

#Getting the AS and CIDR with top 5(based on num of items associated) last hop IPs associated with it, along with how many IPs are associated with them
top_5_last_hops = []
top_5_last_hops_length = []
equal_last_hops = {}
top_5_last_hop_ASNs = []
for key in unique_ends_with_starts:
    if ipaddress.ip_address(key).is_private == False:
        continue
    if len(top_5_last_hops) < 5:
        top_5_last_hops.append(key)
        top_5_last_hops_length.append(len(unique_ends_with_starts[key]))
    else:
        min_index = top_5_last_hops_length.index(min(top_5_last_hops_length))
        if len(unique_ends_with_starts[key]) > top_5_last_hops_length[min_index]:
            top_5_last_hops[min_index] = key
            top_5_last_hops_length[min_index] = len(unique_ends_with_starts[key])
        elif len(unique_ends_with_starts[key]) == top_5_last_hops_length[min_index]:
            try:
                temp = equal_last_hops[key]
            except KeyError:
                equal_last_hops[top_5_last_hops[min_index]] = []
            equal_last_hops[top_5_last_hops[min_index]].append(key)

for hop in top_5_last_hops:
    if ipaddress.ip_address(hop).is_private:
        asn = 'Private'
    else:
        asn,_ = get_asn(hop)
    top_5_last_hop_ASNs.append((hop,asn))
    try:
        temp = equal_last_hops[hop]
    except KeyError:
        temp = []

    for item in temp:
        asn,_ = get_asn(item)
        top_5_last_hop_ASNs.append((item,asn))


print(f'Top 5 Last Hops: {top_5_last_hops}')
print(f'Equal Last Hops: {equal_last_hops}')
print(f'Last Hop ASNs: {top_5_last_hop_ASNs}')
print(f'The range of IPs associated with Last Hops: {max(top_5_last_hops_length)} - {min(top_5_last_hops_length)}')
print('-----------------------------------------------------------------\n')
        
#Getting the AS and CIDR of top 5 most common hops along with how many associated with it
top_5_common_hops = []
equal_common_hops = {}
top_5_common_hops_length = [-1]
top_5_common_hops_ASNs = []

for key in hop_to_ip:
    if ipaddress.ip_address(key).is_private == False:
        continue

    if len(top_5_common_hops) < 5:
        top_5_common_hops.append(key)
        top_5_common_hops_length.append(len(hop_to_ip[key]))
    else:
        min_index = top_5_common_hops_length.index(min(top_5_common_hops_length))
        if len(hop_to_ip[key]) > top_5_common_hops_length[min_index]:
            top_5_common_hops[min_index] = key
            top_5_common_hops_length[min_index] = len(hop_to_ip[key])
        elif len(hop_to_ip[key]) == top_5_common_hops_length[min_index]:
            try:
                temp = equal_common_hops[key]
            except KeyError:
                equal_common_hops[top_5_common_hops[min_index]] = []
            equal_common_hops[top_5_common_hops[min_index]].append(key)

for hop in top_5_common_hops:
    if ipaddress.ip_address(key).is_private == False:
        asn = 'Private'
    else:
        asn,_ = get_asn(hop)
    top_5_common_hops_ASNs.append((hop,asn))
    try:
        temp = equal_common_hops[hop]
    except KeyError:
        temp = []

    for item in temp:
        asn,_ = get_asn(item)
        top_5_common_hops_ASNs.append((item,asn))


print(f'Top 5 Common Hops: {top_5_common_hops}')
print(f'Equal Common Hops: {equal_common_hops}')
print(f'Common Hop ASNs: {top_5_common_hops_ASNs}')
print(f'The range of IPs associated with Common Hops: {max(top_5_common_hops_length)} - {min(top_5_common_hops_length)}')
print('-----------------------------------------------------------------\n')

#Current hop length
print(f'Current hop length: {current_hop_len}')

#Now adjust the RTT values in the all_rtts dictionary, such that if the last rtt is not *, add 0s
#If the last rtt is *, then add 0s till the current hop length, but from the last hop -1
#Change all *s to 0s (for visualizing purposes)
with open('JSON/RTT_values.json', 'w') as f:
    json.dump(all_rtts,f)




