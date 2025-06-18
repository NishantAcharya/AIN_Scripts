import os
import numpy as np

with open('Data_set/output .csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines = [line.strip() for line in lines if line.strip()]

line_lengths = [len(line.split(',')) for line in lines]
max_length = max(line_lengths)

new_lines = []
for line in lines:
    parts = line.split(',')
    if len(parts) < max_length:
        parts.extend([''] * (max_length - len(parts)))
    new_lines.append(','.join(parts))

with open('Data_set/fixed_output.csv', 'w', encoding='utf-8') as f:
    for line in new_lines:
        f.write(line + '\n')