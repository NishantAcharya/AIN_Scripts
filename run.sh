#!/bin/bash

libraries=()
lans=()
lons=()
name=()
state=()

# Read from the Library_data.txt file and separate lines on '-'
while IFS='~' read -r part1 part2 part3 part4 part5; do
    part1=${part1//%/~}
    part2=${part2//%/~}
    part3=${part3//%/~}
    part4=${part4//%/~}
    part5=${part5//%/~}
    lans+=("$part1")
    lons+=("$part2")
    names+=("$part3")
    state+=("$part4")
    libraries+=("$part5")
done < ./validation_input.txt
# Get the CDIRs from all the folders
for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"
    name="${names[$i]// /_}"
    name="${name//\//?}"
    state="${state[$i]}"
    echo "Library: $library"
    echo "Latitude: $lan"
    echo "Longitude: $lon"
    echo "Name: $name"
    echo "State: $state"
    echo

    #Filter CIDR
    #Check if filtered_Ips.txt exists, only run if it doesn't
    echo "Getting filtered IPs..."
    python3 ./residential_remover.py ./Library_Static_Data/Results_"$name"/final_cidrs.txt ./Library_Static_Data/Results_"$name"/filtered_ips.txt ./Library_Static_Data/Results_"$name"/hitlist_count.txt
    #Read the final_cidr.text file based on the correct directory and then add the directory name to the file, after the CIDR
    #Then add the data to common inpt.txt file in the root folder
    echo "Removing duplicates..."
    python3 ./duplicate_remover.py ./Library_Static_Data/Results_"$name"/filtered_ips.txt ./Library_Static_Data/Results_"$name"/filtered_dup_removed.txt ./Library_Static_Data/Results_"$name"/total_cidr.txt

    echo "Finding Vantage Points..."
    python3 ./vantage_point_selector.py "$name" "$lan" "$lon" "$state"
done

#Creating the input file, producer file, consumer file and download file