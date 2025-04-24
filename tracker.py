import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

directory = './Library_Static_Data/'
folders = os.listdir(directory)

og = []
final = []
#Error in folders -- remove
for folder in folders:
    path = os.path.join(directory, folder)
    original_cidrs = os.path.join(path, 'final_cidrs.txt')
    filtered_cidrs = os.path.join(path, 'filtered_ips.txt')
    #Check if the files exist
    if not os.path.exists(original_cidrs) or not os.path.exists(filtered_cidrs):
        print(f"Error: File '{original_cidrs}' or '{filtered_cidrs}' not found in {folder}.")
        continue

    with open(original_cidrs, 'r') as f:
        lines = f.readlines()
        og.append(len(lines))

    with open(filtered_cidrs, 'r') as f:
        lines = f.readlines()
        final.append(len(lines))

#Plotting the data
plt.figure(figsize=(10, 5))
plt.plot(og, label='Original CIDRs', marker='o')
plt.plot(final, label='Final CIDRs', marker='x')
plt.title('Comparison of Original and Final CIDRs')
plt.xlabel('Library Number')
plt.ylabel('Number of CIDRs')
plt.legend()

plt.savefig('CIDR_comparison.png')

