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
    state="${state[$i]}"

    echo "Library: $library"
    echo "Latitude: $lan"
    echo "Longitude: $lon"
    echo "Name: $name"
    echo "State: $state"
    echo
   
   #Filter CIDR
   #Check if filtered_Ips.txt exists, only run if it doesn't
   echo "Checking if filtered_ips.txt exists..."
    if [ ! -f "./Library_Static_Data/Results_$name/filtered_ips.txt" ]; then
        python3 ./residential_remover.py ./Library_Static_Data/Results_"$name"/final_cidrs.txt ./Library_Static_Data/Results_"$name"/filtered_ips.txt
    else
        echo "Filtered IPs already exist for $name, skipping..."
    fi

    echo "Checking if vantage point group exists..."
    if [ ! -f "./Library_Static_Data/Results_$name/grouped_probes.json" ]; then
        python3 ./vantage_point_selector.py "$name" "$lan" "$lon" "$state"
    else
        echo "Grouped probes already exist for $name, skipping..."
    fi


    #Move the producer,consumer,download files to the results directory

    echo
done