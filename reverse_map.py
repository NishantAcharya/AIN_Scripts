import os
import json

def reverse_dict(d):
    return {v: k for k, v in d.items()}

def process_json_files(root_dir, target_filenames):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename in target_filenames:
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    reversed_data = reverse_dict(data)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(reversed_data, f, indent=2, ensure_ascii=False)
                    print(f"Reversed: {file_path}")

if __name__ == "__main__":
    # Set the root directory to search for target JSON files
    root_directory = './Library_Static_Data/'
    target_files = {"org_cache.json", "cidr_asn_mapping.json"}
    process_json_files(root_directory, target_files)