try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Folium not available. Map visualization will be limited.")

import matplotlib.pyplot as plt

def create_map_visualization(map_data, path=None, traffic_data=None, 
                           output_file="route_map.html"):
    """
    Create an interactive map visualization
    """
    if not FOLIUM_AVAILABLE:
        print("Folium is not available. Falling back to basic visualization.")
        return create_basic_visualization(map_data, path)
        
    # Find center of map
    center_lat = sum(i.lat for i in map_data.intersections.values()) / len(map_data.intersections)
    center_lon = sum(i.lon for i in map_data.intersections.values()) / len(map_data.intersections)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    
    # Add all roads with traffic colors if available
    for road_id, road in map_data.roads.items():
        start = road.start
        end = road.end
        
        color = 'gray'
        weight = 2
        opacity = 0.7
        
        # Color based on traffic if available
        traffic_level = road.current_traffic
        if traffic_level < 1.2:
            color = 'green'  # Light traffic
        elif traffic_level < 1.8:
            color = 'orange'  # Moderate traffic
        else:
            color = 'red'  # Heavy traffic
            weight = 3
            opacity = 0.9
            
        # Draw road line
        folium.PolyLine(
            locations=[(start.lat, start.lon), (end.lat, end.lon)],
            color=color,
            weight=weight,
            opacity=opacity,
            tooltip=f"{road.name or 'Unnamed'}: {traffic_level:.1f}x"
        ).add_to(m)
    
    # Add route if provided
    if path:
        route_points = []
        for i in range(len(path)-1):
            current = map_data.intersections[path[i]]
            route_points.append((current.lat, current.lon))
            
            # Add destination
            if i == len(path)-2:
                dest = map_data.intersections[path[i+1]]
                route_points.append((dest.lat, dest.lon))
        
        # Draw route
        folium.PolyLine(
            locations=route_points,
            color='blue',
            weight=5,
            opacity=0.8
        ).add_to(m)
        
        # Add markers for start and end
        start_point = map_data.intersections[path[0]]
        end_point = map_data.intersections[path[-1]]
        
        folium.Marker(
            location=[start_point.lat, start_point.lon],
            icon=folium.Icon(color='green', icon='play'),
            tooltip='Start'
        ).add_to(m)
        
        folium.Marker(
            location=[end_point.lat, end_point.lon],
            icon=folium.Icon(color='red', icon='stop'),
            tooltip='Destination'
        ).add_to(m)
    
    # Save map
    m.save(output_file)
    print(f"Map saved to {output_file}")
    
    return m

def create_basic_visualization(map_data, path=None):
    """Create a basic matplotlib visualization"""
    plt.figure(figsize=(10, 8))
    
    # Plot all roads
    for road_id, road in map_data.roads.items():
        start = road.start
        end = road.end
        
        # Color based on traffic
        color = 'gray'
        if road.current_traffic < 1.2:
            color = 'green'
        elif road.current_traffic < 1.8:
            color = 'orange'
        else:
            color = 'red'
            
        plt.plot([start.lon, end.lon], [start.lat, end.lat], 
                 color=color, linewidth=1, alpha=0.5)
    
    # Plot route if provided
    if path:
        route_x = []
        route_y = []
        for node_id in path:
            node = map_data.intersections[node_id]
            route_x.append(node.lon)
            route_y.append(node.lat)
            
        plt.plot(route_x, route_y, 'b-', linewidth=3)
        
        # Mark start and end
        plt.plot(route_x[0], route_y[0], 'go', markersize=10)  # Start
        plt.plot(route_x[-1], route_y[-1], 'ro', markersize=10)  # End
    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Traffic Map')
    plt.grid(True)
    plt.savefig('traffic_map.png')
    plt.close()
    
    print("Map saved to traffic_map.png")