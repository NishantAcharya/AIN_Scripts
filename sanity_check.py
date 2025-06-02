import os

input_file = 'validation_input.txt'
input_directory = './Library_Static_Data/'
filename = 'filtered_ips.txt'
with open(input_file, 'r') as f:
    lines = f.readlines()
    val_libs = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines]

total_count = 0
per_day_count = 110000
for val in val_libs:
    input_file_path = os.path.join(input_directory, val, filename)
    with open(input_file_path, 'r') as f:
        lines = f.readlines()
        total_count += len(lines)
    print(f"{val}: {len(lines)} IPs found in {input_file_path}")

print(f"Total count of IPs across all libraries: {total_count}")
print(f"Approx Days to process: {total_count // per_day_count + (1 if total_count % per_day_count > 0 else 0)}")