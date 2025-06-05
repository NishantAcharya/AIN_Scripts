import os
import json

input_file = 'validation_input.txt'
directory = './Library_Static_Data/'

with open(input_file, 'r') as file:
    lines = file.readlines()
    folders = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines if line.strip()]

print