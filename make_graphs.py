#This file will go through each folder and save information for the graphs
import os
import json
import ipaddress
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import ast
import numpy as np
######Log CDF Helper######
def log_cdf(values, title="Log CDF", log_base=10, show_stats=True, save_path=None):
    """Create log-scale CDF plot with y-axis 0-100% and x-axis as log values."""
    vals = np.array(values)
    pos_vals = vals[vals > 0]
    if len(pos_vals) == 0:
        raise ValueError("No positive values for log transformation")
    
    sorted_vals = np.sort(pos_vals)
    percentiles = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals) * 100
    log_vals = np.log(sorted_vals) / np.log(log_base) if log_base != np.e else np.log(sorted_vals)
    
    plt.figure(figsize=(8, 5))
    plt.plot(log_vals, percentiles, 'b-', linewidth=2)
    plt.xlabel(f"Log{log_base if log_base != np.e else ''} Values")
    plt.ylabel("Cumulative Percentage (%)")
    plt.title(title)
    plt.ylim(0, 100)  # Fixed: should be 100, not 1
    plt.grid(True, alpha=0.3)
    
    if show_stats:
        plt.axvline(np.mean(log_vals), color='r', linestyle='--', alpha=0.7, 
                   label=f'Mean: {np.mean(log_vals):.2f}')
        plt.axvline(np.median(log_vals), color='g', linestyle='--', alpha=0.7, 
                   label=f'Median: {np.median(log_vals):.2f}')
        plt.legend()
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()

def log_cdf_multi(value_lists, labels=None, title="Log CDF Comparison", log_base=10, save_path=None):
    """Compare multiple datasets on log CDF plot."""
    if labels is None:
        labels = [f"Data {i+1}" for i in range(len(value_lists))]
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(value_lists)))
    
    for vals, label, color in zip(value_lists, labels, colors):
        pos_vals = np.array(vals)[np.array(vals) > 0]
        if len(pos_vals) == 0: 
            continue
        
        sorted_vals = np.sort(pos_vals)
        percentiles = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals) * 100
        log_vals = np.log(sorted_vals) / np.log(log_base) if log_base != np.e else np.log(sorted_vals)
        plt.plot(log_vals, percentiles, color=color, linewidth=2, label=label)
    
    plt.xlabel(f"Log{log_base if log_base != np.e else ''} Values")
    plt.ylabel("Cumulative Percentage (%)")
    plt.title(title)
    plt.ylim(0, 100)  # Fixed: should be 100, not 1
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    plt.show()
#########

directory = './Library_Static_Data_og/'
input_file = 'validation_libraries.txt'
folders = []
with open(input_file, 'r') as f:
    lines = f.readlines()
    folders = ['Results_' + line.strip().split('~')[2].replace(' ', '_') for line in lines]

folders = [folder for folder in folders if os.path.isdir(os.path.join(directory, folder))] 
#Grab the number of IPs from the CIDRs in the final_filtered.txt
#Grab the AS list len from the as_list.txt
#Grab the final_CIDRs.txt


final_ips = {}
start_ips = {}
provider_ips = {}
as_list = {}
provider_list = {}
artifact_list_c = {}
artifact_list_i = {}

for folder in tqdm(folders):
    folder_path = os.path.join(directory, folder)
    
    final_filtered_file = os.path.join(folder_path, 'final_filtered.txt')
    final_cidrs_file = os.path.join(folder_path, 'final_cidrs.txt')
    as_list_file = os.path.join(folder_path, 'asn_list.txt')
    provider_ips_file = os.path.join(folder_path, 'provider_ips.txt')
    provider_set_file = os.path.join(folder_path, 'provider_set.txt')
    trace_cidr_artifact_file = os.path.join(folder_path, 'trace_cidr_artifacts.txt')
    trace_ip_artifact_file = os.path.join(folder_path, 'trace_ip_artifacts.txt')

    name = folder.split('Results_')[1].replace('_', ' ')
    
    # 4 graphs
    if not os.path.exists(final_filtered_file) or not os.path.exists(final_cidrs_file) or not os.path.exists(as_list_file):
        print(f"Skipping {folder} due to missing files.")
        continue
    
    with open(final_filtered_file, 'r') as f:
        temp = f.readlines()
        final_ips_lines = [line.strip() for line in temp if line.strip()]
        for cidr in final_ips_lines:
            cidr = str(cidr)
            host = cidr.strip().split('/')[1]
            num_ips = 2**(32 - int(host))
            try:
                final_ips[name] += num_ips
            except KeyError:
                final_ips[name] = num_ips

    with open(final_cidrs_file, 'r') as f:
        temp = f.readlines()
        final_cidrs_lines = [line.strip() for line in temp if line.strip()]
        for cidr in final_cidrs_lines:
            cidr = str(cidr)
            host = cidr.strip().split('/')[1]
            num_ips = 2**(32 - int(host))
            try:
                start_ips[name] += num_ips
            except KeyError:
                start_ips[name] = num_ips

    with open(provider_ips_file,'r') as f:
        temp = f.readlines()
        provider_ips_lines = [line.strip() for line in temp if line.strip()]
        #Assuming colocation of /26
        for _ in provider_ips_lines:
            num_ips = 2**(32 - 26)
            try:
                provider_ips[name] += num_ips
            except KeyError:
                provider_ips[name] = num_ips

    with open(provider_set_file, 'r') as f:
        temp = f.readlines()
        provider_set_lines = [line.strip() for line in temp if line.strip()]
        pvdr_set = list(set(provider_set_lines))
        try:
            provider_list[name] += len(pvdr_set)
        except KeyError:
            provider_list[name] = len(pvdr_set)
    
    with open(as_list_file, 'r') as f:
        temp = f.readlines()
        temp = [ast.literal_eval(line.strip()) for line in temp if line.strip()]
        as_list_lines = []
        for item in temp:
            as_list_lines.extend(item)
        asn_set = list(set(as_list_lines))
        try:
            as_list[name] += len(asn_set)
        except KeyError:
            as_list[name] = len(asn_set)

    with open(trace_cidr_artifact_file, 'r') as f:
        temp = f.readlines()
        trace_cidr_artifact_lines = [line.strip() for line in temp if line.strip()]
        try:
            artifact_list_c[name] += len(trace_cidr_artifact_lines)
        except KeyError:
            artifact_list_c[name] = len(trace_cidr_artifact_lines)
    
    with open(trace_ip_artifact_file, 'r') as f:
        temp = f.readlines()
        trace_ip_artifact_lines = [line.strip() for line in temp if line.strip()]
        try:
            artifact_list_i[name] += len(trace_ip_artifact_lines)
        except KeyError:
            artifact_list_i[name] = len(trace_ip_artifact_lines)


final_ips_grph = './graphs/final_ips.png' #final and start ips
provider_ips_grph = './graphs/provider_ips.png' # final and provider IPs
as_list_grph = './graphs/as_list.png' # AS list length
provider_list_grph = './graphs/provider_list.png' # Provider list length
artifact_list_grph = './graphs/artifact_list.png' # Artifact cidr and ip

#making the graphs
log_cdf_multi([list(final_ips.values()), list(start_ips.values())],
                labels=['Final IPs', 'Start IPs'],
                title='Log CDF of Final and Start IPs',
                log_base=10,
                save_path=final_ips_grph)

log_cdf_multi([list(provider_ips.values()), list(final_ips.values())],
                labels=['Provider IPs', 'Final IPs'],
                title='Log CDF of Provider and Final IPs',
                log_base=10,
                save_path=provider_ips_grph)

log_cdf_multi([list(as_list.values())],
                labels=['AS List Length'],
                title='Log CDF of AS List Length',
                log_base=10,
                save_path=as_list_grph)

log_cdf_multi([list(provider_list.values())],
                labels=['Provider List Length'],
                title='Log CDF of Provider List Length',
                log_base=10,
                save_path=provider_list_grph)

log_cdf_multi([list(artifact_list_c.values()), list(artifact_list_i.values())],
                labels=['CIDR Artifacts', 'IP Artifacts'],
                title='Log CDF of CIDR and IP Artifacts',
                log_base=10,
                save_path=artifact_list_grph)
    
    
    
