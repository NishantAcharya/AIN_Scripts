import numpy as npy
import ast
import os
from tqdm import tqdm
import pandas as pd
#load the library names from seleceted_libraries_done.txt
with open('Selected_libraries_done.txt', 'r') as f:
    lines = f.readlines()
    selected_libs_done = [line.strip() for line in lines]

#Open the library static data as main directory
directory = './Library_Static_Data/'
input_file = '/home/nishant-acharya/Desktop/Census_collection/CSV/sub_sampled_data.csv' #---> Sampled 500 libraries
df = pd.read_csv(input_file)
input_names = df['Name'].tolist()
input_cidr_len = df['CIDR'].tolist()
selected_libs  = []
selected_cidrs = []
#MANUALLY UPDATE THIS SECTION for the numeber and type of libraries
#current_count = 25
current_high_cidr = 1000
current_low_cidr = 0
Max_count = 9000
#######Alex API inputs
current_cidr_count = 0
for i in range(len(input_names)):
    name = input_names[i]
    num_cidrs = input_cidr_len[i]

    if name in selected_libs_done:
        continue

    if num_cidrs > current_high_cidr or num_cidrs < current_low_cidr:
        continue

    name = f"Results_{name.strip().replace(' ','_')}"
    selected_libs.append(name)
    #######
    if current_cidr_count + num_cidrs >= Max_count:
        print(f"Reached the limit of {Max_count} CIDRs")
        print(f"Total Selected Libraries: {len(selected_libs)}")
        print(f"Total CIDRS: {current_cidr_count}")
        break
    current_cidr_count += num_cidrs
    #######

with open('Selected_libraries_alex.txt', 'w') as f:
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
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            folder.replace('-','~')
            lines = [line.strip()+'-'+str(folder) for line in lines]
            inpts.extend(lines)


with open('input_alex.txt', 'w') as f:
    for line in tqdm(inpts):
        f.write(line + '\n')

############################################################ Running a second time for the second set of inputs
#Open the library static data as main directory
directory = './Library_Static_Data/'
input_file = '/home/nishant-acharya/Desktop/Census_collection/CSV/sub_sampled_data.csv' #---> Sampled 500 libraries
df = pd.read_csv(input_file)
input_names = df['Name'].tolist()
input_cidr_len = df['CIDR'].tolist()
selected_libs  = []
selected_cidrs = []
#MANUALLY UPDATE THIS SECTION for the numeber and type of libraries
#current_count = 25
current_high_cidr = 1000
current_low_cidr = 0
Max_count = 9000
with open('Selected_libraries_alex.txt', 'r') as f:
    lines = f.readlines()
    selected_libs_alex = [line.strip() for line in lines]
#######
current_cidr_count = 0
for i in range(len(input_names)):

    name = input_names[i]
    num_cidrs = input_cidr_len[i]
    if name in selected_libs_alex or name in selected_libs_done:
        continue

    if num_cidrs > current_high_cidr or num_cidrs < current_low_cidr:
        continue

    name = f"Results_{name.strip().replace(' ','_')}"
    selected_libs.append(name)
    #######
    if current_cidr_count + num_cidrs >= Max_count:
        print(f"Reached the limit of {Max_count} CIDRs")
        print(f"Total Selected Libraries: {len(selected_libs)}")
        print(f"Total CIDRS: {current_cidr_count}")
        break
    current_cidr_count += num_cidrs
    #######

with open('Selected_libraries_nish.txt', 'w') as f:
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
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            folder.replace('-','~')
            lines = [line.strip()+'-'+str(folder) for line in lines]
            inpts.extend(lines)


with open('input_nish.txt', 'w') as f:
    for line in tqdm(inpts):
        f.write(line + '\n')

##############################Running a third time for the third set of inputs -- Vijeth's API
#Open the library static data as main directory
directory = './Library_Static_Data/'
input_file = '/home/nishant-acharya/Desktop/Census_collection/CSV/sub_sampled_data.csv' #---> Sampled 500 libraries
df = pd.read_csv(input_file)
input_names = df['Name'].tolist()
input_cidr_len = df['CIDR'].tolist()
selected_libs  = []
selected_cidrs = []
#MANUALLY UPDATE THIS SECTION for the numeber and type of libraries
#current_count = 25
current_high_cidr = 10000
current_low_cidr = 8000
Max_count = 9000
with open('Selected_libraries_alex.txt', 'r') as f:
    lines = f.readlines()
    selected_libs_alex = [line.strip() for line in lines]

with open('Selected_libraries_nish.txt', 'r') as f:
    lines = f.readlines()
    selected_libs_nish = [line.strip() for line in lines]
#######
current_cidr_count = 0
for i in range(len(input_names)):

    name = input_names[i]
    num_cidrs = input_cidr_len[i]
    if name in selected_libs_alex or name in selected_libs_done or name in selected_libs_nish:
        continue

    if num_cidrs > current_high_cidr or num_cidrs < current_low_cidr:
        continue

    name = f"Results_{name.strip().replace(' ','_')}"
    selected_libs.append(name)
    #######
    if current_cidr_count + num_cidrs >= Max_count:
        print(f"Reached the limit of {Max_count} CIDRs")
        print(f"Total Selected Libraries: {len(selected_libs)}")
        print(f"Total CIDRS: {current_cidr_count}")
        break
    current_cidr_count += num_cidrs
    #######

with open('Selected_libraries_nish_2.txt', 'w') as f:
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
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            folder.replace('-','~')
            lines = [line.strip()+'-'+str(folder) for line in lines]
            inpts.extend(lines)


with open('input_nish_2.txt', 'w') as f:
    for line in tqdm(inpts):
        f.write(line + '\n')

#########################Running a 4th time -- validation IPs
#Adjust the directory and lib data to include all the libraries you have done so far
#Then select only the IPs whose CIDRs are not in the above list
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
    print(path)
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
            folder.replace('-','~')
            lines = [line.strip()+'-'+str(folder) for line in lines]
            inpts.extend(lines)


with open('input_val_final.txt', 'w') as f:
    for line in tqdm(inpts):
        f.write(line + '\n')