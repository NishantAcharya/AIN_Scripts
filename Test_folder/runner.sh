#!/bin/bash

# Run Python files concurrently and redirect output to separate files

python3 /home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/Test_folder/producer.py > producer_output.log 2>&1 &
python3 /home/nishant-acharya/Desktop/AIN_Scripts/AIN_Scripts/Test_folder/consumer.py > consumer_output.log 2>&1 &

wait # Wait for all background processes to finish

echo "All Python scripts finished execution."