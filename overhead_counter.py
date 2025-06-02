import os
import sys
done = 0
new_requirements = 0

done_directory = './Library_Static_Data_og/'
new_directory = './Library_Static_Data/'
input_file = 'validation_input.txt'
inputs = []
with open(input_file, 'r') as f:
    inputs = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in f.readlines()]

for folder in os.listdir(done_directory):
    if folder not in inputs:
        continue
    if not os.path.isdir(os.path.join(done_directory, folder)):
        continue
    
    done_path = os.path.join(done_directory, folder, 'filtered_dup_removed.txt')
    new_path = os.path.join(new_directory, folder, 'filtered_dup_removed.txt')

    done_check = True
    new_check = True
    
    if not os.path.exists(done_path):
        print(f"Done file does not exist: {done_path}")
        done_check = False
    
    if not os.path.exists(new_path):
        print(f"New file does not exist: {new_path}")
        new_check = False
    
    if done_check:
        with open(done_path, 'r') as f:
            done_lines = f.readlines()
        done_set = set(line.strip() for line in done_lines)
        done += len(done_set)

    if new_check:
        with open(new_path, 'r') as f:
            new_lines = f.readlines()
        new_set = set(line.strip() for line in new_lines)
        new_requirements += len(new_set)

print(f"Total unique lines in done files: {done}")
print(f"Total unique lines in new files: {new_requirements}")
print(f"Total unique lines in new files that are not in done files: {new_requirements-done}")
    