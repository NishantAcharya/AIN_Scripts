import os
import docx2txt
from tqdm import tqdm

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except PermissionError:
        print(f"Permission denied: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

def remove_empty_lines(filepath):
    """Removes empty lines from a file.

    Args:
        filepath: The path to the file.
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()

    non_empty_lines = [line for line in lines if line.strip()]

    with open(filepath, 'w') as file:
        file.writelines(non_empty_lines)


def iterate_files_with_extension(directory, extension):
    for root, dirs, files in os.walk(directory):
        for file in tqdm(files):
            if file.endswith(extension):

                new_file_name = file.split('.')[0] + '.txt'
                new_file_path = os.path.join(root, new_file_name)

                current_file_path = os.path.join(root, file)

                with open(current_file_path, 'rb') as infile:
                    with open(new_file_path, 'w', encoding='utf-8') as outfile:
                        try:
                            doc = docx2txt.process(infile)
                            outfile.write(doc)
                            
                            
                        except Exception as e:
                            print(f"Error processing file {current_file_path}: {e}")
                            raise e

                remove_empty_lines(new_file_path)       
                delete_file(current_file_path)
                

iterate_files_with_extension('.','.docx')
