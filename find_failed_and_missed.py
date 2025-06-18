import json
import os

input_file = 'validation_input.txt'
directory = './Library_Static_Data/'
target_file = 'Trace_data.json'

with open(input_file, 'r') as file:
    lines = file.readlines()
lines = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines if line.strip()]

output_file = 'failed_and_missed.txt'
failed = 0
reached = 0
partially_failed = 0
for folder in lines:

    folder_path = os.path.join(directory, folder)
    if not os.path.exists(folder_path):
        print(f"Folder {folder} does not exist in {directory}.")
        continue

    files = os.listdir(folder_path)
    if not files:
        print(f"Folder {folder} is empty.")
        continue

    target_path = os.path.join(folder_path, target_file)
    with open(target_path, 'r') as file:
        data = json.load(file)

    for ip_keys in data:
        trace_info = data[ip_keys]

        failed_bool = trace_info.get('Failed', True)

        # Check for int keys or str keys with int values
        for key, value in trace_info.items():
            if isinstance(key, str) or isinstance(value, int):
                response = True

            else:
                response = False

        if response and not failed_bool:
            reached += 1
        elif response and failed_bool:
            partially_failed += 1
        elif not response and failed_bool:
            failed += 1

    with open(output_file, 'a') as out_file:
        out_file.write(f"{folder} - Failed: {failed}, Reached: {reached}, Partially Failed: {partially_failed}\n")

    print(f"{folder} - Failed: {failed}, Reached: {reached}, Partially Failed: {partially_failed}")
                