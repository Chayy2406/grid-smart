import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth given their latitude and longitude in degrees.
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    
    return c * r

def get_center_point(locations):
    """
    Find the geographical center of multiple points
    
    Args:
        locations: List of (lat, lon) tuples
    
    Returns:
        (center_lat, center_lon) tuple
    """
    if not locations:
        return None
        
    lat_sum = sum(lat for lat, _ in locations)
    lon_sum = sum(lon for _, lon in locations)
    count = len(locations)
    
    return (lat_sum / count, lon_sum / count)