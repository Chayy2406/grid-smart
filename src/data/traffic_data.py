# src/data/traffic_data.py
from ..api.traffic_api import TomTomTrafficAPI
from datetime import datetime

class TrafficData:
    def __init__(self, map_data, api_key=None):
        self.map_data = map_data
        self.traffic_api = TomTomTrafficAPI(api_key)
        self.last_update = None
    
    def update_traffic(self):
        """Update traffic conditions for all roads"""
        print("Fetching real-time traffic data...")
        
        # Calculate bounding box for the entire map
        min_lat = min(i.lat for i in self.map_data.intersections.values())
        max_lat = max(i.lat for i in self.map_data.intersections.values())
        min_lon = min(i.lon for i in self.map_data.intersections.values())
        max_lon = max(i.lon for i in self.map_data.intersections.values())
        
        # Get traffic data from API
        traffic_data = self.traffic_api.get_traffic_flow(
            (min_lat, min_lon, max_lat, max_lon)
        )
        
        # Match traffic data to roads using more sophisticated method
        self._match_roads_to_traffic(traffic_data)
        
        print(f"Updated traffic data")
        self.last_update = datetime.now()
    
    def _match_roads_to_traffic(self, traffic_data):
        """More sophisticated matching of roads to traffic data"""
        try:
            from rtree import index
            
            # Create spatial index
            idx = index.Index()
            point_data = {}
            
            # Add traffic data points to index
            i = 0
            for data_id, traffic in traffic_data.items():
                if '_' in data_id:
                    try:
                        parts = data_id.split('_')
                        if len(parts) >= 2:
                            data_lat = float(parts[0])
                            data_lon = float(parts[1])
                            
                            # Add to index
                            idx.insert(i, (data_lon, data_lat, data_lon, data_lat))
                            point_data[i] = (data_id, traffic)
                            i += 1
                    except:
                        continue
            
            # Match roads to nearest traffic data points
            updated_roads = 0
            for road_id, road in self.map_data.roads.items():
                # Get road midpoint
                mid_lat = (road.start.lat + road.end.lat) / 2
                mid_lon = (road.start.lon + road.end.lon) / 2
                
                # Find nearest traffic data points
                nearest = list(idx.nearest((mid_lon, mid_lat, mid_lon, mid_lat), 1))
                
                if nearest:
                    nearest_id = nearest[0]
                    data_id, traffic = point_data[nearest_id]
                    
                    # Apply traffic multiplier to road
                    road.current_traffic = traffic
                    updated_roads += 1
                    
            print(f"Updated {updated_roads} roads using spatial index")
        
        except ImportError:
            # Fall back to simpler matching method if rtree is not available
            print("R-tree package not available, using simple matching")
            self._simple_match_roads_to_traffic(traffic_data)
    
    def _simple_match_roads_to_traffic(self, traffic_data):
        """Simpler matching method without external dependencies"""
        # For each road, find the closest traffic data point
        updated_roads = 0
        for road_id, road in self.map_data.roads.items():
            best_match = self._find_matching_traffic(road, traffic_data)
            if best_match:
                road.current_traffic = best_match
                updated_roads += 1
            else:
                # Default multiplier if no match
                road.current_traffic = 1.0
                
        print(f"Updated {updated_roads} roads using simple matching")
    
    def _find_matching_traffic(self, road, traffic_data):
        """Find the best matching traffic data for a road segment"""
        # For each traffic data point, calculate distance to our road
        # and return the closest match
        best_distance = float('inf')
        best_traffic = None
        
        road_start_lat = road.start.lat
        road_start_lon = road.start.lon
        road_end_lat = road.end.lat
        road_end_lon = road.end.lon
        
        for data_id, traffic in traffic_data.items():
            # Parse coordinates from data_id (our simple format)
            if '_' in data_id:
                try:
                    parts = data_id.split('_')
                    if len(parts) >= 2:
                        data_lat = float(parts[0])
                        data_lon = float(parts[1])
                        
                        # Calculate distance to road (simple Euclidean distance)
                        dist_to_start = ((data_lat - road_start_lat) ** 2 + 
                                         (data_lon - road_start_lon) ** 2)
                        dist_to_end = ((data_lat - road_end_lat) ** 2 + 
                                       (data_lon - road_end_lon) ** 2)
                        min_dist = min(dist_to_start, dist_to_end)
                        
                        if min_dist < best_distance:
                            best_distance = min_dist
                            best_traffic = traffic
                except:
                    continue
                    
        # Only return traffic data if the match is close enough
        if best_distance < 0.001:  # Threshold for matching
            return best_traffic
        return None
    
    def get_traffic_for_road(self, road_id):
        """Get current traffic condition for a specific road"""
        return self.map_data.roads[road_id].current_traffic