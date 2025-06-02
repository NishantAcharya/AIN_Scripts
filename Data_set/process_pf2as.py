#The goal of this is to shorten prefix to as, like removing duplicate entries

file = './Data_set/Prefix_AS.pfx2as'  # The path to prefix to as file

with open(file, 'r') as f:
    lines = f.readlines()

ips = []
prefixes = []
asns = []
for line in lines:
    parts = line.strip().split()
    if len(parts) >= 3:
        ips.append(parts[0])
        prefixes.append(parts[1])
        asns.append(parts[2])

final_set = {}
print(ips[0], prefixes[0], asns[0])
for i in range(len(ips)):
    ip = ips[i]
    prefix = prefixes[i]
    asn = asns[i]

    try:
        temp = final_set[ip]
        if int(prefix) < int(final_set[ip][0]):
            final_set[ip] = (prefix, asn)
    except KeyError:
        final_set[ip] = (prefix,asn)

output_file = './Data_set/Prefix_AS.pfx2as_short.pfx2as'
with open(output_file, 'w') as f:
    for ip, (prefix, asn) in final_set.items():
        f.write(f"{ip} {prefix} {asn}\n")

    
        
