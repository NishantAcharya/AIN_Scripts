import json
import csv

def convert_hitlist(hitlist_file, output_file):
    with open(hitlist_file, 'r') as f:
        lines = f.readlines()
        data = {}
        for i in range(1,len(lines)-1):
            line = lines[i].split('\t')
            score = line[0].strip()
            ip = line[1].strip()

            data[ip] = score
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

#def convert_support_file(support_file,output_file):

def hex_to_ip(hex_string):
    if len(hex_string) != 8:
        raise ValueError("Invalid hexadecimal string length. Must be 8 characters.")

    # Split the hex string into 4 parts of 2 characters each
    parts = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]

    # Convert each part to decimal
    decimal_values = [int(part, 16) for part in parts]

    # Join the decimal values with dots
    ip_address = ".".join(map(str, decimal_values))

    return ip_address

# Example usage
hex_string = "C0A80101"
ip_address = hex_to_ip(hex_string)
print(f"The IP address is: {ip_address}") # Output: The IP address is: 192.168.1.1


#convert_hitlist('CSV/internet_address_hitlist_it109w-20240926.fsdb','JSON/hitlist.json')