import json
import numpy as np
import matplotlib.pyplot as plt
import math

#Read the RTT_Values JSON file
with open('JSON/RTT_values.json', 'r') as f:
    data = json.load(f)

def extend_update_lists(list,l):
    current_len = len(list)
    needed_length = l - current_len
    extended_list = [0 for _ in range(needed_length)]
    list.extend(extended_list)
    updated_list = []
    for i in list:
        if i == '*':
            updated_list.append(0)
            continue
        updated_list.append(i)
    return updated_list,l


def get_median_difference(l):
    difference_list = []
    for i in range(1,len(l)):
        if l[i] == 0 or l[i-1] == 0:
            continue
        difference_list.append(abs(l[i] - l[i-1]))
    
    difference_list.sort()
    median = np.median(difference_list)
    return median


CURRENT_LEN = 20

#For the rest of the code: set each RTT such that the median difference is is preserved
#Question --> Should the median RTT be updated at each pass?
new_data = {}
for key in data.keys():
    new_data[key] = []

for key in data.keys():
    probe_data = data[key]
    for rtt_vals in probe_data:
        if rtt_vals[-1] == '*':
            continue
        updated_list,l = extend_update_lists(rtt_vals,CURRENT_LEN)
        median = get_median_difference(updated_list)
        new_list = []
        for rtt in updated_list:
            
