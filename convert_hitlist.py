import json
import csv
from tqdm import tqdm

def convert_hitlist(hitlist_file, output_file):
    with open(hitlist_file, 'r') as f:
        lines = f.readlines()
        data = {}
        for i in range(1,len(lines)-1):
            line = lines[i].split('\t')
            score = line[1].strip()
            ip = line[-1].strip()

            data[ip] = score
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

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

def convert_hitlist_support(hitlist_file, output_file):
    with open(hitlist_file, 'r') as f:
        lines = f.readlines()
        data = {}
        for i in range(1,len(lines)-1):
            line = lines[i].split('\t')
            cidr = hex_to_ip(line[0].strip()) + '/24'
            octets = line[1].strip().split(',')
            if octets[0] == '-':
                continue
            chosen_ips = []
            for octet in octets:
                ip_last_octet = int(octet.strip(),16) #Hex String
                ip = '.'.join(cidr.split('.')[:-1]) + '.' + str(ip_last_octet)
                chosen_ips.append(ip)
            data[cidr] = chosen_ips

    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

print('Converting Hitlist')
convert_hitlist('CSV/internet_address_hitlist_it109w-20240926.fsdb','JSON/hitlist.json')
print('Converting Hitlist Support')
convert_hitlist_support('CSV/internet_address_verfploeter_hitlist_it109w-20240926.fsdb','JSON/hitlist_support.json')
print('Done')