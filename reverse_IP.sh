
#!/bin/bash

libraries=()
lans=()
lons=()
names=()
states=()

# Read from the Library_data.txt file and separate lines on '-'
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
done < ./other_libs.txt

for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"
    name="${names[$i]// /_}"

    echo "Processing library: $library"
    echo "LAN: $lan"
    echo "Longitude: $lon"
    echo "Name: $name"

    # Checking if we have done this library already
    output_directory="./Library_Static_Data/Results_$name"
    output_file="./outputs/final_cidrs.txt"
    all_orgname_file="./outputs/all_orgname.txt"
    filter_orgname_file="./outputs/providers_orgname.txt"
    black_org_file="./outputs/after_blacklist_orgname.txt"
    stat_file="./outputs/statistic.txt"

    # Verify if all files are already in the output directory
    echo "Checking if Library has been processed..."
    if [ -d "$output_directory" ] && \
        [ -e "$output_directory/final_cidrs.txt" ] && \
        [ -e "$output_directory/all_orgname.txt" ] && \
        [ -e "$output_directory/after_blacklist_orgname.txt" ] && \
        [ -e "$output_directory/statistic.txt" ]; then
         echo "All files are already in $output_directory. Skipping this library."
         continue
    fi




    # Generate the (cidr, netrange, organization name) tuple, this is the most time-consuming part, usually about 2 hours to run
    if [ -e "./whois_data/cidr.dat" ]; then
        echo "whois database has already existed"
    else
        echo "Now generating the local whois database, this might cost about 2 hours"
        python3 ./Local_whois/Netrange_OrgName_pair.py
    fi
    # Get provider names for this library
    python3 ./FCC_Provider/FCC_providers.py "$library"
    exit_code=$?  
    # Don't get any FIPS code
    if [ $exit_code -eq 1 ]; then
        echo "No FIPS code found"
        echo
        python3 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        # Do local whois
        python3 ./Local_whois/local_whois_no_providers.py
    # Get FIPS code, but don't get provider in this census block
    elif [ $exit_code -eq 2 ]; then
        echo "No provider found"
        echo
        python3 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        # Do local whois
        python3 ./Local_whois/local_whois_no_providers.py
    else
        echo "Get FCC providers"
        echo 
        # If the set of organization names and provider names exist, skip this step
        if [ -e "./TF-IDF/nameset.txt" ]; then
            echo "The nameset file exists"
        else
            echo "Now generating the nameset for TF-IDF"
            python3 ./TF-IDF/generate_name_set.py
        fi
        echo
        # Run TF-IDF to get keywords for each name
        python3 ./TF-IDF/TF_IDF.py
        echo
        # Get cidrs near the library
        python3 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        # Do local whois and filtering
        python3 ./Local_whois/local_whois.py
    fi
    # Move the files to the respective folder, made using the library name
    if [ -d "./Library_Static_Data/Results_$name" ]; then
        echo "Directory ./Library_Static_Data/Results_$name already exists."
    else
        mkdir -p ./Library_Static_Data/Results_"$name"
        echo "Creating directory ./Library_Static_Data/Results_$name"
    fi

    # Check if the output files exist and move them to the respective directory

    if [ -e "$output_file" ]; then
        mv "$output_file" ./Library_Static_Data/Results_"$name"/
        echo "Moved $output_file to ./Library_Static_Data/Results_$name/"
    fi

    if [ -e "$all_orgname_file" ]; then
        mv "$all_orgname_file" ./Library_Static_Data/Results_"$name"/
        echo "Moved $all_orgname_file to ./Library_Static_Data/Results_$name/"
    fi

    if [ -e "$filter_orgname_file" ]; then
        mv "$filter_orgname_file" ./Library_Static_Data/Results_"$name"/
        echo "Moved $filter_orgname_file to ./Library_Static_Data/Results_$name/"
    fi

    if [ -e "$black_org_file" ]; then
        mv "$black_org_file" ./Library_Static_Data/Results_"$name"/
        echo "Moved $black_org_file to ./Library_Static_Data/Results_$name/"
    fi

    if [ -e "$stat_file" ]; then
        mv "$stat_file" ./Library_Static_Data/Results_"$name"/
        echo "Moved $stat_file to ./Library_Static_Data/Results_$name/"
    fi

done