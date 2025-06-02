#This file will go through each folder and save information for the graphs
import os
import json
import ipaddress
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import ast

directory = './Library_Static_Data_og/'
input_file = 'validation_libraries.txt'
folders = []
with open(input_file, 'r') as f:
    lines = f.readlines()
    folders = ['Results_' + line.strip().split('~')[2].replace(' ', '_') for line in lines]

folders = [folder for folder in folders if os.path.isdir(os.path.join(directory, folder))]

for folder in tqdm(folders):
    folder_path = os.path.join(directory, folder)
    final_cidrs_file = os.path.join(folder_path, 'final_cidrs.txt')
    
#Grab the length of the final_filtered.txt and final_cidrs.txt
#Grab the number of IPs from the CIDRs in the final_filtered.txt
#Grab the AS list len from the as_list.txt
    