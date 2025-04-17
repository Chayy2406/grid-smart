import heapq

class PriorityQueue:
    """Min-heap implementation for Dijkstra/A* algorithms"""
    
    def __init__(self):
        self.elements = []
        self.entry_finder = {}  # Mapping of items to entries
        self.counter = 0        # Unique sequence count for tie-breaking
    
    def empty(self):
        return len(self.entry_finder) == 0
    
    def add(self, item, priority):
        """Add item with priority or update existing item's priority"""
        if item in self.entry_finder:
            self.remove(item)
        count = self.counter
        self.counter += 1
        entry = [priority, count, item]
        self.entry_finder[item] = entry
        heapq.heappush(self.elements, entry)
    
    def remove(self, item):
        """Remove item from queue"""
        entry = self.entry_finder.pop(item)
        entry[-1] = None  # Mark as removed
    
    def pop(self):
        """Remove and return the lowest priority item"""
        while self.elements:
            priority, count, item = heapq.heappop(self.elements)
            if item is not None:
                del self.entry_finder[item]
                return item
        raise KeyError('Pop from an empty priority queue')