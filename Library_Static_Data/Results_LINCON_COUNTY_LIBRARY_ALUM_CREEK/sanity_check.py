import os
import sys
import json
from tqdm import tqdm

out_file = 'extracted_cidrs.txt'

json_folder = './Library_Static_Data/Results_LINCON_COUNTY_LIBRARY_ALUM_CREEK/JSON/'
json_folders = [f for f in os.listdir(json_folder)]
json_files = []
for folder in json_folders:
    folder_path = os.path.join(json_folder, folder)
    if os.path.isdir(folder_path):
        for file in os.listdir(folder_path):
            if file.endswith('.json'):
                json_files.append(os.path.join(folder_path, file))

cidrs = []
for file in json_files:
    cidr = file.split('-')[-1].split('.json')[0].strip().replace('?','/')
    cidrs.append(cidr)

to_check_cidrs = []
to_check_file = './Library_Static_Data/Results_LINCON_COUNTY_LIBRARY_ALUM_CREEK/filtered_dup_removed.txt'
with open(to_check_file, 'r') as f:
    lines = f.readlines()
    to_check_cidrs = [line.strip().split('-')[1] for line in lines if line.strip()]

#checking for overlap
overlap = []
for cidr in tqdm(cidrs):
    if cidr in to_check_cidrs:
        overlap.append(cidr)

overlap = list(set(overlap))
print(f'Overlap: {len(overlap)}')