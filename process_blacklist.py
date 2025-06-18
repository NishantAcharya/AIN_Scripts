import pandas as pd
import os
import json
from tqdm import tqdm
import json
filename = 'cheatsheet.json'
input_file = 'Data_set/fixed_output.csv'
catdf = pd.read_csv(input_file, encoding='utf-8')
catdf = catdf.loc[:, ~catdf.columns.str.contains('^Unnamed')]

json_data = {}
isp = 'Internet Service Provider (ISP)'
university = 'Colleges, Universities, and Professional Schools'
# Read an entire row in the dataframe (example: read the first row)
for index, row in catdf.iterrows():
    # process each row here
    row = list(row)
    asn = int(row[1].split('AS')[1])
    if asn not in json_data:
        json_data[asn] = None
    if isp in row:
        json_data[asn] = 'ISP'
    elif university in row:
        json_data[asn] = 'University'
    else:
        json_data[asn] = 'Other'

# Write the JSON data to a file
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)