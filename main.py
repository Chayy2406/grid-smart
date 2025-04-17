# main.py
from src.data.map_data import MapData
from src.data.traffic_data import TrafficData
from src.algorithms.dijkstra import dijkstra
from src.algorithms.a_star import a_star
from src.utils.visualization import create_map_visualization
from src.utils.geocoding import GeocodingService
from src.utils.config import load_config
from src.utils.geospatial import haversine_distance
import time
import os
import threading
import datetime

def update_traffic_periodically(traffic_data, interval):
    """Background thread to update traffic at regular intervals"""
    while True:
        try:
            traffic_data.update_traffic()
            print(f"Traffic updated at {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Error updating traffic: {e}")
        time.sleep(interval)

def test_traffic_api(map_data, api_key=None):
    """Test the traffic API and print results"""
    from src.api.traffic_api import TomTomTrafficAPI
    
    # Calculate bounding box
    min_lat = min(i.lat for i in map_data.intersections.values())
    max_lat = max(i.lat for i in map_data.intersections.values())
    min_lon = min(i.lon for i in map_data.intersections.values())
    max_lon = max(i.lon for i in map_data.intersections.values())
    
    # Create API client
    api = TomTomTrafficAPI(api_key)
    
    # Fetch and print traffic data
    print(f"Testing traffic API with bounding box: {min_lat},{min_lon},{max_lat},{max_lon}")
    traffic_data = api.get_traffic_flow((min_lat, min_lon, max_lat, max_lon))
    
    print(f"Received {len(traffic_data)} traffic data points")
    
    # Print first 5 data points
    for i, (road_id, traffic) in enumerate(traffic_data.items()):
        if i >= 5:
            break
        print(f"  Road {road_id}: Traffic multiplier {traffic:.2f}")
    
    return traffic_data

def find_node_by_id(node_id, map_data):
    """Helper function to find a node by ID, handling type conversion if needed"""
    # Try direct lookup
    if node_id in map_data.intersections:
        return node_id
    
    # Try as integer if the input is a string
    if isinstance(node_id, str) and node_id.isdigit():
        int_id = int(node_id)
        if int_id in map_data.intersections:
            return int_id
    
    # Try as string if the input is an integer
    if isinstance(node_id, int):
        str_id = str(node_id)
        if str_id in map_data.intersections:
            return str_id
    
    return None

def get_node_description(map_data, node_id):
    """Generate a human-readable description of an intersection node"""
    intersection = map_data.intersections[node_id]
    
    # Get all road names connected to this intersection
    road_names = set()
    for road in intersection.connections:
        if road.name:
            # Handle if road.name is a list
            if isinstance(road.name, list):
                for name in road.name:
                    if name:  # Only add non-empty names
                        road_names.add(name)
            else:
                road_names.add(road.name)
    
    if not road_names:
        return f"Unnamed intersection at {intersection.lat:.6f}, {intersection.lon:.6f}"
    
    if len(road_names) == 1:
        return f"{next(iter(road_names))}"
    
    # If we have two or more road names, it's an intersection
    road_list = sorted(list(road_names))
    if len(road_list) == 2:
        return f"Intersection of {road_list[0]} and {road_list[1]}"
    else:
        main_roads = road_list[:2]
        return f"Intersection of {main_roads[0]} and {main_roads[1]} (+ {len(road_list)-2} more)"

def find_nearest_nodes(map_data, lat, lon, count=5):
    """Find the nearest nodes to the given coordinates with descriptions"""
    # Calculate distances to all nodes
    nodes_with_distances = []
    
    for node_id, intersection in map_data.intersections.items():
        distance = haversine_distance(lat, lon, intersection.lat, intersection.lon)
        
        # Get description based on connected roads
        description = get_node_description(map_data, node_id)
        
        nodes_with_distances.append((node_id, distance, description))
    
    # Sort by distance and return the closest ones
    nodes_with_distances.sort(key=lambda x: x[1])
    return nodes_with_distances[:count]

def find_nodes_by_location(map_data, geocoding):
    """Find nodes by address, landmark, or nearby road intersections"""
    print("\n=== Find Node by Location ===")
    print("Enter a location description (address, landmark, intersection, etc.)")
    print("Examples: 'Mill Ave and University Dr', 'ASU Tempe Campus', '699 S Mill Ave'")
    
    location = input("Enter location: ")
    
    # Geocode the location
    print(f"Finding coordinates for '{location}'...")
    coords = geocoding.address_to_coordinates(location)
    
    if not coords:
        print("Could not find coordinates for this location. Try a different description.")
        return None
        
    lat, lon = coords
    print(f"Found coordinates: {lat}, {lon}")
    
    # Find nearest nodes
    nearest_nodes = find_nearest_nodes(map_data, lat, lon, 5)
    
    if not nearest_nodes:
        print("No nodes found near this location.")
        return None
        
    # Display the nodes with descriptions
    print("\nNearest intersections:")
    for i, (node_id, distance, description) in enumerate(nearest_nodes):
        print(f"{i+1}. {description} (Node ID: {node_id}, Distance: {distance:.2f}km)")
    
    # Let user select a node
    selection = input("\nSelect a node number (or press Enter to cancel): ")
    if not selection:
        return None
        
    # Check if the input is a node ID directly
    if selection in map_data.intersections:
        return selection
    
    # Check if input is a digit for selecting from the list
    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(nearest_nodes):
            return nearest_nodes[index][0]  # Return the node ID
    
    # Check if the selection matches a node ID from the list
    for node_id, _, _ in nearest_nodes:
        if str(node_id) == selection:
            return node_id
    
    print(f"Invalid selection: {selection}")
    return None

def explore_node_area(map_data):
    """Explore nodes in a geographic area and assign user-friendly names"""
    print("\n=== Explore Map Area ===")
    
    # 1. Calculate center point of the map
    all_lats = [i.lat for i in map_data.intersections.values()]
    all_lons = [i.lon for i in map_data.intersections.values()]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    print(f"Map center: {center_lat:.6f}, {center_lon:.6f}")
    
    # 2. Define search areas
    areas = [
        ("Central", center_lat, center_lon),
        ("North", center_lat + 0.01, center_lon),
        ("South", center_lat - 0.01, center_lon),
        ("East", center_lat, center_lon + 0.01),
        ("West", center_lat, center_lon - 0.01),
        ("Northeast", center_lat + 0.01, center_lon + 0.01),
        ("Northwest", center_lat + 0.01, center_lon - 0.01),
        ("Southeast", center_lat - 0.01, center_lon + 0.01),
        ("Southwest", center_lat - 0.01, center_lon - 0.01)
    ]
    
    # 3. Let user choose an area to explore
    print("\nChoose an area to explore:")
    for i, (name, _, _) in enumerate(areas):
        print(f"{i+1}. {name}")
    
    choice = input("Enter area number: ")
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(areas):
        print("Invalid choice.")
        return None
    
    area_name, area_lat, area_lon = areas[int(choice) - 1]
    print(f"\nExploring {area_name} area...")
    
    # 4. Find nodes in this area
    area_nodes = []
    for node_id, intersection in map_data.intersections.items():
        dist = ((intersection.lat - area_lat) ** 2 + 
                (intersection.lon - area_lon) ** 2) ** 0.5
        if dist < 0.01:  # Roughly 1.1 km radius
            description = get_node_description(map_data, node_id)
            area_nodes.append((node_id, dist, description))
    
    # Sort by distance
    area_nodes.sort(key=lambda x: x[1])
    
    # 5. Display nodes with their descriptions
    if not area_nodes:
        print("No nodes found in this area.")
        return None
    
    print(f"\nFound {len(area_nodes)} nodes in the {area_name} area:")
    for i, (node_id, dist, description) in enumerate(area_nodes[:20]):
        print(f"{i+1}. {description} (Node ID: {node_id})")
    
    # 6. Let user select a node
    selection = input("\nSelect a node number (or press Enter to cancel): ")
    if not selection or not selection.isdigit():
        return None
    
    index = int(selection) - 1
    if 0 <= index < len(area_nodes[:20]):
        return area_nodes[index][0]  # Return the node ID
    
    return None

def main():
    print("Initializing Traffic-Aware Routing System for Tempe, AZ")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        # Default config if loading fails
        config = {
            'map': {'city': "Tempe, AZ"},
            'traffic': {'update_interval': 300},
            'routing': {'default_algorithm': "a_star"}
        }
    
    # Get API key
    api_key = config.get('traffic', {}).get('api_key') or os.environ.get('TOMTOM_API_KEY')
    update_interval = config.get('traffic', {}).get('update_interval', 300)
    
    # Load map data
    print("Loading map data...")
    map_data = MapData(city=config.get('map', {}).get('city', "Tempe, AZ"))
    map_data.load_map()
    print(f"Loaded {len(map_data.intersections)} intersections and {len(map_data.roads)} roads")
    
    # Initialize services
    traffic_data = TrafficData(map_data, api_key=api_key)
    geocoding = GeocodingService()
    
    # Do an initial traffic update
    print("Fetching initial traffic data...")
    traffic_data.update_traffic()
    
    # Start background traffic update thread
    print(f"Starting background traffic updates every {update_interval} seconds")
    traffic_thread = threading.Thread(
        target=update_traffic_periodically,
        args=(traffic_data, update_interval),
        daemon=True  # Thread will exit when main program exits
    )
    traffic_thread.start()
    
    # Main program loop
    while True:
        print("\n===== Traffic-Aware Routing System =====")
        print("1. Find route")
        print("2. Test traffic API")
        print("3. View traffic map")
        print("4. Force traffic update")
        print("5. Exit")
        
        choice = input("Enter choice: ")
        
        if choice == "1":
            print("\n=== Routing ===")
            print("1. Use node IDs directly")
            print("2. Find locations by address/landmark")
            print("3. Explore map areas")
            route_choice = input("Enter choice: ")
            
            if route_choice == "1":
                # Original node ID-based routing
                node_list = list(map_data.intersections.keys())
                print("Available nodes:", node_list[:5], "...")
                
                # Get starting node
                start_input = input("Enter starting node ID: ")
                start_node = find_node_by_id(start_input, map_data)
                
                # Get destination node
                end_input = input("Enter destination node ID: ")
                end_node = find_node_by_id(end_input, map_data)
                
            elif route_choice == "2":
                # Find nodes by location
                print("\n--- Starting Location ---")
                start_node = find_nodes_by_location(map_data, geocoding)
                if not start_node:
                    print("No starting point selected. Returning to main menu.")
                    continue
                    
                print("\n--- Destination Location ---")
                end_node = find_nodes_by_location(map_data, geocoding)
                if not end_node:
                    print("No destination selected. Returning to main menu.")
                    continue
                    
            elif route_choice == "3":
                # Explore map areas
                print("\n--- Starting Location ---")
                start_node = explore_node_area(map_data)
                if not start_node:
                    print("No starting point selected. Returning to main menu.")
                    continue
                    
                print("\n--- Destination Location ---")
                end_node = explore_node_area(map_data)
                if not end_node:
                    print("No destination selected. Returning to main menu.")
                    continue
            
            else:
                print("Invalid choice. Returning to main menu.")
                continue
            
            if not start_node or not end_node:
                print("Invalid node IDs. Please try again.")
                continue
            
            print(f"Finding best route from {start_node} to {end_node}...")
            
            # Choose algorithm
            use_astar = config.get('routing', {}).get('default_algorithm', "a_star") == "a_star"
            if use_astar:
                print("Using A* algorithm for routing")
            else:
                print("Using Dijkstra's algorithm for routing")
            
            try:
                # Find route
                if use_astar:
                    path, time_minutes = a_star(map_data, start_node, end_node)
                else:
                    path, time_minutes = dijkstra(map_data, start_node, end_node)
                
                if path and len(path) > 1:
                    print(f"Found route with {len(path)-1} segments")
                    print(f"Estimated travel time: {time_minutes:.1f} minutes")
                    
                    # Start and end descriptions
                    start_desc = get_node_description(map_data, path[0])
                    end_desc = get_node_description(map_data, path[-1])
                    print(f"\nRoute from {start_desc} to {end_desc}:")
                    
                    # Display route info
                    print("\nTurn-by-turn directions:")
                    total_distance = 0
                    prev_road_name = None
                    
                    for i in range(len(path)-1):
                        current = path[i]
                        next_node = path[i+1]
                        for road in map_data.intersections[current].connections:
                            if road.end.id == next_node:
                                road_name = road.name or "unnamed road"
                                next_intersection = get_node_description(map_data, next_node)
                                traffic_status = "heavy traffic" if road.current_traffic > 1.8 else \
                                               "moderate traffic" if road.current_traffic > 1.2 else \
                                               "light traffic"
                                direction = "Start on" if i == 0 else ("Continue on" if prev_road_name == road_name else "Turn onto")
                                print(f"  {i+1}. {direction} {road_name} toward {next_intersection}")
                                print(f"     Travel {road.length:.0f}m ({traffic_status})")
                                total_distance += road.length
                                prev_road_name = road_name
                                break
                    
                    print(f"\nTotal distance: {total_distance/1000:.2f} km")
                    
                    # Visualize route
                    print("Creating route map...")
                    create_map_visualization(
                        map_data, 
                        path=path, 
                        traffic_data=traffic_data,
                        output_file="route_map.html"
                    )
                    print("Route map created. Open route_map.html in your browser to view.")

                else:
                    print("No route found between these locations.")
            except Exception as e:
                print(f"Error finding route: {e}")
                import traceback
                traceback.print_exc()

        elif choice == "2":
            print("Testing traffic API...")
            test_traffic_api(map_data, api_key)

        elif choice == "3":
            print("Creating traffic map...")
            create_map_visualization(
                map_data,
                traffic_data=traffic_data,
                output_file="traffic_map.html"
            )
            print("Traffic map created. Open traffic_map.html in your browser to view.")

        elif choice == "4":
            print("Forcing traffic update...")
            traffic_data.update_traffic()
            print("Traffic data updated")

        elif choice == "5":
            print("Exiting...")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
