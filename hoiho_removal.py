import requests
import time
import pandas as pd
import numpy as np
from tqdm import tqdm


#Will get rdns for each IP, after giltering along with cidrs

#returns hoiho data
def get_hoiho_data(dmn):
    url = "https://api.hoiho.caida.org/lookups/"+dmn
    
    for _ in range(2):
        response = requests.get(url)
        
        if response.status_code == 200:
            break
        
        time.sleep(1)
    
    if response.status_code != 200:
        return None
    
    return response.json()

#Readnthe txt rnds file and separate the IPs and RDNS
with open('rdns_union.txt', 'r') as f:
    lines = f.readlines()

#BDFRKY --> CLLI Code
#VBD --> Locode
#BED  --> IATA Code
#BED,Bedford,BDFR --> Place
#Kentucky,KY --> State

count = 0

hoiho_filtered = {'IP':[],'RDNS':[]}
#Removind data we know for sure is outside of bedford
for line in tqdm(lines):
    ip,rdns = line.split(' ')
    ip = ip.strip()
    rdns = rdns.strip()
    
    #Sleeping  because of the rate limit
    #time.sleep(0.4)
    
    hoiho_data = get_hoiho_data(rdns)
    
    if hoiho_data is not None:
        if hoiho_data['summary']['hostnames_matched'] >= 1:
            matches = hoiho_data['matches']
            for match in matches:
                try:
                    clli = str(match['clli']).lower()
                except KeyError:
                    clli = None
                try:
                    locode = str(match['locode']).lower()
                except KeyError:
                    locode = None
                try:
                    iata = str(match['iata']).lower()
                except KeyError:
                    iata = None
                try:
                    place = str(match['place']).lower()
                except KeyError:
                    place = None
                
                if clli == 'bfrky' or locode == 'vbd' or iata == 'bed' or place == 'bedford' or place == 'bdf' or place == 'bdfr':
                    hoiho_filtered['IP'].append(ip)
                    hoiho_filtered['RDNS'].append(rdns)
                    break
            #Not info so keeping it
        else:
            hoiho_filtered['IP'].append(ip)
            hoiho_filtered['RDNS'].append(rdns)
    else:
        hoiho_filtered['IP'].append(ip)
        hoiho_filtered['RDNS'].append(rdns)
        
df = pd.DataFrame(hoiho_filtered)
df.to_csv('hoiho_filtered_union.csv', index = False)
print('File saved')