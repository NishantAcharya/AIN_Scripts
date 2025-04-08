
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

    #Generate the (cidr, netrange, organizaton name) tuple, this is the most time consuming part, usually about 2 hours to run
    if [ -e "./whois_data/cidr.dat" ]; then
        echo "whois database has already existed"
    else
        echo "Now generating the local whois database, this might cost about 2 hours"
        python3 ./Local_whois/Netrange_OrgName_pair.py
    fi
    #Get provider names for this library
    python3 ./FCC_Provider/FCC_providers.py "$library"
    exit_code=$?  
    #don't get any FIPS code
    if [ $exit_code -eq 1 ]; then
        echo "No FIPS code found"
        echo
        python3.9 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        #do local whois
        python3 ./Local_whois/local_whois_no_providers.py
    #get FIPS code, but don't get provider in this census block
    elif [ $exit_code -eq 2 ]; then
        echo "No provider found"
        echo
        python3.9 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        #do local whois
        python3 ./Local_whois/local_whois_no_providers.py
    else
        echo "Get FCC providers"
        echo 
        #if the set of organization names and provider names exist, skip this step
        if [ -e "./TF-IDF/nameset.txt" ]; then
            echo "The nameset file exists"
        else
            echo "now generating the nameset for TF-IDF"
            python3 ./TF-IDF/generate_name_set.py
        fi
        echo
        #Run TF-IDF to get keywords for each name
        python3 ./TF-IDF/TF_IDF.py
        echo
        #get cidrs near the library
        python3.9 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
        #do local whois and filtering
        python3 ./Local_whois/local_whois.py
    fi

done