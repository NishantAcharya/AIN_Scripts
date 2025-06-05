import os
from tqdm import tqdm
import json

def merge_json_files(file1, file2, output_file):
    """Merge two JSON files"""
    with open(file1, 'r') as f1:
        data1 = json.load(f1)
    
    with open(file2, 'r') as f2:
        data2 = json.load(f2)
    
    # Merge dictionaries or lists
    if isinstance(data1, dict) and isinstance(data2, dict):
        merged = {**data1, **data2}
    elif isinstance(data1, list) and isinstance(data2, list):
        merged = data1 + data2
    else:
        merged = data2  # Use second file if types don't match
    
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"JSON files merged into: {output_file}")

def merge_text_files_remove_duplicates(file1, file2, output_file):
    """Merge text files and remove duplicate lines"""
    lines = set()
    
    # Read lines from both files
    with open(file1, 'r') as f1:
        lines.update(line.strip() for line in f1 if line.strip())
    
    with open(file2, 'r') as f2:
        lines.update(line.strip() for line in f2 if line.strip())
    
    # Write unique lines
    with open(output_file, 'w') as f:
        for line in sorted(lines):
            f.write(line + '\n')
    
    print(f"Text files merged (no duplicates) into: {output_file}")

input_file = 'validation_input.txt'
base_dir = './Library_Static_Data_og/'
dest_dir = './Library_Static_Data/'

target_folder = 'JSON'
merge_files = [
    'filtered_dup_removed.txt',
    'final_cidrs.txt',
    'filtered_ips.txt',
    'final_filtered.txt',
    'grouped_probes.json',
    'statistic.txt'
]

with open(input_file, 'r') as file:
    lines = file.readlines()
    folders = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines if line.strip()]

for folder in tqdm(folders):
    source_folder = os.path.join(base_dir, folder, target_folder)
    dest_folder = os.path.join(dest_dir, folder, target_folder)

    if not os.path.exists(source_folder):
        continue
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    # Copy JSON subfolders and files
    for foldername in os.listdir(source_folder):
        source_path = os.path.join(source_folder, foldername)
        if not os.path.isdir(source_path):
            continue
        dest_path = os.path.join(dest_folder, foldername)

        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for filename in os.listdir(source_path):
            source_file = os.path.join(source_path, filename)
            dest_file = os.path.join(dest_path, filename)

            if not os.path.exists(dest_file):
                with open(source_file, 'r') as src_file:
                    content = src_file.read()
                with open(dest_file, 'w') as dst_file:
                    dst_file.write(content)

    # Merge specified files using new functions
    for merge_file in merge_files:
        source_merge_file = os.path.join(base_dir, folder, merge_file)
        dest_merge_file = os.path.join(dest_dir, folder, merge_file)

        if os.path.exists(source_merge_file):
            os.makedirs(os.path.dirname(dest_merge_file), exist_ok=True)
            
            if merge_file.endswith('.json'):
                # Use JSON merge function for .json files
                if os.path.exists(dest_merge_file):
                    merge_json_files(dest_merge_file, source_merge_file, dest_merge_file)
                else:
                    # If destination doesn't exist, just copy the source
                    with open(source_merge_file, 'r') as src:
                        content = src.read()
                    with open(dest_merge_file, 'w') as dst:
                        dst.write(content)
            else:
                # Use text merge function for .txt files
                if os.path.exists(dest_merge_file):
                    merge_text_files_remove_duplicates(dest_merge_file, source_merge_file, dest_merge_file)
                else:
                    # If destination doesn't exist, just copy the source
                    with open(source_merge_file, 'r') as src:
                        content = src.read()
                    with open(dest_merge_file, 'w') as dst:
                        dst.write(content)
