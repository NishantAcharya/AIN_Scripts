import json
import pandas as pd
import statistics


csv_file = '../../Census_collection/CSV/sub_sampled_data.csv'
val_file = './Selected_libraries.txt'
input_df = pd.read_csv(csv_file)
input_names = input_df['Name'].tolist()
input_cidr_len = input_df['CIDR'].tolist()
input_pop_density = input_df['pop_d'].tolist()

with open(val_file, 'r') as f:
    lines = f.readlines()
    selected_libs = [line.strip() for line in lines]

selected_density = []
cidr_count = 0
# MANUALLY UPDATE THIS SECTION for the number and type of libraries
my_max_count = 9000
alex_max_count = 40000
alex_libs = []
my_libs = []
for i in range(len(input_names)):
    name = input_names[i]
    num_cidrs = input_cidr_len[i]
    pop_density = input_pop_density[i]

    if name not in selected_libs:
        continue

    if cidr_count > alex_max_count:
        print(f"Total CIDRS for Alex's API -- {cidr_count}, Max allowed -- {alex_max_count}")
        print(f"Total Selected Libraries: {len(alex_libs)}")
        print
        break

    selected_density.append(pop_density)
    alex_libs.append(name)
    cidr_count += num_cidrs