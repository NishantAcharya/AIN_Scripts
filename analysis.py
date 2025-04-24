import json
import numpy as np
from tqdm import tqdm
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt

#Load the rtt value file
#Make this dynamic later
with open('Library_Static_Data/Results_PARROTTSVILLE_COMMUNITY_LIBRARY/rtt_vals.json', 'r') as f:
    rtt_vals = json.load(f)

last_hop = []
second_last_hops = []
min_deviation = []
for key in rtt_vals.keys():
    ip_val = rtt_vals[key]
    for item in ip_val:
        last_hop.append(ip_val[item]['last_rtt'])
        second_last_hops.append(ip_val[item]['second_last_rtt'])
        min_deviation.append(ip_val[item]['min_rtt_devation'])

#Plot Last hop and second last hop
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(last_hop, label='Last Hop', color='blue')
plt.plot(second_last_hops, label='Second Last Hop', color='orange')
plt.title('Last Hop vs Second Last Hop')
plt.xlabel('Index')
plt.ylabel('IP Address')
plt.legend()
plt.grid()
plt.subplot(2, 1, 2)
plt.plot(min_deviation, label='Minimum Deviation', color='green')
plt.title('Minimum Deviation')
plt.xlabel('Index')
plt.ylabel('RTT Deviation')
plt.legend()
plt.grid()
plt.savefig('rtt_analysis.png')