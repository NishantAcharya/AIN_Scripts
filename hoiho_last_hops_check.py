import requests
import json
import socket
import multiprocessing
import ast
#Save the data in the form 3 last hop ips per file
#if there is a * in the middle? --> it won't get looked up, if there is no info, put in an '' string
#The output I am looking for is a (cc,st,place) tuple for each domain -- if no info found put ('', '', '')

#Preparing the data

def is_integer(str_value):
    try:
        int(str_value)
        return True
    except ValueError:
        return False

def get_hops(file):
    with open(file, 'r') as f:
        data = json.load(f)
    
    #Last 3 hops per IP in order


    final = []

    for ip in data:
        for probe in data[ip]:
            #Only probe ids will be ints as keys
            hops = []
            order = []
            if not is_integer(probe):
                continue

            
            try:
                last_hop_ip = data[ip][probe]['Last_Hop_IP']
            except:
                print(data[ip][probe])
                print(ip)
                print(probe)
                raise Exception("No last hop IP found")
            
            for i in range(len(data[ip][probe]['Traceroute'])-1,0,-1):
                hop = data[ip][probe]['Traceroute'][i]

                if hop == last_hop_ip:
                    hops.insert(0,hop)
                    if i == 0:
                        hops.insert(0,'*')
                        hops.insert(0,'*')
                    elif i == 1:
                        hops.insert(0,data[ip][probe]['Traceroute'][i-1])
                        hops.insert(0,'*')
                    else:
                        hops.insert(0,data[ip][probe]['Traceroute'][i-1])
                        hops.insert(0,data[ip][probe]['Traceroute'][i-2])

                    break
            if len(hops) == 0:
                hops.insert(0,'*')
                hops.insert(0,'*')
                hops.insert(0,'*')

            order.insert(0,str(ip)+'-'+str(probe))
            final.append(str(hops)+'-'+str(order))

    with open('hoiho_data.txt', 'w') as f:
        for item in final:
            f.write("%s\n" % item)
    print('Finished writing the file')
    return final


final = get_hops('Trace_data/Burlington.json')

######################### HOIHO PART ##############################

def reverse_dns_lookup(ip):
    try:
        result = socket.gethostbyaddr(ip)
        return {ip: result[0]}  # Return the hostname
    except:
        return {ip: None}  # Return None if no hostname is found
    
def perform_lookups(ip_list):
    with multiprocessing.Pool() as pool:
        results = pool.map(reverse_dns_lookup, ip_list)
    return dict(item for result in results for item in result.items())


ip_list = ['8.8.8.8','*','1.1.1.1','*','*','69.139.164.45', '24.153.80.226', '73.254.57.210']
results = perform_lookups(ip_list)
print(results)



#Creating the hoiho query
def create_hoiho_query(data):
    #Assuming the above format "[ips]-[dest_ip-probe]"
    #do a rdns lookup for all of them

    #Parsing the data -- every 3 ips split into a different probe
    all_ips = []
    for line in data:
        ips = ast.literal_eval(line.split('-')[0])
        all_ips.extend(ips)

    #Performing the reverse DNS lookup
    results = perform_lookups(all_ips)

    domain_list = []
    for ip in all_ips:
        domain = results[ip]
        if domain is not None:
            domain_list.append(domain)
        else:
            domain_list.append('*') #Placeholder for no domain found

    
    data = domain_list
    url = 'https://api.hoiho.caida.org/lookups'
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Request was successful.")
        response_data = response.json()
        print(response_data)
        # Process the response data as needed
        return response_data
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)



    return None
                
                
create_hoiho_query(final[:3])

###PARSE THE HOIHO RESULTS