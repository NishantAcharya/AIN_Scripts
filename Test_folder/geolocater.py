from geopy.geocoders import Nominatim
from geopy.distance import geodesic

def get_metropolitan_area(address, metro_areas):
    """
    Finds the nearest metropolitan area to a given address.

    Args:
        address (str): The address to geocode.
        metro_areas (dict): A dictionary of metropolitan areas with their coordinates.
                              e.g., {"New York": (40.7128, -74.0060), "Los Angeles": (34.0522, -118.2437)}

    Returns:
        str: The name of the nearest metropolitan area, or None if an error occurs.
    """
    geolocator = Nominatim(user_agent="geo_app")
    try:
        location = geolocator.geocode(address)
        if location:
            address_coords = (location.latitude, location.longitude)
            nearest_metro = min(metro_areas, key=lambda city: geodesic(address_coords, metro_areas[city]).km)
            return nearest_metro
        else:
            return None
    except Exception as e:
         print(f"Error: {e}")
         return None

# Example usage:
metro_areas = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698)
}
address_to_check = "1600 Amphitheatre Parkway, Mountain View, CA"
nearest_metro_area = get_metropolitan_area(address_to_check, metro_areas)

if nearest_metro_area:
    print(f"The nearest metropolitan area to '{address_topolled_address}' is: {nearest_metro_area}")
else:
    print("Could not find the nearest metropolitan area.")