from geopy.distance import geodesic
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj
import numpy as np
from itertools import combinations
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
import multiprocessing
import os
import sys
import json
import ipaddress
import ast
from tqdm import tqdm
class Circle:
    def __init__(self, center: Tuple[float, float], radius: float):
        self.center = center
        self.radius = radius

def create_geodesic_circle(lat, lon, radius, n=360):
    geod = pyproj.Geod(ellps='WGS84')
    points = [geod.fwd(lon, lat, angle, radius)[:2] for angle in np.linspace(0, 360, n, False)]
    return Polygon(points)

def poly_intersection(polys):
    if not polys: return None
    intersection = polys[0]
    for p in polys[1:]: intersection = intersection.intersection(p)
    return intersection if not intersection.is_empty else None

def project_poly(poly):
    if poly.is_empty: return None, None, None
    lon, lat = poly.centroid.x, poly.centroid.y
    utm_crs = pyproj.CRS.from_epsg(32600 + int((lon + 180) / 6) + (100 * (lat >= 0)))
    project = pyproj.Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True).transform
    inv_project = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True).transform
    projected_poly = transform(project, poly)
    centroid_proj = inv_project(*projected_poly.centroid.xy)
    return projected_poly, centroid_proj, utm_crs

def get_area(poly):
    return project_poly(poly)[0].area if poly and not poly.is_empty else None

def find_max_intersect(circles):
    n = len(circles)
    geos = [create_geodesic_circle(*c.center, c.radius) for c in circles]
    max_intersect_poly, max_count, max_indices = None, 0, tuple()
    for i in range(1, n + 1):
        for indices in combinations(range(n), i):
            intersect = poly_intersection([geos[j] for j in indices])
            if intersect and i > max_count:
                max_count, max_intersect_poly, max_indices = i, intersect, tuple(sorted(indices))
    return max_intersect_poly, max_count, max_indices, geos

def check_overlap_with_new_circle(max_poly: Polygon, new_circle: Circle) -> Optional[Polygon]:
    if not max_poly:
        return None
    new_circle_geo = create_geodesic_circle(*new_circle.center, new_circle.radius)
    overlap = poly_intersection([max_poly, new_circle_geo])
    return overlap

def plot_results(circles, max_poly, max_indices, overlap_with_new=None, new_circle=None, utm_crs=None):
    fig, ax = plt.subplots(figsize=(10, 10))
    if utm_crs:
        project = pyproj.Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True).transform
    else:
        project = lambda x: x  # Identity if no projection

    for i, c in enumerate(circles):
        poly = create_geodesic_circle(*c.center, c.radius)
        px, py = transform(project, poly).exterior.xy
        ax.plot(px, py, label=f'Circle {i}')

    if max_poly:
        px_max, py_max = transform(project, max_poly).exterior.xy
        ax.fill(px_max, py_max, color='red', alpha=0.5, label=f'Max Intersection ({len(max_indices)} circles)')

    if overlap_with_new and new_circle:
        new_circle_geo = create_geodesic_circle(*new_circle.center, new_circle.radius)
        px_new, py_new = transform(project, new_circle_geo).exterior.xy
        ax.plot(px_new, py_new, '--g', label=f'New Circle (Overlap Check)')
        px_overlap, py_overlap = transform(project, overlap_with_new).exterior.xy
        ax.fill(px_overlap, py_overlap, color='blue', alpha=0.5, label='Overlap with New Circle')

    ax.set_xlabel(f"Easting ({utm_crs.name})" if utm_crs else "Longitude")
    ax.set_ylabel(f"Northing ({utm_crs.name})" if utm_crs else "Latitude")
    ax.set_title("Circle Intersections and Overlap with New Circle")
    ax.legend()
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True)
    plt.show()

# Function to convert IP to /mask
def apply_netmask(ip, mask):
    return str(ipaddress.ip_network(f"{ip}/{mask}", strict=False))

def is_ip_in_cidr(ip, cidr):
  try:
    ip_obj = ipaddress.ip_address(ip)
    network = ipaddress.ip_network(cidr, strict=False)
    return ip_obj in network
  except ValueError:
    return False


#Folder for the multi_process
def process_cbg_data(trace_folder_name,graph_folder_name,outfile_name):
    process_name = multiprocessing.current_process().name
    mask = 26
    print(f"Process {process_name} is processing data for folder: {trace_folder_name}")
    #CIDR file path
    cidr_file_path = f"./Library_Static_Data/{trace_folder_name}/filtered_dup_removed.txt"
    #Output file path
    output_file_path = f"./Library_Static_Data/{trace_folder_name}/{outfile_name}"
    #Graph file path
    graph_file_path = f"./Library_Static_Data/{trace_folder_name}/{graph_folder_name}/"
    #Trace data file path
    trace_data_file_path = f"./Library_Static_Data/{trace_folder_name}/Trace_data.json"
    #Meta info path
    meta_info_file_path = f"./Library_Static_Data/{trace_folder_name}/Meta_info.txt"
    #Meta info#####
    didnt_reach_target = 0
    single_probe_no_overlap = 0
    single_probe_overlap = 0
    multiple_probe_no_overlap = 0
    multiple_probe_overlap = 0
    total = 0
    ambigious_count = 0
    target_ip_cidrs = 0
    #Meta Info end#####

    #Checking if the trace data file exists
    if not os.path.exists(trace_data_file_path):
        print(f"Trace data file '{trace_data_file_path}' does not exist. Skipping folder: {trace_folder_name}")
        return
    
    #Duplicate the trace data file
    trace_data_copy_path = f"./Library_Static_Data/{trace_folder_name}/Trace_data_copy.json"
    with open(trace_data_file_path, 'r') as f:
        data = json.load(f)
    with open(trace_data_copy_path, 'w') as f:
        json.dump(data, f)

    #Processing the trace data
    confirmed_ips = []
    for ip in tqdm(data.keys()):
        smallest_rtt_probes = data[ip]['Smallest_RTT_Probes']
        total += 1
        ambigious = False
        if len(smallest_rtt_probes) == 0:
            didnt_reach_target += 1
            continue
        elif len(smallest_rtt_probes) == 1:
            target_circle_data = ((data[ip]['Lat'],data[ip]['Lon']), 40000) #Radius in meters -- 40Km
            probe = str(smallest_rtt_probes[0])
            rtt = data[ip][probe]['Usable_Last_Hop_RTT']

            lat_long = (float(data[ip][probe]['Lat,Long'][0]), float(data[ip][probe]['Lat,Long'][1]))
            distance = data[ip][probe]['Distance Destination']*1000 #Convert to meters

            #IF distance is > 40 km use the RTT formula else use the SoL constraints
            if distance <= 40000:
                sol_radius = (rtt/0.01)*1000
                if distance > sol_radius:
                    ambigious = True
                    radius = -1
                else:
                    radius = sol_radius
            #IF distance > 40 KM but RTT is between 14.75 and 2.75 -- use the above formula
            else:
                sol_radius = (rtt/0.01)*1000
                if distance > sol_radius:
                    ambigious = True
                    radius = -1
                else:
                    if rtt <= 14.75:
                            radius = sol_radius
                    else:
                        max_radius = ((rtt - 14.75 + 12)/0.015)*1000
                        radius = max_radius

            
            input_circle_data = (lat_long, radius)
            # Create the target circle and input circle
            if ambigious:
                ambigious_count += 1
                continue
            target_circle = Circle(center=target_circle_data[0], radius=target_circle_data[1])
            input_circle = Circle(center=input_circle_data[0], radius=input_circle_data[1])

            # Find the overlap between the target circle and input circle
            overlap = check_overlap_with_new_circle(create_geodesic_circle(*target_circle.center, target_circle.radius), input_circle)
            # If there is an overlap, process it further
            if overlap and not overlap.is_empty:
                overlap_area = get_area(overlap)
                single_probe_overlap += 1
                confirmed_ips.append(ip)
            else:
                single_probe_no_overlap += 1
                continue
        else:
            target_circle_data = ((data[ip]['Lat'],data[ip]['Lon']), 40000) #Radius in meters -- 40Km
            probes = smallest_rtt_probes
            circles = []
            #Collecting circle data
            for probe in probes:
                probe_key = str(probe)
                rtt = data[ip][probe_key]['Usable_Last_Hop_RTT']
                lat_long = (float(data[ip][probe_key]['Lat,Long'][0]), float(data[ip][probe_key]['Lat,Long'][1]))
                distance = data[ip][probe_key]['Distance Destination']*1000 #Convert to meters
                #IF distance is > 40 km use the RTT formula else use the SoL constraints
                if distance <= 40000:
                    sol_radius = (rtt/0.01)*1000 # 1ms/KM roughly
                    if distance > sol_radius:
                        ambigious = True
                        radius = -1
                    else:
                        radius = sol_radius
                #IF distance > 40 KM byut RTT is between 14.75 and 2.75 -- use the above formula
                else:
                    sol_radius = (rtt/0.01)*1000 # 1ms/KM roughly
                    if distance > sol_radius:
                            ambigious = True
                            radius = -1
                    else:
                        if rtt <= 14.75:
                            radius = sol_radius
                        else:
                            max_radius = ((rtt - 14.75 + 12)/0.015)*1000
                            radius = max_radius
                    
                circle = Circle(center=lat_long, radius=radius)
                circles.append(circle)
            
            #Found a single probe for the IP that violated SoL constraints -- discarding this IP
            if ambigious:
                ambigious_count += 1
                continue
            #Processing interesection and overlap
            target_circle = Circle(center=target_circle_data[0], radius=target_circle_data[1])
            max_poly, max_count, max_indices, geos = find_max_intersect(circles)
            if max_poly:
                projected_poly, centroid_proj, utm_crs = project_poly(max_poly)
                area = get_area(max_poly)
                if(ip == "64.40.217.1"):
                    print("Debugging")
                    print(area)
                    print(target_circle.center, target_circle.radius)
                    print([(c.center, c.radius) for  c in circles])
                    print(probes)
                    plot_results(circles, max_poly, max_indices, overlap_with_new, target_circle, utm_crs)  
                
                overlap_with_new = check_overlap_with_new_circle(max_poly, target_circle)

                if overlap_with_new:
                    overlap_area = get_area(overlap_with_new)
                    multiple_probe_overlap += 1
                    confirmed_ips.append(ip)
                else:
                    multiple_probe_no_overlap += 1

    


                

    #Read the CIDR file
    with open(cidr_file_path, 'r') as f:
        lines = f.readlines()
        cidrs = [line.strip().split('-')[-1].strip()for line in lines if line.strip()]

    #Checking if confirmed IPs are in the CIDRs
    for ip in confirmed_ips:
        for cidr in cidrs:
            if is_ip_in_cidr(ip, cidr):
                target_ip_cidrs += 1
                break

    #Writing the data to the output file
    with open(output_file_path, 'w') as f:
        ips = [apply_netmask(ip,mask).strip()+'\n' for ip in confirmed_ips]
        f.writelines(ips)

    #Writing the meta info
    with open(meta_info_file_path, 'w') as f:
        f.write(f"Process: {process_name}\n")
        f.write(f"Total IPs: {total}\n")
        f.write(f"Did not reach target: {didnt_reach_target}\n")
        f.write(f"Single probe no overlap: {single_probe_no_overlap}\n")
        f.write(f"Single probe overlap: {single_probe_overlap}\n")
        f.write(f"Multiple probe no overlap: {multiple_probe_no_overlap}\n")
        f.write(f"Multiple probe overlap: {multiple_probe_overlap}\n")
        f.write(f"Ambigious count: {ambigious_count}\n")
        f.write(f"Target IP CIDRs: {target_ip_cidrs}\n")
        f.write("\n")

    
    
    
    
    

if __name__ == '__main__':
    #Load the name of the Folder to look at
    #create n processes -- start with stamford and littlefield -- to process the tracedata
    ## Each process will open the respective folder and load all the CIDRs currently being processed
    ## Each process will duplicate the trace_data json file
    ## Each process will load the duplicated json trace data
    ## Each process will go through the IPs
    ### If the smallest RTT probes is 0, skip
    ### If the smallest RTT probes is 1 -- find the intersection of that probe's circle and the target circle
    ### If > 1 smallest RTT -- find the the max intersection, then that intersection's overlap with the target circle
    ### Make sure that all 3 circles intersect (or all n circles intersect) -- if not remove
    ## Each process will save this result by saving it to the duplicate trace data json file and write it to a file
    print("Starting the process...")
    input_file_name = 'validation_test.txt' #Library File
    graph_folder_name = 'Graphs' #Graph Folder in results folder
    outfile_name = 'final_filtered.txt'
    with open(input_file_name, 'r') as f:
        lines = f.readlines()
        lines = ['Results_'+line.strip().split('~')[2].replace(' ','_') for line in lines if line.strip()]
    
    if len(lines) <= 14:
        processes_num = len(lines)
    else:
        processes_num = 14

    # Create a pool of processes
    with multiprocessing.Pool(processes=processes_num) as pool:
        # Map the function to the lines
        pool.starmap(process_cbg_data, [(line.strip(), graph_folder_name,outfile_name) for line in lines])

    #By here all the data has been processed and the lines have been written to the file