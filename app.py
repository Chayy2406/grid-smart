# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import threading
import time

# Import your existing modules
from src.data.map_data import MapData
from src.data.traffic_data import TrafficData
from src.algorithms.dijkstra import dijkstra
from src.algorithms.a_star import a_star
from src.utils.visualization import create_map_visualization
from src.utils.geocoding import GeocodingService
from src.utils.config import load_config

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')
CORS(app)  # Enable CORS for all routes

# Initialize global objects
try:
    config = load_config()
except Exception as e:
    print(f"Error loading config: {e}")
    config = {
        'map': {'city': "Tempe, AZ"},
        'traffic': {'update_interval': 300},
        'routing': {'default_algorithm': "a_star"}
    }

api_key = config.get('traffic', {}).get('api_key') or os.environ.get('TOMTOM_API_KEY')
update_interval = config.get('traffic', {}).get('update_interval', 300)

# Load map data (this is done once when app starts)
print("Loading map data...")
map_data = MapData(city=config.get('map', {}).get('city', "Tempe, AZ"))
map_data.load_map()
print(f"Loaded {len(map_data.intersections)} intersections and {len(map_data.roads)} roads")

# Initialize services
traffic_data = TrafficData(map_data, api_key=api_key)
geocoding = GeocodingService()

# Background traffic updates
def update_traffic_periodically(traffic_data, interval):
    """Background thread to update traffic at regular intervals"""
    while True:
        try:
            traffic_data.update_traffic()
            print(f"Traffic updated at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Error updating traffic: {e}")
        time.sleep(interval)

# Start the background traffic update thread
traffic_thread = threading.Thread(
    target=update_traffic_periodically,
    args=(traffic_data, update_interval),
    daemon=True
)
traffic_thread.start()

# Initial traffic update
traffic_data.update_traffic()

# Helper functions
def get_node_description(node_id):
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

def find_nodes_by_coordinates(lat, lon, max_count=5):
    """Find nearest nodes to the given coordinates"""
    from src.utils.geospatial import haversine_distance
    
    # Calculate distances to all nodes
    nodes_with_distances = []
    
    for node_id, intersection in map_data.intersections.items():
        distance = haversine_distance(lat, lon, intersection.lat, intersection.lon)
        description = get_node_description(node_id)
        nodes_with_distances.append({
            "node_id": node_id,
            "distance": distance,
            "description": description,
            "lat": intersection.lat,
            "lon": intersection.lon
        })
    
    # Sort by distance and return the closest ones
    nodes_with_distances.sort(key=lambda x: x["distance"])
    return nodes_with_distances[:max_count]

def find_node_by_id(node_id):
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

# Define API routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/geocode', methods=['POST'])
def geocode_location():
    """Geocode an address to coordinates"""
    data = request.json
    if not data or 'location' not in data:
        return jsonify({"error": "Missing location parameter"}), 400
    
    location = data['location']
    coords = geocoding.address_to_coordinates(location)
    
    if not coords:
        return jsonify({"error": f"Could not find coordinates for '{location}'"}), 404
    
    lat, lon = coords
    
    # Find nearest nodes
    nearest_nodes = find_nodes_by_coordinates(lat, lon, 5)
    
    return jsonify({
        "location": location,
        "coordinates": {"lat": lat, "lon": lon},
        "nearest_nodes": nearest_nodes
    })

@app.route('/api/explore-area', methods=['POST'])
def explore_area():
    """Get nodes in a specific area"""
    data = request.json
    if not data or 'lat' not in data or 'lon' not in data:
        return jsonify({"error": "Missing coordinates"}), 400
    
    lat = float(data['lat'])
    lon = float(data['lon'])
    radius = float(data.get('radius', 0.01))  # Default ~1km radius
    
    # Find nodes in this area
    area_nodes = []
    for node_id, intersection in map_data.intersections.items():
        dist = ((intersection.lat - lat) ** 2 + 
                (intersection.lon - lon) ** 2) ** 0.5
        if dist < radius:
            description = get_node_description(node_id)
            area_nodes.append({
                "node_id": node_id,
                "distance": dist,
                "description": description,
                "lat": intersection.lat,
                "lon": intersection.lon
            })
    
    # Sort by distance
    area_nodes.sort(key=lambda x: x["distance"])
    
    return jsonify({
        "center": {"lat": lat, "lon": lon},
        "nodes": area_nodes[:50]  # Limit to 50 nodes max
    })

@app.route('/api/route', methods=['POST'])
def find_route():
    """Find a route between two nodes"""
    data = request.json
    if not data or 'start_node' not in data or 'end_node' not in data:
        return jsonify({"error": "Missing start or end node"}), 400
    
    start_node = find_node_by_id(data['start_node'])
    end_node = find_node_by_id(data['end_node'])
    
    if not start_node or not end_node:
        return jsonify({"error": "Invalid node IDs"}), 400
    
    algorithm = data.get('algorithm', 'a_star')
    
    try:
        # Find route
        if algorithm == 'a_star':
            path, time_minutes = a_star(map_data, start_node, end_node)
        else:
            path, time_minutes = dijkstra(map_data, start_node, end_node)
        
        if not path or len(path) < 2:
            return jsonify({"error": "No route found"}), 404
            
        # Generate route details
        route_details = []
        total_distance = 0
        prev_road_name = None
        
        # Create map visualization
        map_file = f"route_{start_node}_{end_node}.html"
        create_map_visualization(
            map_data, 
            path=path, 
            traffic_data=traffic_data,
            output_file=f"static/{map_file}"
        )
        
        # Get route points for frontend
        route_points = []
        for node_id in path:
            node = map_data.intersections[node_id]
            route_points.append({"lat": node.lat, "lon": node.lon})
            
        # Generate turn-by-turn directions
        directions = []
        
        for i in range(len(path)-1):
            current = path[i]
            next_node = path[i+1]
            
            current_desc = get_node_description(current)
            next_desc = get_node_description(next_node)
            
            for road in map_data.intersections[current].connections:
                if road.end.id == next_node:
                    road_name = road.name if road.name else "unnamed road"
                    if isinstance(road_name, list):
                        road_name = road_name[0] if road_name else "unnamed road"
                    
                    traffic_level = road.current_traffic
                    if traffic_level > 1.8:
                        traffic_status = "heavy traffic"
                    elif traffic_level > 1.2:
                        traffic_status = "moderate traffic"
                    else:
                        traffic_status = "light traffic"
                    
                    if i == 0:
                        direction = "Start on"
                    else:
                        direction = "Continue on" if prev_road_name == road_name else "Turn onto"
                    
                    directions.append({
                        "direction": direction,
                        "road_name": road_name,
                        "next_intersection": next_desc,
                        "distance": road.length,
                        "traffic_status": traffic_status,
                        "current_node": current,
                        "next_node": next_node
                    })
                    
                    total_distance += road.length
                    prev_road_name = road_name
                    break
        
        # Prepare response
        response = {
            "start_node": {
                "id": start_node,
                "description": get_node_description(start_node),
                "coordinates": {
                    "lat": map_data.intersections[start_node].lat,
                    "lon": map_data.intersections[start_node].lon
                }
            },
            "end_node": {
                "id": end_node,
                "description": get_node_description(end_node),
                "coordinates": {
                    "lat": map_data.intersections[end_node].lat,
                    "lon": map_data.intersections[end_node].lon
                }
            },
            "path": path,
            "route_points": route_points,
            "time_minutes": time_minutes,
            "distance_km": total_distance / 1000,
            "directions": directions,
            "map_url": map_file
        }
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error finding route: {str(e)}"}), 500

@app.route('/api/traffic/update', methods=['POST'])
def update_traffic():
    """Force traffic update"""
    try:
        traffic_data.update_traffic()
        return jsonify({"message": "Traffic data updated"})
    except Exception as e:
        return jsonify({"error": f"Error updating traffic: {str(e)}"}), 500

@app.route('/api/map-data', methods=['GET'])
def get_map_bounds():
    """Get map bounds and center"""
    all_lats = [i.lat for i in map_data.intersections.values()]
    all_lons = [i.lon for i in map_data.intersections.values()]
    
    return jsonify({
        "center": {
            "lat": sum(all_lats) / len(all_lats),
            "lon": sum(all_lons) / len(all_lons)
        },
        "bounds": {
            "min_lat": min(all_lats),
            "max_lat": max(all_lats),
            "min_lon": min(all_lons),
            "max_lon": max(all_lons)
        },
        "city": config.get('map', {}).get('city', "Tempe, AZ")
    })

if __name__ == '__main__':
    app.run(debug=True)