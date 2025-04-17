from .priority_queue import PriorityQueue
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    
    return c * r

def a_star(graph, start, end):
    """
    Find shortest path using A* algorithm
    
    Args:
        graph: Graph representation with nodes and edges
        start: Starting intersection ID
        end: Destination intersection ID
    
    Returns:
        Tuple of (path, total_time) or (None, math.inf) if no path exists
    """
    # Get end coordinates for heuristic
    end_node = graph.intersections[end]
    end_lat, end_lon = end_node.lat, end_node.lon
    
    queue = PriorityQueue()
    queue.add(start, 0)
    
    # Track actual cost from start to each node
    g_score = {node: math.inf for node in graph.intersections}
    g_score[start] = 0
    
    # Track estimated total cost from start to goal through each node
    f_score = {node: math.inf for node in graph.intersections}
    
    # Calculate initial f_score for start
    start_node = graph.intersections[start]
    h_start = haversine_distance(
        start_node.lat, start_node.lon, 
        end_lat, end_lon
    ) / 50  # Assuming 50 km/h average speed
    f_score[start] = h_start
    
    # Track path
    previous = {node: None for node in graph.intersections}
    
    while not queue.empty():
        current = queue.pop()
        
        # Found destination
        if current == end:
            break
            
        # Look at all neighbors
        for road in graph.intersections[current].connections:
            neighbor = road.end.id
            travel_time = road.travel_time()
            
            # Calculate new g_score
            tentative_g_score = g_score[current] + travel_time
            
            # If we found a better path, update
            if tentative_g_score < g_score[neighbor]:
                previous[neighbor] = current
                g_score[neighbor] = tentative_g_score
                
                # Calculate heuristic
                neighbor_node = graph.intersections[neighbor]
                h_score = haversine_distance(
                    neighbor_node.lat, neighbor_node.lon,
                    end_lat, end_lon
                ) / 50  # Assuming 50 km/h average speed
                
                f_score[neighbor] = tentative_g_score + h_score
                queue.add(neighbor, f_score[neighbor])
    
    # Build path from start to end
    if g_score[end] == math.inf:
        return None, math.inf
        
    path = []
    current = end
    while current != start:
        path.append(current)
        current = previous[current]
    path.append(start)
    path.reverse()
    
    return path, g_score[end]