// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let map;
    let mapCenter = [33.4255, -111.9400]; // Default center (Tempe, AZ)
    let startMarker, endMarker, routeLine;
    let selectedStartNode = null;
    let selectedEndNode = null;
    
    // Initialize map
    initMap();
    
    // Load map data
    loadMapData();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize the map
    function initMap() {
        map = L.map('map').setView(mapCenter, 14);
        
        // Use a dark theme map style
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
    }
    
    // Load map data
    function loadMapData() {
        fetch('/api/map-data')
            .then(response => response.json())
            .then(data => {
                // Update map center
                mapCenter = [data.center.lat, data.center.lon];
                map.setView(mapCenter, 14);
                
                // Update system info
                document.getElementById('city-name').textContent = data.city;
                document.getElementById('intersection-count').textContent = 
                    data.intersections_count ? data.intersections_count : 'N/A';
                document.getElementById('last-update').textContent = 
                    formatDateTime(new Date());
            })
            .catch(error => {
                console.error('Error loading map data:', error);
            });
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Panel tabs
        const tabs = document.querySelectorAll('.panel-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Hide all panel content
                document.querySelectorAll('.panel-content').forEach(content => {
                    content.classList.add('hidden');
                });
                
                // Show corresponding panel content
                const panelId = this.getAttribute('data-tab');
                document.getElementById(`${panelId}-panel`).classList.remove('hidden');
            });
        });
        
        // Location search
        document.getElementById('search-start').addEventListener('click', function() {
            const location = document.getElementById('start-location').value;
            if (location) {
                searchLocation(location, 'start');
            }
        });
        
        document.getElementById('search-end').addEventListener('click', function() {
            const location = document.getElementById('end-location').value;
            if (location) {
                searchLocation(location, 'end');
            }
        });
        
        // Enter key in search fields
        document.getElementById('start-location').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const location = this.value;
                if (location) {
                    searchLocation(location, 'start');
                }
            }
        });
        
        document.getElementById('end-location').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const location = this.value;
                if (location) {
                    searchLocation(location, 'end');
                }
            }
        });
        
        // Clear selected locations
        document.querySelector('#selected-start .location-clear').addEventListener('click', function() {
            clearSelectedLocation('start');
        });
        
        document.querySelector('#selected-end .location-clear').addEventListener('click', function() {
            clearSelectedLocation('end');
        });
        
        // Find route button
        document.getElementById('find-route').addEventListener('click', findRoute);
        
        // Area exploration
        const areaBtns = document.querySelectorAll('.area-btn');
        areaBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const direction = this.getAttribute('data-direction');
                exploreArea(direction);
            });
        });
        
        // Update traffic button
        document.getElementById('update-traffic').addEventListener('click', updateTraffic);
        
        // View traffic map button
        document.getElementById('view-traffic-map').addEventListener('click', viewTrafficMap);
    }
    
    // Search for a location
    function searchLocation(location, type) {
        fetch('/api/geocode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ location: location })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showSearchResults([], type);
                alert(data.error);
                return;
            }
            
            // Show results
            showSearchResults(data.nearest_nodes, type);
            
            // Pan map to location
            map.panTo([data.coordinates.lat, data.coordinates.lon]);
            
            // Add a temporary marker
            const tempMarker = L.circleMarker([data.coordinates.lat, data.coordinates.lon], {
                radius: 8,
                color: '#6c40ff',
                fillColor: '#6c40ff',
                fillOpacity: 0.5
            }).addTo(map);
            
            // Remove marker after 3 seconds
            setTimeout(() => {
                map.removeLayer(tempMarker);
            }, 3000);
        })
        .catch(error => {
            console.error('Error searching location:', error);
            showSearchResults([], type);
            alert('Error searching for location. Please try again.');
        });
    }
    
    // Show search results
    function showSearchResults(nodes, type) {
        const resultsContainer = document.getElementById(`${type}-results`);
        resultsContainer.innerHTML = '';
        
        if (nodes.length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        // Create result items
        nodes.forEach(node => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.innerHTML = `
                <div class="result-description">${node.description}</div>
                <div class="result-distance">${(node.distance * 1000).toFixed(0)}m away</div>
            `;
            
            // Add click event
            resultItem.addEventListener('click', function() {
                selectNode(node, type);
                resultsContainer.style.display = 'none';
            });
            
            resultsContainer.appendChild(resultItem);
        });
        
        resultsContainer.style.display = 'block';
    }
    
    // Select a node
    function selectNode(node, type) {
        // Update selected node
        if (type === 'start') {
            selectedStartNode = node.node_id;
            
            // Update display
            document.getElementById('selected-start').style.display = 'flex';
            document.querySelector('#selected-start .location-name').textContent = node.description;
            
            // Update map marker
            if (startMarker) {
                map.removeLayer(startMarker);
            }
            
            startMarker = L.marker([node.lat, node.lon], {
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: `<div style="background-color:#4cd964; width:15px; height:15px; border-radius:50%; border:2px solid white;"></div>`,
                    iconSize: [15, 15],
                    iconAnchor: [7, 7]
                })
            }).addTo(map);
            
        } else if (type === 'end') {
            selectedEndNode = node.node_id;
            
            // Update display
            document.getElementById('selected-end').style.display = 'flex';
            document.querySelector('#selected-end .location-name').textContent = node.description;
            
            // Update map marker
            if (endMarker) {
                map.removeLayer(endMarker);
            }
            
            endMarker = L.marker([node.lat, node.lon], {
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: `<div style="background-color:#ff453a; width:15px; height:15px; border-radius:50%; border:2px solid white;"></div>`,
                    iconSize: [15, 15],
                    iconAnchor: [7, 7]
                })
            }).addTo(map);
        }
        
        // Clear input field
        document.getElementById(`${type}-location`).value = '';
    }
    
    // Clear selected location
    function clearSelectedLocation(type) {
        if (type === 'start') {
            selectedStartNode = null;
            document.getElementById('selected-start').style.display = 'none';
            
            if (startMarker) {
                map.removeLayer(startMarker);
                startMarker = null;
            }
        } else if (type === 'end') {
            selectedEndNode = null;
            document.getElementById('selected-end').style.display = 'none';
            
            if (endMarker) {
                map.removeLayer(endMarker);
                endMarker = null;
            }
        }
        
        // Hide route if either start or end is cleared
        if (!selectedStartNode || !selectedEndNode) {
            hideRouteInfo();
            
            if (routeLine) {
                map.removeLayer(routeLine);
                routeLine = null;
            }
        }
    }
    
    // Find optimal route
    function findRoute() {
        if (!selectedStartNode || !selectedEndNode) {
            alert('Please select both starting point and destination.');
            return;
        }
        
        // Get algorithm choice
        const useAStar = document.getElementById('algorithm-toggle').checked;
        const algorithm = useAStar ? 'a_star' : 'dijkstra';
        
        // Show loading state
        document.getElementById('find-route').textContent = 'Finding Route...';
        document.getElementById('find-route').disabled = true;
        
        // Make API request
        fetch('/api/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_node: selectedStartNode,
                end_node: selectedEndNode,
                algorithm: algorithm
            })
        })
        .then(response => response.json())
        .then(data => {
            // Reset button
            document.getElementById('find-route').textContent = 'Find Best Route';
            document.getElementById('find-route').disabled = false;
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Display route on map
            displayRoute(data);
            
            // Show route info
            showRouteInfo(data);
        })
        .catch(error => {
            console.error('Error finding route:', error);
            document.getElementById('find-route').textContent = 'Find Best Route';
            document.getElementById('find-route').disabled = false;
            alert('Error finding route. Please try again.');
        });
    }
    
    // Display route on map
    function displayRoute(routeData) {
        // Remove existing route
        if (routeLine) {
            map.removeLayer(routeLine);
        }
        
        // Create a polyline for the route
        const routePoints = routeData.route_points.map(point => [point.lat, point.lon]);
        
        routeLine = L.polyline(routePoints, {
            color: '#6c40ff',
            weight: 5,
            opacity: 0.7,
            lineJoin: 'round'
        }).addTo(map);
        
        // Fit map to show the entire route
        map.fitBounds(routeLine.getBounds(), {
            padding: [50, 50]
        });
    }
    
    // Show route info
    function showRouteInfo(routeData) {
        // Update route metrics
        document.getElementById('route-time').textContent = routeData.time_minutes.toFixed(1);
        document.getElementById('route-distance').textContent = routeData.distance_km.toFixed(2);
        
        // Generate directions
        const directionsContainer = document.getElementById('directions');
        directionsContainer.innerHTML = '';
        
        routeData.directions.forEach((step, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = 'direction-step';
            
            // Determine traffic status class
            let trafficClass = 'traffic-light';
            if (step.traffic_status === 'moderate traffic') {
                trafficClass = 'traffic-moderate';
            } else if (step.traffic_status === 'heavy traffic') {
                trafficClass = 'traffic-heavy';
            }
            
            stepElement.innerHTML = `
                <div>
                    <span class="step-number">${index + 1}</span>
                    <span class="step-instruction">${step.direction} ${step.road_name}</span>
                </div>
                <div class="step-details">
                    Travel ${(step.distance).toFixed(0)}m toward ${step.next_intersection}
                    <span class="traffic-indicator ${trafficClass}">${step.traffic_status}</span>
                </div>
            `;
            
            directionsContainer.appendChild(stepElement);
        });
        
        // Show route info panel
        document.getElementById('route-info').classList.remove('hidden');
    }
    
    // Hide route info
    function hideRouteInfo() {
        document.getElementById('route-info').classList.add('hidden');
    }
    
    // Explore area
    function exploreArea(direction) {
        // Calculate coordinates based on direction
        let lat = mapCenter[0];
        let lon = mapCenter[1];
        const offset = 0.01; // ~1km
        
        switch (direction) {
            case 'N':
                lat += offset;
                break;
            case 'S':
                lat -= offset;
                break;
            case 'E':
                lon += offset;
                break;
            case 'W':
                lon -= offset;
                break;
            case 'NE':
                lat += offset;
                lon += offset;
                break;
            case 'NW':
                lat += offset;
                lon -= offset;
                break;
            case 'SE':
                lat -= offset;
                lon += offset;
                break;
            case 'SW':
                lat -= offset;
                lon -= offset;
                break;
            // Center (C) uses the default mapCenter
        }
        
        // Call API to explore area
        fetch('/api/explore-area', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                radius: 0.01
            })
        })
        .then(response => response.json())
        .then(data => {
            // Show results
            showAreaResults(data.nodes);
            
            // Pan map to location
            map.panTo([data.center.lat, data.center.lon]);
            
            // Add a temporary circle to show the area
            const areaCircle = L.circle([data.center.lat, data.center.lon], {
                radius: 1000, // 1km in meters
                color: '#6c40ff',
                fillColor: '#6c40ff',
                fillOpacity: 0.1,
                weight: 1
            }).addTo(map);
            
            // Remove circle after 5 seconds
            setTimeout(() => {
                map.removeLayer(areaCircle);
            }, 5000);
        })
        .catch(error => {
            console.error('Error exploring area:', error);
            alert('Error exploring area. Please try again.');
        });
    }
    
    // Show area results
    function showAreaResults(nodes) {
        const resultsContainer = document.getElementById('area-results');
        resultsContainer.innerHTML = '';
        
        if (nodes.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-message">No nodes found in this area.</div>';
            return;
        }
        
        // Only show the first 20 nodes
        const nodesToShow = nodes.slice(0, 20);
        
        // Create result items
        nodesToShow.forEach(node => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.innerHTML = `
                <div class="result-description">${node.description}</div>
                <div class="result-actions">
                    <button class="btn-set-start">Set as Start</button>
                    <button class="btn-set-end">Set as End</button>
                </div>
            `;
            
            // Add click events for buttons
            resultItem.querySelector('.btn-set-start').addEventListener('click', function(e) {
                e.stopPropagation();
                selectNodeFromExploration(node, 'start');
                
                // Switch to route tab
                document.querySelector('.panel-tab[data-tab="route"]').click();
            });
            
            resultItem.querySelector('.btn-set-end').addEventListener('click', function(e) {
                e.stopPropagation();
                selectNodeFromExploration(node, 'end');
                
                // Switch to route tab
                document.querySelector('.panel-tab[data-tab="route"]').click();
            });
            
            resultsContainer.appendChild(resultItem);
        });
        
        // Add message if there are more nodes
        if (nodes.length > 20) {
            const moreMessage = document.createElement('div');
            moreMessage.className = 'more-message';
            moreMessage.textContent = `${nodes.length - 20} more nodes not shown`;
            resultsContainer.appendChild(moreMessage);
        }
    }
    
    // Select node from exploration
    function selectNodeFromExploration(node, type) {
        selectNode({
            node_id: node.node_id,
            description: node.description,
            lat: node.lat,
            lon: node.lon
        }, type);
    }
    
    // Update traffic
    function updateTraffic() {
        const button = document.getElementById('update-traffic');
        button.textContent = 'Updating...';
        button.disabled = true;
        
        fetch('/api/traffic/update', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            button.textContent = 'Update Traffic Now';
            button.disabled = false;
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Update the last update timestamp
            document.getElementById('last-update').textContent = formatDateTime(new Date());
            
            // Show success message
            alert('Traffic data updated successfully!');
            
            // If we have a route displayed, refresh it
            if (selectedStartNode && selectedEndNode) {
                findRoute();
            }
        })
        .catch(error => {
            console.error('Error updating traffic:', error);
            button.textContent = 'Update Traffic Now';
            button.disabled = false;
            alert('Error updating traffic. Please try again.');
        });
    }
    
    // View traffic map
    function viewTrafficMap() {
        // Create and open traffic map in a new tab/window
        window.open('/static/traffic_map.html', '_blank');
    }
    
    // Format date and time
    function formatDateTime(date) {
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
});