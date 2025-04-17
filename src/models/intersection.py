class Intersection:
    def __init__(self, id, lat, lon):
        self.id = id          # Unique identifier
        self.lat = lat        # Latitude
        self.lon = lon        # Longitude
        self.connections = [] # Connecting road segments
    
    def add_connection(self, road):
        self.connections.append(road)