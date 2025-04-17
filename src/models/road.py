class Road:
    def __init__(self, id, start_intersection, end_intersection, 
                 length, speed_limit, name=None):
        self.id = id
        self.start = start_intersection
        self.end = end_intersection
        self.length = length        # in meters
        self.speed_limit = speed_limit  # in km/h
        self.name = name
        self.current_traffic = 1.0  # Traffic multiplier (1.0 = normal)
    
    def travel_time(self):
        """Calculate travel time including traffic conditions"""
        return (self.length / 1000) / (self.speed_limit / self.current_traffic)