#!/bin/bash

lib_name=()
lat=()
lon=()
name=()
state=()

# Read from the Library_data.txt file and separate lines on '-'
while IFS='-' read -r part1 part2 part3 part4 part5; do
    part1=${part1//\//-}
    part2=${part2//\//-}
    part3=${part3//\//-}
    part4=${part4//\//-}
    part5=${part5//\//-}
    lat+=("$part1")
    lon+=("$part2")
    name+=("$part3")
    state+=("$part4")
    lib_name+=("$part5")
done < ../Library_data.txt

echo "Latitude: ${lat[@]}"
echo "Longitude: ${lon[@]}"
echo "Name: ${name[@]}"
echo "State: ${state[@]}"
echo "Library Name: ${lib_name[@]}"