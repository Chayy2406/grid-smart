import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.intersection import Intersection
from src.models.road import Road
from src.algorithms.dijkstra import dijkstra
from src.algorithms.a_star import a_star

class TestGraph:
    """Test fixture with a simple graph"""
    
    def __init__(self):
        self.intersections = {}
        self.roads = {}
        
        # Create a simple grid network
        for i in range(3):
            for j in range(3):
                node_id = f"{i}_{j}"
                self.intersections[node_id] = Intersection(
                    id=node_id,
                    lat=i,
                    lon=j
                )
        
        # Connect horizontally
        for i in range(3):
            for j in range(2):
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
                
                # Add reverse direction
                road_rev = Road(
                    id=f"h_{end_id}_{start_id}",
                    start_intersection=self.intersections[end_id],
                    end_intersection=self.intersections[start_id],
                    length=1000,  # 1km
                    speed_limit=50,  # 50km/h
                    name=f"East-West Road {i}_{j} Rev"
                )
                
                self.roads[road_rev.id] = road_rev
                self.intersections[end_id].add_connection(road_rev)
        
        # Connect vertically
        for i in range(2):
            for j in range(3):
                start_id = f"{i}_{j}"
                end_id = f"{i+1}_{j}"
                
                road = Road(
                    id=f"v_{start_id}_{end_id}",
                    start_intersection=self.intersections[start_id],
                    end_intersection=self.intersections[end_id],
                    length=1000,  # 1km
                    speed_limit=50,  # 50km/h
                    name=f"North-South Road {i}_{j}"
                )
                
                self.roads[road.id] = road
                self.intersections[start_id].add_connection(road)
                
                # Add reverse direction
                road_rev = Road(
                    id=f"v_{end_id}_{start_id}",
                    start_intersection=self.intersections[end_id],
                    end_intersection=self.intersections[start_id],
                    length=1000,  # 1km
                    speed_limit=50,  # 50km/h
                    name=f"North-South Road {i}_{j} Rev"
                )
                
                self.roads[road_rev.id] = road_rev
                self.intersections[end_id].add_connection(road_rev)
        
        # Add traffic to one route
        self.roads["h_0_0_0_1"].current_traffic = 3.0  # Heavy traffic
        self.roads["h_0_1_0_2"].current_traffic = 3.0  # Heavy traffic

def test_dijkstra():
    """Test that Dijkstra's algorithm finds the correct path"""
    graph = TestGraph()
    
    # Test direct path
    path, time = dijkstra(graph, "0_0", "0_2")
    assert path == ["0_0", "0_1", "0_2"]
    
    # Test with traffic - should find alternate route
    # Even though it's longer distance, it should be faster
    graph.roads["h_0_0_0_1"].current_traffic = 10.0  # Very heavy traffic
    path, time = dijkstra(graph, "0_0", "0_2")
    # Should go 0_0 -> 1_0 -> 1_1 -> 1_2 -> 0_2 to avoid traffic
    assert path == ["0_0", "1_0", "1_1", "1_2", "0_2"]
    
def test_a_star():
    """Test that A* algorithm finds the correct path"""
    graph = TestGraph()
    
    # Test direct path
    path, time = a_star(graph, "0_0", "0_2")
    assert path == ["0_0", "0_1", "0_2"]
    
    # A* should be faster than Dijkstra for diagonal paths
    path, time = a_star(graph, "0_0", "2_2")
    assert path is not None
    
    # Test with traffic - should find alternate route
    graph.roads["h_0_0_0_1"].current_traffic = 10.0  # Very heavy traffic
    path, time = a_star(graph, "0_0", "0_2")
    # Should avoid the traffic
    assert "0_1" not in path