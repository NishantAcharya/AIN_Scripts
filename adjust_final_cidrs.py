import os
from tqdm import tqdm
import ipaddress

#Go over the input file, go to the library static data
#Then copy the final_cidrs.txt in the same folder
#Check if the same folder exists in og folder --> This count should be 30
#Load the final cidr from theog folder, if it doesn't exist set it to empyt list
#Go over the first list and remove any items that are in the og list
#Print the cidr count
input_file = 'validation_input.txt'
input_directory = './Library_Static_Data/'
og_directory = './Library_Static_Data_og/'
with open(input_file, 'r') as f:
    lines = f.readlines()
    val_libs = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines]

weird_count = 0
total = 0
for folder in tqdm(val_libs):
    filename = 'final_cidrs.txt'
    input_file_path = os.path.join(input_directory, folder, filename)
    og_file_path = os.path.join(og_directory, folder, filename)
    
    if not os.path.exists(input_file_path):
        print(f"File {input_file_path} does not exist, skipping...")
        continue

    with open(input_file_path, 'r') as f:
        input_final_cidrs = [line.strip() for line in f.readlines() if line.strip()]

    if not os.path.exists(og_file_path):
        og_cidrs = []
    else:
        with open(og_file_path, 'r') as f:
            og_cidrs = [line.strip() for line in f.readlines() if line.strip()]

    #Duplicate the final_cidrs.txt file
    duplicate_file_path = os.path.join(input_directory, folder, 'final_cidrs_duplicate.txt')
    with open(duplicate_file_path, 'w') as f:
        for cidr in input_final_cidrs:
            f.write(cidr + '\n')

    #Remove any items in input_final_cidrs that are in og_cidrs 
    input_final_cidrs = [cidr for cidr in input_final_cidrs if cidr not in og_cidrs]
    print(folder,len(input_final_cidrs), len(og_cidrs))

    with open(input_file_path, 'w') as f:
        for cidr in input_final_cidrs:
            f.write(cidr + '\n')

print(f"Weird count: {weird_count}, Total processed: {total}")

    




    
