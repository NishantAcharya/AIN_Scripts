import math

def find_circle_intersection(circle1, circle2):
    x1, y1, r1 = circle1
    x2, y2, r2 = circle2

    # Distance between the centers
    d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    # Check if there are no intersections
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return []

    # Find the point of intersection
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(r1**2 - a**2)

    # Point P2 where the line through the circle intersection points crosses the line between the circle centers
    x3 = x1 + a * (x2 - x1) / d
    y3 = y1 + a * (y2 - y1) / d

    # Intersection points
    intersection1 = (x3 + h * (y2 - y1) / d, y3 - h * (x2 - x1) / d)
    intersection2 = (x3 - h * (y2 - y1) / d, y3 + h * (x2 - x1) / d)

    # If the circles touch at one point, return a single intersection
    if d == r1 + r2 or d == abs(r1 - r2):
        return [intersection1]

    return [intersection1, intersection2]

def find_all_intersections(circles):
    intersections = []
    n = len(circles)

    # Compare each pair of circles
    for i in range(n):
        for j in range(i + 1, n):
            circle1 = circles[i]
            circle2 = circles[j]
            intersections.extend(find_circle_intersection(circle1, circle2))

    return intersections

circle1 = (0,0,2)
circle2 = (3,0,2)
circle3 = (1.5,2,2)
circles = [circle1, circle2, circle3]

print(find_all_intersections(circles))
