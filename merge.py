import json
import os
from tqdm import tqdm

input_file = 'validation_input.txt'
directory = './Library_Static_Data/'
merge_file_name = 'merged_data.json'
with open(input_file, 'r') as file:
    lines = file.readlines()
    folders = ['Results_' + line.strip().split('~')[2].replace(' ', '_') for line in lines if line.strip()]

for folder in folders:
    folder_path = os.path.join(directory, folder)
    if not os.path.exists(folder_path):
        print(f"Folder {folder} does not exist.")
        continue

    org_cache_file = os.path.join(folder_path, 'org_cache.json')
    if not os.path.exists(org_cache_file):
        print(f"File {org_cache_file} does not exist.")
        continue
    
    cidr_asn_file = os.path.join(folder_path, 'cidr_asn_mapping.json')
    if not os.path.exists(cidr_asn_file):
        print(f"File {cidr_asn_file} does not exist.")
        continue

    with open(org_cache_file, 'r', encoding='utf-8') as f:
        org_cache_data = json.load(f)

    with open(cidr_asn_file, 'r', encoding='utf-8') as f:
        cidr_asn_data = json.load(f)

    merged_data = {}
    for asn, ip in tqdm(cidr_asn_data.items(), desc=f"Merging {folder}"):
        if asn in cidr_asn_data:
            merged_data[asn] = {
                'org': org_cache_data.get(ip, None),
                'IP': ip
            }
    with open(os.path.join(folder_path, merge_file_name), 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    break  # Uncomment this line to process all folders