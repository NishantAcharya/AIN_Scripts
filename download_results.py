#Receive's pings

from ripe.atlas.cousteau import (
  Ping,
  Traceroute,
    AtlasSource,
    AtlasResultsRequest,
    AtlasCreateRequest,
    Measurement
)
import pandas as pd
import numpy as np
import ast
from tqdm import tqdm
from random import sample
from datetime import datetime,timedelta,timezone
from ipaddress import ip_address,ip_network,ip_interface
import time
import json
import threading
import math
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import random
import json
import csv
import os
from datetime import date
import socket
import geoip2.database
import requests
import sys
import ast

def read_msms(close:False):
    msms = []
    libs = []
    if not close:
        with open('msms.txt','r') as f:
            for line in f:
                new_line = line.strip().split('-')
                msm = ast.literal_eval(new_line[0])
                lib = new_line[1].split('_')[-1].split('json')[0][:-1]
                msms.append(msm)
                libs.append(lib)
        return msms,libs
    if close:
        with open('close_msms.txt','r') as f:
            for line in f:
                new_line = line.strip().split('-')
                msm = ast.literal_eval(new_line[0])
                lib = new_line[1].split('_')[-1].split('json')[0][:-1]
                msms.append(msm)
                libs.append(lib)
        return msms,libs


def check_status(msm):
    status = Measurement(id=msm).status
    return status

def retreive_msm(msm):
    kwargs = {
        "msm_id": msm
    }

    is_success, results = AtlasResultsRequest(**kwargs).create()
    return results

#Grab all the results, get the min RTT of them all
#Then get the min RTT to reach the close by probe from another closeby probe
#Then check if the RTT to a probe, then to a different close probe is close to the RTT gotten from the equation
#Then create a graph for it
def main():
    msms_groups,libs = read_msms(False)
    for i in tqdm(range(len(msms_groups))):
        msms = msms_groups[i]
        lib = libs[i]
        #extracting the values
        data_dict = {
                'dest_addr': [],
                'src_addr': [],
                'src_prb_id': [],
                'all_rtt': [],
                'min_rtt': [],
                'max_rtt': [],
                'protocol': [],
                'timestamp': [],
                'step': [],
                'msm_id': []
            }
        for msm in msms:
            result = retreive_msm(msm)
            for ping in result:
                data_dict['msm_id'].append(msm)
                data_dict['dest_addr'].append(ping['dst_addr'])
                data_dict['src_addr'].append(ping['src_addr'])
                data_dict['protocol'].append(ping['proto'])
                data_dict['src_prb_id'].append(ping['prb_id'])
                rtts = ping['result']
                output_rtts = ''
                for rtt in rtts:
                    try:
                        temp = rtt['rtt']
                    except KeyError:
                        temp = -1

                    output_rtts += str(temp) + ','
                output_rtts = output_rtts[:-1]

                data_dict['all_rtt'].append(output_rtts)
                data_dict['min_rtt'].append(ping['min'])
                data_dict['max_rtt'].append(ping['max'])
                data_dict['timestamp'].append(ping['stored_timestamp'])
                data_dict['step'].append(ping['step'])

        #Saving
            file_name = f'{lib}-far.csv'


            df = pd.DataFrame(data_dict)
            df.to_csv(f'CSV/{file_name}',index = False)
    
    #Close pings
    msms_groups,libs = read_msms(True)
    for i in tqdm(range(len(msms_groups))):
        msms = msms_groups[i]
        lib = libs[i]
        #extracting the values
        data_dict = {
                'dest_addr': [],
                'src_addr': [],
                'src_prb_id': [],
                'all_rtt': [],
                'min_rtt': [],
                'max_rtt': [],
                'protocol': [],
                'timestamp': [],
                'step': [],
                'msm_id': []
            }
        for msm in msms:
            result = retreive_msm(msm)
            for ping in result:
                data_dict['msm_id'].append(msm)
                data_dict['dest_addr'].append(ping['dst_addr'])
                data_dict['src_addr'].append(ping['src_addr'])
                data_dict['protocol'].append(ping['proto'])
                data_dict['src_prb_id'].append(ping['prb_id'])
                rtts = ping['result']
                output_rtts = ''
                for rtt in rtts:
                    try:
                        temp = rtt['rtt']
                    except KeyError:
                        temp = -1

                    output_rtts += str(temp) + ','
                output_rtts = output_rtts[:-1]

                data_dict['all_rtt'].append(output_rtts)
                data_dict['min_rtt'].append(ping['min'])
                data_dict['max_rtt'].append(ping['max'])
                data_dict['timestamp'].append(ping['stored_timestamp'])
                data_dict['step'].append(ping['step'])

        #Saving
            file_name = f'{lib}-close.csv'


            df = pd.DataFrame(data_dict)
            df.to_csv(f'CSV/{file_name}',index = False)

            

main()
    
        