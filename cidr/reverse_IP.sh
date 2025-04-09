#!/bin/bash

libraries=()
lans=()
lons=()
name=()
state=()

# Read from the Library_data.txt file and separate lines on '-'
while IFS='-' read -r part1 part2 part3 part4 part5 ; do
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
    echo "$part3"
done < ./Library_data.txt




for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"
    name="${name[$i]// /_}"

    #echo "Library: $library"
    #echo "Latitude: $lan"
    #echo "Longitude: $lon"
    #echo "Name: $name"
    #echo
    #echo
# 
#     #Check if outputs folder exists
#     if [ -d "./outputs" ]; then
#         echo "The outputs folder exists"
#     else
#         mkdir outputs
#     fi
# 
#     # Get CIDR
#     python3 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
#     echo
#     echo
# 
#     # Get provider names for this library
#     python3 ./FCC_Provider/FCC_providers.py "$library"
#     echo
#     echo
# 
#     # If the set of organization names and provider names exist, skip this step
#     if [ -e "./TF-IDF/nameset.txt" ]; then
#         echo "The nameset file exists"
#     else
#         python3 ./TF-IDF/generate_name_set.py
#     fi
#     echo
#     echo
# 
#     # Run TF-IDF to get keywords for each name
#     python3 ./TF-IDF/TF_IDF.py
#     echo
#     echo
# 
#     # Generate the (cidr, netrange, organization name) tuple
#     if [ -e "./Local_whois/cidr.dat" ]; then
#         echo "local whois could run now."
#     else
#         python3 ./Local_whois/Netrange_OrgName_pair.py
#     fi
#     echo
#     echo
# 
#     # Do local whois
#     python3 ./Local_whois/local_whois.py
# 
#     # Check if the Results folder exists in Done_Results
#     if [ -d "../Results_$name" ]; then
#         echo "The Results folder exists in Done_Results"
#     else
#         mkdir ../Results_"$name"
#     fi
# 
#     # Move the output folder to Done_Results
#     mv ./outputs ../Results_"$name"
done
