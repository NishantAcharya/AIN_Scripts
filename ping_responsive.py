import subprocess
#Read the unique_ips.txt file
with open('unique_ips.txt','r') as f:
    b = f.readlines()
    b = [x.strip() for x in b]

#Create a reponsive ip_file text
with open('responsive_ips.txt','w') as f:
    result = []
    for ip in b:
        p = subprocess.Popen(['ping', '-c', '10', ip]) # runs ping in background
        result.append(p) # store the Popen object for later result retrieval

    for ip, p in zip(b, result):
        if p.wait() == 0:
            f.write(ip+'\n')

#The non responsive IPs are removed from the overall list of IPs

#The IPs from the traceroutes --> Ping to find the non responsive ones (Mark them as inf RTT)
#The responsive RTTs are pinged from vantage points 
#To select the VP, find first 3(A number to start with) closest VPs and record their distance
#Then find the first 3 furthest VPs and record their distance
#Once found, find 3 VPs in the middle of the two sets of VPs
#Ping the responsive IPs from these VPs, and penalize the IPs confidence score based on how far away is the RTT from the 
#Closest VP RTT * 2/3 speed of light - distance between VP and IP
## IF the IP is close to the actual location, it's score would be comparatively higher
##Why not a higher RTT? We need a score and just using RTT will give a qualitative value (Is the smallest RTT from the closest VP?)
##This way the RTT can be quantified for the eventual merge.

print('Done')
#This step is to be added right before the pings are sent -- so the unique_ips file needs to be extracted before the hits