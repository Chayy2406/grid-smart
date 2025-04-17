import osmnx as ox
import networkx as nx
from ..models.intersection import Intersection
from ..models.road import Road

class MapData:
    def __init__(self, city="Tempe, AZ"):
        self.city = city
        self.graph = None
        self.intersections = {}  # id -> Intersection
        self.roads = {}          # id -> Road
    
    def load_map(self):
        """Load road network from OSM for the specified city"""
        try:
            G = ox.graph_from_place(self.city, network_type='drive')
            self.graph = G
            
            # Process nodes (intersections)
            for node_id, data in G.nodes(data=True):
                intersection = Intersection(
                    id=node_id,
                    lat=data['y'],
                    lon=data['x']
                )
                self.intersections[node_id] = intersection
            
            # Process edges (roads)
            for u, v, key, data in G.edges(data=True, keys=True):
                road_id = f"{u}_{v}_{key}"
                
                # Get length or calculate it
                if 'length' in data:
                    length = data['length']
                else:
                    length = ox.distance.great_circle(
                        G.nodes[u]['y'],
                        G.nodes[u]['x'],
                        G.nodes[v]['y'],
                        G.nodes[v]['x']
                    )
                
                # Get speed limit or use default
                if 'speed_kph' in data:
                    speed = data['speed_kph']
                else:
                    speed = 50  # Default 50 km/h
                
                road = Road(
                    id=road_id,
                    start_intersection=self.intersections[u],
                    end_intersection=self.intersections[v],
                    length=length,
                    speed_limit=speed,
                    name=data.get('name', None)
                )
                
                self.roads[road_id] = road
                self.intersections[u].add_connection(road)
                
            print(f"Successfully loaded {len(self.intersections)} intersections and {len(self.roads)} roads.")
        except Exception as e:
            print(f"Error loading map data: {e}")
            # Create a simple test graph for demonstration
            self._create_test_graph()
    
    def _create_test_graph(self):
        """Create a simple test graph for demonstration"""
        print("Creating test graph instead...")
        
        # Create a 3x3 grid of intersections
        for i in range(3):
            for j in range(3):
                node_id = f"{i}_{j}"
                self.intersections[node_id] = Intersection(
                    id=node_id,
                    lat=33.4 + i * 0.01,  # Approximate Tempe coordinates
                    lon=-111.9 + j * 0.01
                )
        
        # Connect the grid with roads
        for i in range(3):
            for j in range(2):
                # Horizontal roads
                start_id = f"{i}_{j}"
                end_id = f"{i}_{j+1}"
                
                road = Road(
                    id=f"h_{start_id}_{end_id}",
                    start_intersection=self.intersections[start_id],
                    end_intersection=self.intersections[end_id],
                    length=1000,  # 1km
                    speed_limit=50,  # 50km/h
                    name=f"East-West Road {i}_{j}"
                )
                
                self.roads[road.id] = road
                self.intersections[start_id].add_connection(road)
                
                # Reverse direction
                road_rev = Road(
                    id=f"h_{end_id}_{start_id}",
                    start_intersection=self.intersections[end_id],
                    end_intersection=self.intersections[start_id],
                    length=1000,
                    speed_limit=50,
                    name=f"East-West Road {i}_{j} Rev"
                )
                
                self.roads[road_rev.id] = road_rev
                self.intersections[end_id].add_connection(road_rev)
                
        # Vertical roads
        for i in range(2):
            for j in range(3):
                start_id = f"{i}_{j}"
                end_id = f"{i+1}_{j}"
                
                road = Road(
                    id=f"v_{start_id}_{end_id}",
                    start_intersection=self.intersections[start_id],
                    end_intersection=self.intersections[end_id],
                    length=1000,
                    speed_limit=50,
                    name=f"North-South Road {i}_{j}"
                )
                
                self.roads[road.id] = road
                self.intersections[start_id].add_connection(road)
                
                # Reverse direction
                road_rev = Road(
                    id=f"v_{end_id}_{start_id}",
                    start_intersection=self.intersections[end_id],
                    end_intersection=self.intersections[start_id],
                    length=1000,
                    speed_limit=50,
                    name=f"North-South Road {i}_{j} Rev"
                )
                
                self.roads[road_rev.id] = road_rev
                self.intersections[end_id].add_connection(road_rev)
        
        print(f"Created test graph with {len(self.intersections)} intersections and {len(self.roads)} roads.")