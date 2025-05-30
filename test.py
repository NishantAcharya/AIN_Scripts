import numpy as np
import pandas as pd
import json
import ipaddress
from tqdm import tqdm
import time
from bs4 import BeautifulSoup
import requests
import gzip
import shutil
import sys

#Helper
def apply_netmask(ip, mask):
    return str(ipaddress.ip_network(f"{ip}/{mask}", strict=False))

print(apply_netmask('96.91.29.208',26))