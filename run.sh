#!/bin/bash

libraries=()
lans=()
lons=()
name=()
state=()

# Read from the Library_data.txt file and separate lines on '-'
while IFS='-' read -r part1 part2 part3 part4 part5; do
    part1=${part1//\//-}
    part2=${part2//\//-}
    part3=${part3//\//-}
    part4=${part4//\//-}
    part5=${part5//\//-}
    lans+=("$part1")
    lons+=("$part2")
    name+=("$part3")
    state+=("$part4")
    libraries+=("$part5")
done < ./Library_data.txt

for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"
    name="${name[$i]// /_}"

    echo "Library: $library"
    echo "Latitude: $lan"
    echo "Longitude: $lon"
    echo "Name: $name"
    echo

   #get RDNS
   #Check if the rdns_info.json exists, only then run
    if [ ! -f "./Results_$name/rdns_info.json" ]; then
        python3 ./Fcc_removal_rdns.py ./Results_"$name"/outputs/final_cidrs.txt ./Results_"$name"/rdns_info.json
    else
        echo "RDNS info already exists for $name, skipping..."
    fi
   
   #Filter CIDR
   #Check if filtered_Ips.txt exists, only run if it doesn't
    if [ ! -f "./Results_$name/filtered_ips.txt" ]; then
        python3 ./residential_remover.py ./Results_"$name"/rdns_info.json ./Results_"$name"/filtered_ips.txt
    else
        echo "Filtered IPs already exist for $name, skipping..."
    fi


done