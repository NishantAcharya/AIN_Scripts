import os

def get_all_files_in_folder(folder_path):
  """
  Gets a list of all files within a given folder.

  Args:
    folder_path: The path to the folder.

  Returns:
    A list of file names within the folder.
  """
  try:
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
  except FileNotFoundError:
    print(f"Error: Folder '{folder_path}' not found.")
    return []

# Example usage:
folder_path = "/home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/JSON/Jan-08-2025"
all_files = get_all_files_in_folder(folder_path)

if all_files:
  print("Files in the folder:")
  for file in all_files:
    print(file)