import numpy as npy
import ast
import os
from tqdm import tqdm
import pandas as pd

directory = './Library_Static_Data/'
input_file = './validation_input.txt'
with open(input_file, 'r') as f:
    lines = f.readlines()
    val_libs = [line.strip().split('~')[2].strip() for line in lines]

selected_libs  = []
selected_cidrs = []


for i in range(len(val_libs)):

    name = val_libs[i]

    name = f"Results_{name.strip().replace(' ','_')}"
    selected_libs.append(name)

with open('Selected_libraries_val.txt', 'w') as f:
    for lib in selected_libs:
        f.write(lib.split('Results_')[1].replace('?','/').replace('_',' ') + '\n')
#Get a list of folders in the directory -- remove any folder that doesnot contain a library from the library_data.txt(500 sub sampled)

input_folders = []
for folder in os.listdir(directory):
    if os.path.isdir(os.path.join(directory, folder)) and folder in selected_libs:
        input_folders.append(folder)

#From each folder copy the filtered_dup_removed.txt
inpts = []
for folder in input_folders:
    path = os.path.join(directory, folder, 'filtered_dup_removed.txt')
    main_file = os.path.join(directory, folder, 'filtered_ips.txt')
    base_file = os.path.join(directory, folder, 'final_cidrs.txt')
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            folder.replace('-','~')
            lines = [line.strip()+'-'+str(folder) for line in lines]
            print(folder, len(lines))
            inpts.extend(lines)
        #################
        with open(main_file, 'r') as f:
            main_lines = f.readlines()
            main_lines = [line.strip()+'-'+str(folder) for line in main_lines]
            print(len(main_lines))

        with open(base_file, 'r') as f:
            base_lines = f.readlines()
            base_lines = [line.strip()+'-'+str(folder) for line in base_lines]
            print(len(base_lines))
        ####################
        print('------------')


with open('input_val_final.txt', 'w') as f:
    for line in tqdm(inpts):
        f.write(line + '\n')