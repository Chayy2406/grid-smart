from .priority_queue import PriorityQueue
import math

def dijkstra(graph, start, end):
    """
    Find shortest path using Dijkstra's algorithm
    
    Args:
        graph: Graph representation with nodes and edges
        start: Starting intersection ID
        end: Destination intersection ID
    
    Returns:
        Tuple of (path, total_time) or (None, math.inf) if no path exists
    """
    queue = PriorityQueue()
    queue.add(start, 0)
    
    # Track best known distance to each node
    distances = {node: math.inf for node in graph.intersections}
    distances[start] = 0
    
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
            
            # Calculate new distance
            distance = distances[current] + travel_time
            
            # If we found a better path, update
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current
                queue.add(neighbor, distance)
    
    # Build path from start to end
    if distances[end] == math.inf:
        return None, math.inf
        
    path = []
    current = end
    while current != start:
        path.append(current)
        current = previous[current]
    path.append(start)
    path.reverse()
    
    return path, distances[end]