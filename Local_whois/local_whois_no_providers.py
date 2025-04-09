import pyasn
from datetime import datetime
import linecache
import ipaddress
import random
import csv
import io
from pathlib import Path

# Initialize module and load IP to ASN database
# the sample database can be downloaded or built - see below


#input files
input_cidr = "./reverse_geolocation/cidrs_near_library.txt"
csv_file = "./whois_data/cidr_greater_25.csv"
dat_file = "./whois_data/cidr.dat"
black_list_file = "./Data_set/blacklist.txt"

#output files
output_file = "./outputs/final_cidrs.txt"
all_orgname_file = "./outputs/all_orgname.txt"
black_org_file = "./outputs/after_blacklist_orgname.txt"
stat_file = "./outputs/statistic.txt"

asndb = pyasn.pyasn(str(dat_file))

test_mode = 1

def clean_string(text):
    return " ".join(word.replace(".", "") for word in text.split())   

def check_ip_in_range(ip, netrange):
    nnn = netrange.split("-")
    start_range = nnn[0].split()[0]
    end_range = nnn[1].split()[0]
    if int(ipaddress.ip_address(ip)) >= int(ipaddress.ip_address(start_range)) and int(ipaddress.ip_address(ip)) <= int(ipaddress.ip_address(end_range)):
        return True
    else:
        return False

#this is used to check whether a cidr is in a net range
def check_cidr_in_range(cidr, netrange):
    nnn = netrange.split("-")
    start_range = nnn[0].split()[0]
    end_range = nnn[1].split()[0]
    network = ipaddress.ip_network(cidr, strict=False)
    start_cidr = network[0]
    end_cidr = network[-1] 
    #print(f"{start_cidr} -- {end_cidr}")
    #print(f"{start_range} -- {end_range}")
    if int(ipaddress.ip_address(start_cidr)) >= int(ipaddress.ip_address(start_range)) and int(ipaddress.ip_address(end_cidr)) <= int(ipaddress.ip_address(end_range)):
        return True
    else:
        return False

def get_cidr_num(cidr):
    cc = ipaddress.IPv4Network(cidr)
    return(cc.num_addresses)

#Build a class to store cidrs, net range and organization names
class NetRan:
    def __init__(self, cidr):
        self.cidr_set = []
        self.cidr_set.append(cidr)
        network = ipaddress.IPv4Network(cidr)
        randome_ip = str(random.choice(list(network.hosts())))
        csv_line_num = asndb.lookup(randome_ip)[0]
        csv_line = linecache.getline(str(csv_file), csv_line_num).strip()
        #print(csv_line)
        fields = next(csv.reader(io.StringIO(csv_line)))
        self.netrange = fields[1]
        self.OrgName = clean_string(fields[2])
        #print(self.netrange)
        #print(type(self.netrange))
        #print(self.OrgName)
        #print(type(self.OrgName))
    def check_and_add(self, cidr):
        if check_cidr_in_range(cidr, self.netrange) == True:
            self.cidr_set.append(cidr)
            return True
        else:
            return False
    def get_Netrange(self):
        return self.netrange
    def get_cidr_set(self):
        return self.cidr_set
    def get_orgname(self):
        return self.OrgName


Current_Org = None
Org_set = []

r = 0 
with open(input_cidr, mode ='r')as file:
  #next(csvFile)
  for line in file:
        #print(line[0])
        input_c = line.strip()
        r = r + 1
        if r % 100000 == 0:
            print(f"{str(r)} lines have been processed")
        if Current_Org != None:
            f = Current_Org.check_and_add(input_c)
            if f == False:
                Org_set.append(Current_Org)
                Current_Org = NetRan(input_c)
        else:
            Current_Org = NetRan(input_c)

Org_set.append(Current_Org)




blacklist = []
with open(black_list_file, "r") as b:
    for line in b:
        blacklist.append(line.strip())

if test_mode == 1:
    orgname_set = []
    for org in Org_set:
        orgn = org.get_orgname()
        if orgn not in orgname_set:
            orgname_set.append(orgn)
    with open(all_orgname_file, "w") as file:
        for orgn in orgname_set:
            file.write(orgn)
            file.write("\n")
        


black_orgs = [org for org in Org_set if any(keyword in org.get_orgname().lower().replace(" ", "") for keyword in blacklist)]
flitered_black_orgs = list(set(Org_set) - set(black_orgs))



total_num = 0
total_ip = 0
with open(output_file, "w") as output:
    for org in flitered_black_orgs:
        cidrs = org.get_cidr_set()
        i = 0 
        for cidr in cidrs:
            total_num = total_num + 1
            total_ip = total_ip + get_cidr_num(cidr)
            output.write(cidr+"\n")


print(f"{str(total_num)} cidrs remains")
print(f"{str(total_ip)} ips remains")

if test_mode == 1:
    orgname_set = []
    with open(black_org_file, "w") as file:
        org_set = []
        for org in flitered_black_orgs:
            if org.get_orgname() not in org_set:
                org_set.append(org.get_orgname())
        for orgn in org_set:
            file.write(orgn)
            file.write("\n")            


with open(stat_file, "w") as ofile:
    ofile.write("No filtering\n")
    ofile.write(f"{str(total_num)} cidrs in total\n")
    ofile.write(f"{str(total_ip)} ips remains")



