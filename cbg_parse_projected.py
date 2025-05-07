from geopy.distance import geodesic, great_circle #To get the best approximation
from shapely.geometry import Point, Polygon #Polygon operations
import json
import os
import sys
from shapely.ops import transform
import pyproj
import numpy as np
import math
from itertools import combinations
import matplotlib.pyplot as plt

#HELPERS
#All distance is in KM
#All arrays convert them to np arrays for simplicity
#Check if a point is within a circle -- to check for intersection with a polygon
def is_in(d_lat,d_lon,c_lat,c_lon,rad):
    return geodesic((d_lat, d_lon), (c_lat, c_lon)).km <= rad

#Edge case --  when circles intersect at 1 point, return the point as appoximating that is hard
def single_point_case(x1,y1,r1,x2,y2,r2):
    # Calculate the distance between the centers
    d = geodesic((x1, y1), (x2, y2)).km

    # Check if the circles touch at one point
    #return d == r1 + r2 or d == abs(r1 - r2)
    #Floating point precision error can happen above -- use np.isclose
    return np.isclose(d, r1 + r2, atol=1e-5) or np.isclose(d, abs(r1 - r2), atol=1e-5)

#Given a set of circles, find all the possible iterative intersections
def find_n_circle_intersection(circles, n, s_density):
    #Error check
    if n < 2:
        raise ValueError("The number of circles needs to be 2 at least")
    elif n > len(circles):
        raise ValueError("Too many intersections requested")
    
    centeroids_circles = []
    areas_intersection = []
    indicies_intersection = []

    #Use the GPS coordinate system
    projection = pyproj.CRS("EPSG:4326")

    #Need a way to project the circles to a flat plane
    #Using UTM? --> Why? Better for spatial analysis -- needed for area analysis in the end
    #UTM also changes based on the lat long -- keep it the same for US but need to change it later
    #utm_zone = 10 #Change between 10-19 across the states

    #All the circles are ~ going to be in the same zone -- edge case where they can be different
    #Circle -- (lat, lon, radius)
    lon_appox = np.mean([circle[1] for circle in circles])

    #Use the approx lat for projection -- can lead to shape issues on edge cases
    #EPSG codes start from 3600 for north and 3700 for south
    #+ 180 to deal with -ve values
    utm_zone = int((math.floor(lon_appox) + 180)/6) + 1

    try:
        utm_proj = pyproj.CRS(f"EPSG:326{utm_zone}")
        projected_lat_lon = pyproj.Transformer.from_crs(projection, utm_proj, always_xy=True).transform
    except pyproj.exceptions.CRSError as e:
        #Some error in the CRS code -- since we will be using the closest 3 RTT circles
        print(f"Invalid CRS Code: {e}")
        return [], [], []
    
    #Get per n intersections -- we only care about till 3
    for indices in combinations(range(len(circles)), n):
        selected_circles = [circles[i] for i in indices]

        #Handling edge case -- any more than 3 circles intersecting is very hard to manage
        if n == 2 and single_point_case(selected_circles[0][0], selected_circles[0][1], selected_circles[0][2], selected_circles[1][0], selected_circles[1][1], selected_circles[1][2]):
            centroid_1 = (selected_circles[0][0], selected_circles[0][1])
            centroid_2 = (selected_circles[1][0], selected_circles[1][1])
            #Getting the mid point between the two circles -- appox intersection
            mid_point = ((centroid_1[0] + centroid_2[0]) / 2, (centroid_1[1] + centroid_2[1]) / 2)
            centeroids_circles.append(mid_point)
            areas_intersection.append(0.0)
            indicies_intersection.append(list(indices))
            continue

        #For other cases -- if >= 3 touch points are found -- we ignore them due to complexity
        #To approximate the circle we will sample points
        #Getting the range for sampling

        #Offset the km to degrees
        min_lat = min([circle[0] - circle[2]*0.015 for circle in selected_circles])
        max_lat = max([circle[0] + circle[2]*0.015 for circle in selected_circles])
        min_lon = min([circle[1] - circle[2]*0.015 for circle in selected_circles])
        max_lon = max([circle[1] + circle[2]*0.015 for circle in selected_circles])

        #Sample points
        sampled_lat_circle = np.linspace(min_lat, max_lat, s_density)
        sampled_lon_circle = np.linspace(min_lon, max_lon, s_density)

        intersections = []
        for lat in sampled_lat_circle:
            for lon in sampled_lon_circle:
                #Check if the point is inside all the circles
                if all(is_in(lat, lon, circle[0], circle[1], circle[2]) for circle in selected_circles):
                    intersections.append((lon, lat))

        if len(intersections) < 3:
            # Not enough points to form a polygon -- skip
            centeroids_circles.append(None)
            areas_intersection.append(0.0)
            indicies_intersection.append(list(indices))
            continue
        try:
            circle_polygon = Polygon(intersections).convex_hull
            projected_polygon = transform(projected_lat_lon, circle_polygon)
            area_approximated = projected_polygon.area / 1000000.0  # Convert to KM^2
        except Exception as e:
            print(f"Error creating polygon: {e}")
            centeroids_circles.append(None)
            areas_intersection.append(0.0)
            indicies_intersection.append(list(indices))
            continue

        #Getting the centroid of the intersection
        lon_coordinates = [point[0] for point in intersections]
        lat_coordinates = [point[1] for point in intersections]
        centroid_lat = np.mean(lat_coordinates)
        centroid_lon = np.mean(lon_coordinates)
        centroid = (centroid_lon, centroid_lat)

        centeroids_circles.append(centroid)
        areas_intersection.append(area_approximated)
        indicies_intersection.append(list(indices))

    return centeroids_circles, areas_intersection, indicies_intersection

#The area of the porjected-distored circle calculation
def calculate_area(circle, sample_points=100):
    lat, lon, radius = circle

    projection_circle = pyproj.CRS("EPSG:4326")
    utm_zone = int(math.floor(lon + 180) / 6) + 1

    try:
        utm_proj = pyproj.CRS(f"EPSG:326{utm_zone}")
        projected_lat_lon = pyproj.Transformer.from_crs(projection_circle, utm_proj, always_xy=True).transform
    except pyproj.exceptions.CRSError as e:
        #Some error in the CRS code -- since we will be using the closest 3 RTT circles
        print(f"Invalid CRS Code: {e}")
        return 0.0
    
    angles = np.linspace(0,360, sample_points, endpoint=False)
    boundary_points = []
    for angle in angles:
        gc = great_circle(kilometers=radius)
        point = gc.destination((lat, lon), angle)
        boundary_points.append((point.longitude, point.latitude))

    if boundary_points:
        polygon = Polygon(boundary_points)
        projected_polygon = transform(projected_lat_lon, polygon)
        area = projected_polygon.area / 1000000.0
        centroid = (lon, lat)
        return centroid, area
    else:
        return None, 0.0
    

if __name__ == "__main__":
    #Grab this from the the trace_data -- tracedata will have information for the top 3 (max) lowest RTT circles
    circles_data = [
        (37.655395,-122.348219,543.96648),
        (42.236594,-112.758164,543.97000),
        (34.318702,-114.191737,543.97000),
        (34.208614, -108.168081,543.97000)
    ]
    #These will be the probe_ids
    circle_label = ['Circle 1', 'Circle 2', 'Circle 3', 'Circle 4']
    #If there is only 1 circle, we use that circle's info 
    num_circles = len(circles_data)
    all_intersections_data = {}

    print("\n--- Input Circles ---")
    for i in range(len(circles_data)):
        circle = circles_data[i]
        cl = circle_label[i]
        centroid, area = calculate_area(circle)
        print(f"Circle: {cl}, Centroid: (Lat: {centroid[0]:.4f}, Lon: {centroid[1]:.4f}), Area: {area:.2f} sq km")

    for i in range(2, num_circles + 1):
        centers, areas, indices = find_n_circle_intersection(circles_data, i, s_density=150)
        print(f"\n--- Approximate Intersections for {i} Circles ---")
        for j, center in enumerate(centers):
            involved_labels = [circle_label[idx] for idx in indices[j]]
            if center:
                print(f"  Circles: {', '.join(involved_labels)}, Centroid: (Lon: {center[0]:.4f}, Lat: {center[1]:.4f}), Area: {areas[j]:.2f} sq km")
                if i not in all_intersections_data:
                    all_intersections_data[i] = []
                all_intersections_data[i].append({'labels': involved_labels, 'centroid': center, 'area': areas[j]})
            else:
                print(f"  Circles: {', '.join(involved_labels)}, No significant intersection found.")

    # Visualization (plotting circles and intersection centroids)
    if all_intersections_data or circles_data:
        fig, ax = plt.subplots()

        for circle_info in circles_data:
            center_lat, center_long, radius_km = circle_info
            # Approximate circle for plotting
            circle = Point(center_long, center_lat).buffer(radius_km * 0.01)
            x, y = circle.exterior.xy
            ax.plot(x, y, alpha=0.5, label=f"Circle ({center_lat:.2f}, {center_long:.2f})")
            ax.plot(center_long, center_lat, 'o', color='black', markersize=5)  # Mark circle centers

        for n_circles, intersections in all_intersections_data.items():
            for intersection in intersections:
                center = intersection['centroid']
                labels = intersection['labels']
                ax.plot(center[0], center[1], 'x', markersize=8, label=f'{n_circles} Circles ({", ".join(labels)})') # Mark intersection centroids

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Circles and Approximate Intersection Centers")
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_aspect('equal', adjustable='box')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("circles_intersections.png", dpi=300)
    else:
        print("\nNo data to visualize.")




