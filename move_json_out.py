import json
import os
#Grab the JSON folders inside all and move them to a seperate place

#Check if storage folder exists
if not os.path.exists("storage"):
    os.makedirs("storage")

directory = './Library_Static_Data'
out_directory = './storage'

# Loop through all the folders in the directory
for foldername in os.listdir(directory):
    folder_path = os.path.join(directory, foldername)
    #Check if JSON folder exists if not continue
    if not os.path.exists(os.path.join(folder_path, 'JSON')):
        continue
    #Move the JSON folder to the storage folder
    json_path = os.path.join(folder_path, 'JSON')
    os.rename(json_path, os.path.join(out_directory, foldername + '_JSON'))