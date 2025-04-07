import re
import os
import ipaddress
from datetime import datetime
import csv
from pathlib import Path


#write all cidrs into csv files now and only write those >= /24 ones into .dat file


#input files
file_name1 = Path(__file__).resolve().parent / ".." / "Data_set" / "bulk_whois" / "Networks.txt"
file_name2 =  Path(__file__).resolve().parent / ".." / "Data_set" / "bulk_whois" / "Organizations.txt"


#output_cidr
tmp_csv_file = Path(__file__).resolve().parent / ".." / "whois_data" / "cidr_orgName.csv"
#netranges that don't have organization names
no_orgname_file = Path(__file__).resolve().parent / ".." / "whois_data" / "no_orgname.csv"
#netranges that don't have organization name and >= /24
csv_file = Path(__file__).resolve().parent / ".." / "whois_data" / "cidr_greater_25.csv"
small_cidr_csv_file = Path(__file__).resolve().parent / ".." / "whois_data" / "small_cidr.csv"
dat_file = Path(__file__).resolve().parent / ".." / "whois_data" / "cidr.dat"


#divide network ranges into cidrs
def range_to_cidr(netrange):
    #print(netrange)
    nnn = netrange.split("-")
    start_ip = nnn[0].split()[0]
    end_ip = nnn[1].split()[0]
    ##print(end_ip)
    return [cidr for cidr in ipaddress.summarize_address_range(ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip))]

#read the bulk whois data and divide the data into blocks
def extract_blocks(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    blocks = re.split(r'\n{3,}', content.strip()) 
    return blocks

#extrac the orgID and netrange from each block
def process_network_blocks(block):
    lines = block.split("\n")
    netrange = ""
    orID = ""
    flag = 0
    for line in lines:
        if line.startswith("NetRange:"):
            flag = 1
            netrange = line.split("NetRange:")[-1].strip()
            if ":" in netrange:
                return ["!", "!"]
    if flag == 0:
        print("This block doesn't have netrange field:")
        print(block)
        return ["!", "!"]
    flag = 0
    for line in lines:
        if line.startswith("OrgID:"):
            flag = 1
            orID = line.split("OrgID:")[-1].strip()
    if flag == 0:
        print(f"{netrange} doesn't have orgID")
    return [netrange, orID]

#extrac the orgID and orgname from each block
def process_org_blocks(block):
    lines = block.split("\n")
    orgID = ""
    orgname = ""
    flag = 0
    for line in lines:
        if line.startswith("OrgID:"):
            orgID = line.split("OrgID:")[-1].strip()
            flag = flag + 1
        if line.startswith("OrgName:"):
            orgname = line.split("OrgName:")[-1].strip()
            flag = flag + 2
    if flag == 3:
        return [orgID, orgname]
    elif flag == 1:
        print("No orgname:")
        print(block)
        return ["!", "!"]
    elif flag == 2:
        print("No orgID")
        print(block)
        return ["!", "!"]
    else:
        print("No orgname and orgID:")
        print(blocks)   
        return ["!", "!"]         

#write the output cidr into csv file
def save_file(triple, file_name):
    with open(file_name, "a", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(triple)



print(f"The process starts and time is {str(datetime.now())}")
org_dic = {}
org_id = []
org_name = []
r = 0
org_block = extract_blocks(file_name2)
for block in org_block:
    orgID, orgname = process_org_blocks(block)
    if orgID != "!":
        #print(orgID)
        org_dic.update({orgID:orgname})
print(f"Find {str(len(org_dic))} (orgID, orgName) pairs")

#Write the titile line into csv file
if not os.path.exists(tmp_csv_file ):
    with open(tmp_csv_file , "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CIDR", "netrange", "orgname"]) 
if not os.path.exists(no_orgname_file):
    with open(no_orgname_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CIDR", "netrange", "orgID"])  
print(f"Extracting orgID and orgName finished at {str(datetime.now())}")
r = 0
cidrs = []
net_range = []
orgName_set = []
netrange_block = extract_blocks(file_name1)
print(f"processing netrange to orgName at {str(datetime.now())}")


r = 1
for block in netrange_block:
    netrange, orgid = process_network_blocks(block)
    if netrange != "!":
        if r % 200000 == 0:
            print(f"{r / len(org_dic) * 100:.2f}% netranges have been processed")
            print(datetime.now())
        oorgname = org_dic.get(orgid, "No found")
        cidrs = range_to_cidr(netrange)
        if oorgname == "No found":
            for c in cidrs:
                t = (c, netrange, orgid)
                save_file(t, no_orgname_file)
        else:
            for c in cidrs:
                r = r + 1
                t = (c, netrange, oorgname)
                save_file(t, tmp_csv_file )




print(datetime.now())

if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CIDR", "netrange", "orgname"])
        f.flush()
if not os.path.exists(small_cidr_csv_file):
    with open(small_cidr_csv_file , "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CIDR", "netrange", "orgname"]) 

r = 1
with open(tmp_csv_file, newline="", encoding="utf-8") as t_csvfile, open(csv_file, "a+") as c_file, open(small_cidr_csv_file, "a+") as s_file, open(dat_file, "w") as dat:
    reader = csv.reader(t_csvfile)
    next(reader)
    for row in reader:
        cidr = ipaddress.ip_network(row[0], strict=False)
        if cidr.num_addresses >= 256:
            r = r+1
            writer = csv.writer(c_file)
            writer.writerow(row)
            dat.write(str(cidr) + "\t" + str(r) + "\n")
        else:
            writer = csv.writer(s_file)
            writer.writerow(row)
