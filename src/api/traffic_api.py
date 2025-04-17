# src/api/traffic_api.py
import requests
import time
import os
from datetime import datetime

class TomTomTrafficAPI:
    """Interface for fetching live traffic data from TomTom"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("j3vxL9Ym1y775Q3qbGSDw6uxwD1K5VeZ")
        self.base_url = "https://api.tomtom.com/traffic/services/4/"
        
    def get_traffic_flow(self, bbox):
        """
        Get traffic flow data for an area defined by bounding box
        
        Args:
            bbox: Tuple of (min_lat, min_lon, max_lat, max_lon)
        
        Returns:
            Dictionary mapping road_ids to traffic multipliers
        """
        if not self.api_key:
            print("Warning: No TomTom API key provided, using simulated data")
            return self._simulate_traffic_data()
            
        min_lat, min_lon, max_lat, max_lon = bbox
        bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        try:
            url = f"{self.base_url}flowSegmentData/absolute/10/json"
            response = requests.get(
                url,
                params={
                    "bbox": bbox_str,
                    "key": self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_tomtom_response(response.json())
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return self._simulate_traffic_data()
                
        except Exception as e:
            print(f"Error fetching traffic data: {e}")
            return self._simulate_traffic_data()
    
    def _parse_tomtom_response(self, data):
        """Parse TomTom API response into traffic multipliers by road segment"""
        traffic_data = {}
        
        try:
            # Process TomTom flow segments
            if 'flowSegmentData' in data:
                for segment in data.get('flowSegmentData', {}).get('freeFlowSegmentData', []):
                    # Extract road identifier (using coordinates as unique ID)
                    if 'coordinates' in segment and len(segment['coordinates']['coordinate']) > 0:
                        coords = segment['coordinates']['coordinate']
                        road_id = f"{coords[0]['latitude']}_{coords[0]['longitude']}"
                        
                        # Calculate traffic multiplier
                        current_speed = segment.get('currentSpeed', 0)
                        free_flow_speed = segment.get('freeFlowSpeed', 0)
                        
                        if free_flow_speed > 0 and current_speed > 0:
                            # Lower speeds mean higher travel times
                            multiplier = free_flow_speed / current_speed
                        else:
                            multiplier = 1.0  # Default if speeds not available
                            
                        traffic_data[road_id] = min(multiplier, 5.0)  # Cap at 5x
        except Exception as e:
            print(f"Error parsing TomTom response: {e}")
            
        return traffic_data
    
    def _simulate_traffic_data(self):
        """Generate simulated traffic data for testing"""
        import random
        
        traffic_data = {}
        
        # Time-based patterns
        hour = datetime.now().hour
        
        # Simulate rush hour patterns
        base_congestion = 1.0
        if 7 <= hour <= 9:  # Morning rush
            base_congestion = 2.0
        elif 16 <= hour <= 18:  # Evening rush
            base_congestion = 2.2
        elif 11 <= hour <= 13:  # Lunch time
            base_congestion = 1.5
        elif 22 <= hour <= 5:  # Late night
            base_congestion = 0.8
            
        # Add randomness - roads array would be populated from the map
        for i in range(1000):  # Simulate for a large number of roads
            road_id = f"r{i}"
            # Random variation around base level
            multiplier = base_congestion * random.uniform(0.7, 1.4)
            traffic_data[road_id] = max(0.8, min(multiplier, 5.0))
            
        return traffic_data