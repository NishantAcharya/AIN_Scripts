
#!/bin/bash

libraries=()
lans=()
lons=()
names=()
states=()

# Read from the Library_data.txt file and separate lines on '-'
while IFS='-' read -r part1 part2 part3 part4 part5; do
    part1=${part1//\//-}
    part2=${part2//\//-}
    part3=${part3//\//-}
    part4=${part4//\//-}
    part5=${part5//\//-}
    lans+=("$part1")
    lons+=("$part2")
    names+=("$part3")
    state+=("$part4")
    libraries+=("$part5")
done < ./Library_data.txt

for i in "${!libraries[@]}"; do
    library="${libraries[$i]}"
    lan="${lans[$i]}"
    lon="${lons[$i]}"
    name="${names[$i]// /_}"

    echo "Processing library: $library"
    echo "LAN: $lan"
    echo "Longitude: $lon"
    echo "Name: $name"

done