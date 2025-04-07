libraries=("443 N Rexford Dr, Beverly Hills, CA, 90210" 
"820 E Washington Ave, Burlington, WA, 98233" 
"1307 Commerce Dr Suite 140, Saratoga Springs, UT, 84045"
"602 E Cass St, Albion, MI, 49224" 
"222 21st Ave S, Minneapolis, MN,  55455" 
"335588 E. 750 Road, Perkins, OK, 74059"
"164 King St, Charleston, SC, 29401"
"8005 Connecticut Ave, Chevy Chase, MD, 20815"
"1100 Lawrence St, Denver, CO, 80204" 
"925 West Edenborne Parkway, Gonzales, LA, 70737" 
"128 South 3rd Street, Decatur, IN, 46733")

lans=("34.07327962493017" 
"48.474422" 
"40.39101791381836" 
"42.2450259" 
"44.9731694"
"36.909472"
"32.7784456"
"38.9911446"
"39.745185" 
"30.189389" 
"40.829202")

lons=("-118.39929344207874" 
"-122.323685" 
"-111.91393280029297" 
"-84.7458006" 
"-93.243012"
"-95.963552"
"-79.93269"
"-77.0765288"
"-105.000679"
"-90.920184"
"-84.925192")




for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"

    echo "Library: $library"
    echo "Latitude: $lan"
    echo "Longitude: $lon"
    echo
    echo

    #Check if outputs folder exists
    if [ -d "./outputs" ]; then
        echo "The outputs folder exists"
    else
        mkdir outputs
    fi

    # Get CIDR
    python3 ./reverse_geolocation/get_cidrs.py "$lan" "$lon"
    echo
    echo

    # Get provider names for this library
    python3 ./FCC_Provider/FCC_providers.py "$library"
    echo
    echo

    # If the set of organization names and provider names exist, skip this step
    if [ -e "./TF-IDF/nameset.txt" ]; then
        echo "The nameset file exists"
    else
        python3 ./TF-IDF/generate_name_set.py
    fi
    echo
    echo

    # Run TF-IDF to get keywords for each name
    python3 ./TF-IDF/TF_IDF.py
    echo
    echo

    # Generate the (cidr, netrange, organization name) tuple
    if [ -e "./Local_whois/cidr.dat" ]; then
        echo "local whois could run now."
    else
        python3 ./Local_whois/Netrange_OrgName_pair.py
    fi
    echo
    echo

    # Do local whois
    python3 ./Local_whois/local_whois.py

    # Rename and move the output folder to Done_Results
    # Check if the folder exists
    if [ -d "./Done_Results" ]; then
        echo "The Done_Results folder exists"
    else
        mkdir Done_Results
    fi

    # Check if the Results folder exists in Done_Results
    if [ -d "./Done_Results/Results_$library" ]; then
        echo "The Results folder exists in Done_Results"
    else
        mkdir ./Done_Results/Results_"$library"
    fi

    # Move the output folder to Done_Results
    mv ./outputs ./Done_Results/Results_"$library"
done
