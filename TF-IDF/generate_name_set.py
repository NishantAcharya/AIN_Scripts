import re
import pandas as pd
from unidecode import unidecode
from pathlib import Path


#input files
file_name1 = "./Data_set/bulk_whois/Organizations.txt"
file_name2 = "./Data_set/FCC_providers/BDC.xlsx"
#contains all organization names from Whois and FCC provider names
output_name = "./nameset.txt"


org_name_set = []

error_set = []


def clean_string(text):
    return " ".join(word.replace(".", "") for word in text.split())  


#extract all lines start with "OrgName"
def extract_blocks(file_path):
    global org_name_set
    with open(file_path, 'r', encoding = "UTF-8") as file:
        for line_num, line in enumerate(file, start=1):
            if line.startswith("OrgName:"):
                text = unidecode(line)
                orgname = text.split("OrgName:")[-1].strip()
                orgname = clean_string(orgname)
                org_name_set.append(orgname)
            



extract_blocks(file_name1)
outpout_set = list(set(org_name_set))
print(f"extract {str(len(outpout_set))} Organization names")


#read the xlsx file
xlsx_file = pd.read_excel(file_name2)
hholding_company = xlsx_file["Holding Company"].tolist()
holding_company = [clean_string(text) for text in hholding_company]
pprovider_Name = xlsx_file["Provider Name"].tolist()
Provider_Name = [clean_string(text) for text in pprovider_Name]
providers = list(set(holding_company + Provider_Name))
print(f"extact {str(len(providers))} providers names")

#delelte duplicate names
final_set = list(set(outpout_set + providers))
print(f"get {str(len(final_set))} names in total")


with open(output_name, "a+", encoding='us-ascii') as output:
    for org in final_set:
        org = org.replace("\xa0", " ")
        output.write(org + "\n")
    