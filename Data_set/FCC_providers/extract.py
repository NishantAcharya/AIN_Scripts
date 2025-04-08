import zipfile
import os
import shutil
import sys

def extract_zip_files_in_folders():
    current_dir = os.getcwd()
    for folder in os.listdir(current_dir):
        folder_path = os.path.join(current_dir, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.zip'):
                    zip_path = os.path.join(folder_path, file)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_path = os.path.join(folder_path, os.path.splitext(file)[0])
                        os.makedirs(extract_path, exist_ok=True)
                        zip_ref.extractall(extract_path)
                        print(f"Extracted {file} to {extract_path}")
                        # Move extracted files to the parent folder
                        for extracted_file in os.listdir(extract_path):
                            extracted_file_path = os.path.join(extract_path, extracted_file)
                            destination_path = os.path.join(folder_path, extracted_file)
                            if os.path.exists(destination_path):
                                os.remove(destination_path)  # Overwrite by removing the existing file
                            shutil.move(extracted_file_path, folder_path)
                        
                        # Remove the now-empty extracted folder
                        os.rmdir(extract_path)

                        # Move the original zip file to 'Data_dump'
                        data_dump_folder = os.path.join(folder_path, 'Data_dump')
                        os.makedirs(data_dump_folder, exist_ok=True)
                        shutil.move(zip_path, data_dump_folder)

                        # Move any non-CSV file to 'Data_dump'
                        for item in os.listdir(folder_path):
                            item_path = os.path.join(folder_path, item)
                            if os.path.isfile(item_path) and not item.endswith('.csv'):
                                shutil.move(item_path, data_dump_folder)
                        
                        #Move any folder to 'Data_dump'
                        for item in os.listdir(folder_path):
                            item_path = os.path.join(folder_path, item)
                            if os.path.isdir(item_path) and item != 'Data_dump':
                                shutil.move(item_path, data_dump_folder)


extract_zip_files_in_folders()

