/**
 * Map.js - Interactive Traffic Map
 * Handles map visualization for traffic data
 */

class TrafficMap {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.markers = new Map();
        this.layers = new Map();
        this.currentLocation = { lat: 40.7128, lng: -74.0060 }; // NYC default
        this.zoomLevel = 12;
        this.init();
    }
    
    async init() {
        // Map library is now loaded in the HTML
        this.createMap();
        this.setupEventListeners();
        this.loadTrafficData();
    }
    
    // Removed loadMapLibrary as it's now loaded in the HTML template
    
    createMap() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container ${this.containerId} not found`);
            return;
        }
        
        // Create map instance
        this.map = L.map(this.containerId).setView(
            [this.currentLocation.lat, this.currentLocation.lng], 
            this.zoomLevel
        );
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Add scale control
        L.control.scale().addTo(this.map);
        
        // Create layer groups
        this.createLayerGroups();
    }
    
    createLayerGroups() {
        // Traffic markers layer
        this.layers.set('traffic', L.layerGroup().addTo(this.map));
        
        // Heatmap layer
        this.layers.set('heatmap', L.layerGroup().addTo(this.map));
        
        // Route layer
        this.layers.set('routes', L.layerGroup().addTo(this.map));
        
        // Incident layer
        this.layers.set('incidents', L.layerGroup().addTo(this.map));
        
        // Signal layer
        this.layers.set('signals', L.layerGroup().addTo(this.map));
    }
    
    async loadTrafficData() {
        try {
            const response = await fetch('/api/traffic-data');
            const data = await response.json();
            this.renderTrafficData(data);
        } catch (error) {
            console.error('Error loading traffic data:', error);
            this.renderSampleData();
        }
    }
    
    renderTrafficData(data) {
        // Clear existing markers
        this.clearLayer('traffic');
        
        // Add traffic markers
        data.locations.forEach(location => {
            this.addTrafficMarker(location);
        });
        
        // Add signal markers
        this.clearLayer('signals');
        data.signals.forEach(signal => {
            this.addSignalMarker(signal);
        });
        
        // Create heatmap if enough data
        if (data.locations.length > 5) {
            this.createHeatmap(data.locations);
        }
    }
    
    renderSampleData() {
        const sampleLocations = [
            { id: 1, name: 'Downtown', lat: 40.7128, lng: -74.0060, congestion: 85 },
            { id: 2, name: 'Midtown', lat: 40.7549, lng: -73.9840, congestion: 75 },
            { id: 3, name: 'Uptown', lat: 40.8610, lng: -73.9390, congestion: 60 },
            { id: 4, name: 'Brooklyn', lat: 40.6782, lng: -73.9442, congestion: 70 },
            { id: 5, name: 'Queens', lat: 40.7282, lng: -73.7949, congestion: 55 },
            { id: 6, name: 'Bronx', lat: 40.8448, lng: -73.8648, congestion: 65 },
            { id: 7, name: 'Staten Island', lat: 40.5795, lng: -74.1502, congestion: 45 }
        ];
        
        sampleLocations.forEach(location => {
            this.addTrafficMarker(location);
        });
    }
    
    addTrafficMarker(location) {
        const color = this.getCongestionColor(location.congestion);
        const size = this.getMarkerSize(location.congestion);
        
        // Create custom icon
        const icon = L.divIcon({
            html: `
                <div class="traffic-marker" style="
                    width: ${size}px;
                    height: ${size}px;
                    background: ${color};
                    border: 2px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: ${size / 3}px;
                    cursor: pointer;
                ">
                    ${Math.round(location.congestion)}
                </div>
            `,
            className: 'custom-traffic-marker',
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2]
        });
        
        const marker = L.marker([location.lat, location.lng], { icon })
            .addTo(this.layers.get('traffic'))
            .bindPopup(`
                <div class="map-popup">
                    <h3>${location.name}</h3>
                    <p><strong>Congestion:</strong> ${location.congestion}%</p>
                    <p><strong>Status:</strong> ${this.getCongestionLevel(location.congestion)}</p>
                    <p><strong>Coordinates:</strong> ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}</p>
                    <button class="btn btn-sm btn-primary" onclick="trafficMap.viewLocationDetails(${location.id})">
                        View Details
                    </button>
                </div>
            `);
        
        this.markers.set(`traffic_${location.id}`, marker);
    }
    
    addSignalMarker(signal) {
        const statusColors = {
            'normal': '#28a745',
            'congested': '#dc3545',
            'heavy': '#ffc107'
        };
        
        const color = statusColors[signal.status] || '#6c757d';
        
        const icon = L.divIcon({
            html: `
                <div class="signal-marker" style="
                    width: 24px;
                    height: 24px;
                    background: ${color};
                    border: 2px solid white;
                    border-radius: 4px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    cursor: pointer;
                    position: relative;
                ">
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                    ">S</div>
                </div>
            `,
            className: 'custom-signal-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        // Use approximate coordinates (in real app, get actual coordinates)
        const lat = 40.7128 + (Math.random() - 0.5) * 0.1;
        const lng = -74.0060 + (Math.random() - 0.5) * 0.1;
        
        const marker = L.marker([lat, lng], { icon })
            .addTo(this.layers.get('signals'))
            .bindPopup(`
                <div class="map-popup">
                    <h3>${signal.location}</h3>
                    <p><strong>Status:</strong> ${signal.status}</p>
                    <p><strong>Cycle Time:</strong> ${signal.cycle_time}s</p>
                    <p><strong>Efficiency:</strong> ${signal.efficiency || 85}%</p>
                    <button class="btn btn-sm btn-primary" onclick="trafficMap.controlSignal(${signal.id})">
                        Control Signal
                    </button>
                </div>
            `);
        
        this.markers.set(`signal_${signal.id}`, marker);
    }
    
    createHeatmap(locations) {
        this.clearLayer('heatmap');
        
        const heatmapData = locations.map(loc => ({
            lat: loc.lat,
            lng: loc.lng,
            intensity: loc.congestion / 100
        }));
        
        // Create heatmap layer
        const heatmapLayer = L.layerGroup();
        
        heatmapData.forEach(point => {
            const radius = 1000 * point.intensity; // Radius in meters
            const color = this.getCongestionColor(point.intensity * 100);
            
            L.circle([point.lat, point.lng], {
                radius: radius,
                color: color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 1
            }).addTo(heatmapLayer);
        });
        
        heatmapLayer.addTo(this.map);
        this.layers.set('heatmap', heatmapLayer);
    }
    
    drawRoute(routePoints, options = {}) {
        this.clearLayer('routes');
        
        const defaultOptions = {
            color: '#4361ee',
            weight: 4,
            opacity: 0.8,
            dashArray: null
        };
        
        const routeOptions = { ...defaultOptions, ...options };
        
        // Convert route points to LatLng array
        const latLngs = routePoints.map(point => [point.lat, point.lng]);
        
        // Create polyline
        const routeLine = L.polyline(latLngs, routeOptions)
            .addTo(this.layers.get('routes'));
        
        // Add start and end markers
        this.addRouteMarker(routePoints[0], 'Start', '#28a745');
        this.addRouteMarker(routePoints[routePoints.length - 1], 'End', '#dc3545');
        
        // Fit map to route bounds
        this.map.fitBounds(routeLine.getBounds());
        
        return routeLine;
    }
    
    addRouteMarker(point, label, color) {
        const icon = L.divIcon({
            html: `
                <div class="route-marker" style="
                    width: 30px;
                    height: 30px;
                    background: ${color};
                    border: 3px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    cursor: pointer;
                ">
                    ${label.charAt(0)}
                </div>
            `,
            className: 'custom-route-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const marker = L.marker([point.lat, point.lng], { icon })
            .addTo(this.layers.get('routes'))
            .bindPopup(`<strong>${label}</strong><br>${point.name || 'Point'}`);
        
        this.markers.set(`route_${label.toLowerCase()}`, marker);
    }
    
    addIncident(incident) {
        const icon = L.divIcon({
            html: `
                <div class="incident-marker" style="
                    width: 32px;
                    height: 32px;
                    background: #dc3545;
                    border: 2px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    animation: pulse 1.5s infinite;
                ">
                    ⚠️
                </div>
                <style>
                    @keyframes pulse {
                        0% { transform: scale(1); opacity: 1; }
                        50% { transform: scale(1.2); opacity: 0.7; }
                        100% { transform: scale(1); opacity: 1; }
                    }
                </style>
            `,
            className: 'custom-incident-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        });
        
        const marker = L.marker([incident.lat, incident.lng], { icon })
            .addTo(this.layers.get('incidents'))
            .bindPopup(`
                <div class="map-popup">
                    <h3>${incident.type}</h3>
                    <p><strong>Severity:</strong> ${incident.severity}</p>
                    <p><strong>Time:</strong> ${incident.time}</p>
                    <p><strong>Description:</strong> ${incident.description}</p>
                    <button class="btn btn-sm btn-warning" onclick="trafficMap.viewIncidentDetails('${incident.id}')">
                        View Details
                    </button>
                </div>
            `);
        
        this.markers.set(`incident_${incident.id}`, marker);
    }
    
    clearLayer(layerName) {
        if (this.layers.has(layerName)) {
            this.layers.get(layerName).clearLayers();
        }
        
        // Remove markers from this layer
        Array.from(this.markers.entries())
            .filter(([key]) => key.startsWith(`${layerName}_`))
            .forEach(([key]) => this.markers.delete(key));
    }
    
    clearAllLayers() {
        this.layers.forEach(layer => layer.clearLayers());
        this.markers.clear();
    }
    
    setView(lat, lng, zoom = null) {
        if (zoom !== null) {
            this.map.setView([lat, lng], zoom);
        } else {
            this.map.setView([lat, lng]);
        }
    }
    
    fitBounds(bounds) {
        this.map.fitBounds(bounds);
    }
    
    showLayer(layerName) {
        if (this.layers.has(layerName)) {
            this.map.addLayer(this.layers.get(layerName));
        }
    }
    
    hideLayer(layerName) {
        if (this.layers.has(layerName)) {
            this.map.removeLayer(this.layers.get(layerName));
        }
    }
    
    toggleLayer(layerName) {
        if (this.layers.has(layerName)) {
            if (this.map.hasLayer(this.layers.get(layerName))) {
                this.hideLayer(layerName);
                return false;
            } else {
                this.showLayer(layerName);
                return true;
            }
        }
        return false;
    }
    
    getCongestionColor(congestion) {
        if (congestion >= 80) return '#ff0000';
        if (congestion >= 60) return '#ff9900';
        if (congestion >= 40) return '#ffff00';
        return '#00ff00';
    }
    
    getCongestionLevel(congestion) {
        if (congestion >= 80) return 'Severe';
        if (congestion >= 60) return 'Heavy';
        if (congestion >= 40) return 'Moderate';
        return 'Light';
    }
    
    getMarkerSize(congestion) {
        // Size from 20px to 40px based on congestion
        return 20 + (congestion / 100) * 20;
    }
    
    setupEventListeners() {
        // Map click event
        this.map.on('click', (e) => {
            this.onMapClick(e);
        });
        
        // Map move/zoom events
        this.map.on('moveend', () => {
            this.onMapMove();
        });
        
        this.map.on('zoomend', () => {
            this.onMapZoom();
        });
        
        // Key events
        document.addEventListener('keydown', (e) => {
            this.onKeyDown(e);
        });
    }
    
    onMapClick(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        
        // Show coordinates in console (in production, show in UI)
        console.log(`Map clicked at: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        
        // Open add marker dialog
        if (this.addMarkerMode) {
            this.addCustomMarker(lat, lng);
        }
    }
    
    onMapMove() {
        // Update any dynamic content based on viewport
        const bounds = this.map.getBounds();
        const center = this.map.getCenter();
        
        // Could trigger data reload for visible area
        console.log(`Map moved to: ${center.lat.toFixed(4)}, ${center.lng.toFixed(4)}`);
    }
    
    onMapZoom() {
        const zoom = this.map.getZoom();
        console.log(`Zoom level: ${zoom}`);
        
        // Adjust marker sizes or show/hide details based on zoom
        this.adjustMarkersForZoom(zoom);
    }
    
    onKeyDown(e) {
        // Add keyboard shortcuts
        switch(e.key) {
            case '+':
            case '=':
                this.map.zoomIn();
                break;
            case '-':
            case '_':
                this.map.zoomOut();
                break;
            case 'r':
                if (e.ctrlKey) {
                    this.refreshData();
                }
                break;
            case 'h':
                this.toggleLayer('heatmap');
                break;
            case 't':
                this.toggleLayer('traffic');
                break;
            case 's':
                this.toggleLayer('signals');
                break;
        }
    }
    
    adjustMarkersForZoom(zoom) {
        // In production, adjust marker sizes/styles based on zoom level
        // For now, just log the zoom level
        if (zoom < 10) {
            // Hide detailed markers, show clusters
            this.hideLayer('signals');
        } else {
            // Show all markers
            this.showLayer('signals');
        }
    }
    
    addCustomMarker(lat, lng, options = {}) {
        const marker = L.marker([lat, lng])
            .addTo(this.map)
            .bindPopup(options.popup || 'Custom Marker')
            .openPopup();
        
        this.markers.set(`custom_${Date.now()}`, marker);
        return marker;
    }
    
    async refreshData() {
        await this.loadTrafficData();
        this.showNotification('Map data refreshed', 'success');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `map-notification map-notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : 
                        type === 'error' ? '#dc3545' : 
                        '#007bff'};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
        
        // Add CSS for animations if not already present
        if (!document.getElementById('map-notification-animations')) {
            const style = document.createElement('style');
            style.id = 'map-notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // Public methods for external use
    viewLocationDetails(locationId) {
        console.log(`Viewing details for location ${locationId}`);
        // In production, open location details modal
        this.showNotification(`Opening details for location ${locationId}`, 'info');
    }
    
    controlSignal(signalId) {
        console.log(`Controlling signal ${signalId}`);
        // In production, open signal control modal
        window.location.href = `/traffic-control?signal=${signalId}`;
    }
    
    viewIncidentDetails(incidentId) {
        console.log(`Viewing incident ${incidentId}`);
        // In production, open incident details modal
        this.showNotification(`Opening incident ${incidentId} details`, 'warning');
    }
    
    enableAddMarkerMode() {
        this.addMarkerMode = true;
        this.showNotification('Click on map to add marker', 'info');
    }
    
    disableAddMarkerMode() {
        this.addMarkerMode = false;
        this.showNotification('Add marker mode disabled', 'info');
    }
    
    exportMapAsImage() {
        // Note: Leaflet doesn't have built-in export
        // In production, use html2canvas or similar library
        this.showNotification('Map export feature requires additional setup', 'info');
    }
    
    printMap() {
        window.print();
    }
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.trafficMap = new TrafficMap('traffic-map-container');
});

// Export for use in other files
window.TrafficMap = TrafficMap;