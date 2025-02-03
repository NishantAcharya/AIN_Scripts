import json
import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import plotly.express as px
import random


PROBES = [21003,55451,1009747,10342,1145,52574,53097,55692,1008382,30350]

#FUnction to get all json files in a folder
def get_all_files_in_folder(folder_path):
    try:
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except FileNotFoundError:
        print(f"Error: Folder '{folder_path}' not found.")
        return []

#Function to read a json file and get the min RTT per probe
def read_json(file):
    with open(file, 'r') as f:
        data = json.load(f)
    
    #Holding space for probe RTTs
    probe_rtt = {21003:-1,55451:-1,1009747:-1,10342:-1,1145:-1,52574:-1,53097:-1,55692:-1,1008382:-1,30350:-1,'Failed':False}

    #Holding space for if the ping reached or not, [dup,rcvd,sent]
    probe_reached = {21003:[0,0,0],55451:[0,0,0],1009747:[0,0,0],10342:[0,0,0],1145:[0,0,0],52574:[0,0,0],53097:[0,0,0],55692:[0,0,0],1008382:[0,0,0],30350:[0,0,0],'Failed':False}

    #Checking for Failed Pings
    if type(data) == dict and 'Failed' in data.keys():
        probe_rtt['Failed'] = True
        probe_reached['Failed'] = True
        return probe_rtt,probe_reached

    #Finding Min RTT per probe and if dest Replied
    for probe_data in data:

        probe_id = probe_data['prb_id']
        min_rtt = probe_data['min']
            
        if probe_rtt[int(probe_id)] == -1 or min_rtt < probe_rtt[int(probe_id)]:
            probe_rtt[int(probe_id)] = min_rtt

        probe_reached[int(probe_id)][0] += probe_data['dup']
        probe_reached[int(probe_id)][1] += probe_data['rcvd']
        probe_reached[int(probe_id)][2] += probe_data['sent']
    
    return probe_rtt,probe_reached


#Code to create a continous Density function for 1 array
def cdf(data_all,bin_size):
    cdfs = []
    for key in data_all.keys():
        data = data_all[key]
        # getting data of the histogram 
        count, bins_count = np.histogram(data, range(0,60)) 
        
        # finding the PDF of the histogram using count values
        pdf = count / sum(count) 
        
        # using numpy np.cumsum to calculate the CDF 
        # We can also find using the PDF values by looping and adding 
        cdf = np.cumsum(pdf)
        plt.plot(bins_count[1:], cdf, label=f"CDF : {key}")
    plt.title("CDF of Min RTT for the given probes to last responsive IP on traceroutes to Burlington Public Library")
    plt.xlabel("Min RTTs in ms")
    plt.ylabel("Percentage of Values in a given Bin/Range of Min RTTs")
    plt.legend()
    plt.show()



def main(folder_path):
    files = get_all_files_in_folder(folder_path)
    #ping_data ==> IP:[[min_rtt_21003_run1, min_rtt_21003_run2],[min_rtt_55451_run1,..],...,[min_rtt_30350_run1,..]]
    ping_data = {'IP':[],21003:[],55451:[],1009747:[],10342:[],1145:[],52574:[],53097:[],55692:[],1008382:[],30350:[],'Failed':[]}
    
    #rtt_data ==> IP:[[min_rtt_21003_run1, min_rtt_21003_run2],[min_rtt_55451_run1,..],...,[min_rtt_30350_run1,..]]
    rchd_data = {'IP':[],21003:[],55451:[],1009747:[],10342:[],1145:[],52574:[],53097:[],55692:[],1008382:[],30350:[],'Failed':[]}
    
    for file in tqdm(files):
        file_path = folder_path + '/' + file
        ip = file.split('-')[-3].strip()
        ip_check = ip in ping_data['IP']
        if not ip_check:
            ping_data['IP'].append(ip)
            rchd_data['IP'].append(ip)
        
        probe_rtt,probe_reached = read_json(file_path)

        for key in probe_rtt.keys():
            if ip_check:
                index = ping_data['IP'].index(ip)
                ping_data[key][index].append(probe_rtt[key])
                rchd_data[key][index].append(probe_reached[key])
            else:
                ping_data[key].append([probe_rtt[key]])
                rchd_data[key].append([probe_reached[key]])
            

    #Saving the data
    ping_df = pd.DataFrame(ping_data)
    rchd_df = pd.DataFrame(rchd_data)

    #to_csv
    ping_df.to_csv('ping_data.csv',index=False)
    rchd_df.to_csv('reached_data.csv',index=False) #There is array of False Entries

    fail_count = 0
    didnt_reach_count = 0
    ip_probe = []
    unique_non_reachable_ips = set()
    total_unique_ips = set(ping_df['IP'])

    min_rtt_data = {21003:[],55451:[],1009747:[],10342:[],1145:[],52574:[],53097:[],55692:[],1008382:[],30350:[]}
    probe_fail_count = {21003:0,55451:0,1009747:0,10342:0,1145:0,52574:0,53097:0,55692:0,1008382:0,30350:0}
    for i in range(ping_df['IP'].size):
        if ping_df['Failed'][i].count(True) > 0:
            fail_count += ping_df['Failed'][i].count(True)
        for key in min_rtt_data.keys():
            if np.min(ping_df[key][i]) == -1:
                didnt_reach_count += 1
                ip_probe.append(str(ping_df['IP'][i])+'-'+str(key))
                unique_non_reachable_ips.add(ping_df['IP'][i])
                probe_fail_count[key] += 1
                continue
            min_rtt_data[key].append(np.min(ping_df[key][i]))
    
    #print(min_rtt_data)
    print(f"Failed Pings: {fail_count}")
    len_each_probe = [len(min_rtt_data[key]) for key in min_rtt_data.keys()]
    print(f"Didn't Reach Destination: {didnt_reach_count/sum(len_each_probe)}")
    print(f"IPs with Probe not reaching: {len(unique_non_reachable_ips)}")
    print(f"Total Unique IPs: {len(total_unique_ips)}")
    print(f"IP-Probe not reaching: {len(ip_probe)}")
    print(f"Probe Fail Count: {probe_fail_count}")

    #Getting 10 random IP values to test the difference between hardware and software probes
    random_ips = random.sample(total_unique_ips,10)
    print(f"Random IPs: {random_ips}")

    #Plot min_rtt data as a cdf with each probe as a different line

    #cdf(min_rtt_data,1000)
        

main('/home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/JSON/2025-01-21')

    
