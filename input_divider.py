input_file = 'input_val_final.txt'
alex_file = 'input_alex.txt'
nish_file = 'input_nish.txt'
nish_2_file = 'input_nish_2.txt'
vijeth_file = 'input_vijeth.txt'
humaira_file = 'input_humaira.txt'
jiayi_file = 'input_jiayi.txt'
anyu_file = 'input_anyu.txt'

with open(input_file, 'r') as f:
    lines = f.readlines()

count = 0
for line in lines:

    if count == 109999:
        count = 0