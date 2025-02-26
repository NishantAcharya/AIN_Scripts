import numpy as np
import pandas as pd
from tqdm import tqdm
import json

def read_uscities():
    """
    Reads the uscities.csv file and returns a DataFrame with the following columns:
    - city
    - city_ascii
    - state_id
    - state_name
    - county_fips
    - county_name
    - county_fips_all
    - county_name_all
    - lat
    - lng
    - population
    - density
    - source
    - military
    - incorporated
    - timezone
    - ranking
    - zips
    - id
    - _created
    - _updated
    - _etag
    """
    return pd.read_csv('uscities.csv')

#create a dictionary, in the format of {state:{geolocation:[],population_density:[]}}
def get_state_geoloc_density(df):
    state_dict = {}
    for index,row in tqdm(df.iterrows()):
        state = row['state_name']
        if state not in state_dict:
            state_dict[state] = {'geolocation':[],'population_density':[]}
        state_dict[state]['geolocation'].append((row['lat'],row['lng']))
        state_dict[state]['population_density'].append(row['density'])
    return state_dict

#get the top density gelocs and densities
def get_top_density_indices(state_dict):
    top_density_indices = {}
    for state in state_dict:
        density = state_dict[state]['population_density']
        top_density_indices[state] = np.argsort(density)[-int(len(density)*0.1):]
        state_dict[state]['top_density_geoloc'] = [state_dict[state]['geolocation'][i] for i in top_density_indices[state]]
        state_dict[state]['top_density'] = [density[i] for i in top_density_indices[state]]

#save the dictioary as a json file
def save_state_geoloc_density(state_dict):
    with open('state_geoloc_density.json','w') as f:
        json.dump(state_dict,f)

def main():
    print('Processing uscities.csv...')
    df = read_uscities()
    state_dict = get_state_geoloc_density(df)
    get_top_density_indices(state_dict)
    save_state_geoloc_density(state_dict)
    print('Done')

main()
