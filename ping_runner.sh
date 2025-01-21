#!/bin/bash

# Run Python files concurrently and redirect output to separate files

for i in {1..5}
do
    python3 /home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/send_ping.py > producer_output_$i.log 2>&1 &
    python3 /home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/receive_ping.py > consumer_output_$i.log 2>&1 &
    wait # Wait for both scripts to finish before starting the next iteration
    if [ $i -lt 5 ]; then
        sleep 5400 # Sleep for 90 minutes (5400 seconds) between runs
    fi
done

wait # Wait for all background processes to finish

echo "All Python scripts finished execution."