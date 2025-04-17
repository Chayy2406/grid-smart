# src/utils/geocoding.py
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

class GeocodingService:
    """Convert between addresses and coordinates"""
    
    def __init__(self, user_agent="traffic_routing_app"):
        self.geolocator = Nominatim(user_agent=user_agent)
        self.cache = {}  # Simple cache to avoid repeated queries
    
    def address_to_coordinates(self, address, city="Tempe, AZ"):
        """
        Convert an address to coordinates
        
        Args:
            address: Street address or place name
            city: City to search within (default: Tempe, AZ)
        
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Add city context if not specified
        if city.lower() not in address.lower():
            full_address = f"{address}, {city}"
        else:
            full_address = address
            
        # Check cache
        if full_address in self.cache:
            return self.cache[full_address]
            
        try:
            # Geocode the address
            location = self.geolocator.geocode(full_address, timeout=10)
            
            if location:
                result = (location.latitude, location.longitude)
                self.cache[full_address] = result
                return result
            else:
                print(f"Could not find coordinates for '{full_address}'")
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error: {e}")
            # Retry once with backoff
            time.sleep(2)
            try:
                location = self.geolocator.geocode(full_address, timeout=10)
                if location:
                    result = (location.latitude, location.longitude)
                    self.cache[full_address] = result
                    return result
            except:
                pass
                
            return None
    
    def find_nearest_intersection(self, lat, lon, map_data):
        """
        Find the nearest intersection to the given coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            map_data: MapData object
        
        Returns:
            Intersection ID of the nearest intersection
        """
        nearest_id = None
        min_distance = float('inf')
        
        for node_id, intersection in map_data.intersections.items():
            distance = ((intersection.lat - lat) ** 2 + 
                        (intersection.lon - lon) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_id = node_id
                
        return nearest_id