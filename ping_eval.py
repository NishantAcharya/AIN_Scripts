import json
import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import plotly.express as px
import random


#Load all probes from the probe file
probes = []
data = []
with open('JSON/grouped_probes.json') as f:
    data = json.load(f)

for key in data.keys():
    group = data[key]
    for dist in group.keys():
        probes.append(data[key][dist])

#Load all the ping data
pings = []

#How many IPs out of all of these are close to the lib loc according to this! -- GOAL

    
