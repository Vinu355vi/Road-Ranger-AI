class TrafficDashboard {
    constructor() {
        this.init();
    }

    async init() {
        await this.loadTrafficData();
        this.setupEventListeners();
        this.updateDashboard();
        setInterval(() => this.updateDashboard(), 5000);
    }

    async loadTrafficData() {
        try {
            const response = await fetch('/api/traffic-data');
            this.trafficData = await response.json();
            this.updateUI();
        } catch (error) {
            console.error('Error loading traffic data:', error);
        }
    }

    updateUI() {
        this.updateStats();
        this.updateTrafficMap();
        this.updateSignalStatus();
    }

    updateStats() {
        const avgCongestionElement = document.getElementById('avg-congestion');
        if (!avgCongestionElement) return;

        const avgCongestion = this.calculateAverageCongestion();
        const totalSignals = this.trafficData.signals.length;
        const congestedSignals = this.trafficData.signals.filter(s => s.status === 'congested').length;
        
        avgCongestionElement.textContent = `${avgCongestion}%`;
        document.getElementById('total-signals').textContent = totalSignals;
        document.getElementById('congested-signals').textContent = congestedSignals;
        
        this.updateCongestionLevel(avgCongestion);
    }

    calculateAverageCongestion() {
        const sum = this.trafficData.locations.reduce((acc, loc) => acc + loc.congestion, 0);
        return Math.round(sum / this.trafficData.locations.length);
    }

    updateCongestionLevel(level) {
        const levelElement = document.getElementById('congestion-level');
        levelElement.textContent = level >= 70 ? 'High' : level >= 40 ? 'Medium' : 'Low';
        levelElement.className = `congestion-level ${level >= 70 ? 'high' : level >= 40 ? 'medium' : 'low'}`;
    }

    updateTrafficMap() {
        const mapContainer = document.getElementById('traffic-map');
        if (!mapContainer) return;

        // Clear existing markers
        mapContainer.innerHTML = '';
        
        // Create map visualization
        const mapCanvas = document.createElement('div');
        mapCanvas.className = 'map-canvas';
        mapContainer.appendChild(mapCanvas);

        if (!this.trafficData.locations || this.trafficData.locations.length === 0) return;

        // Find bounds
        const lats = this.trafficData.locations.map(l => l.lat);
        const lngs = this.trafficData.locations.map(l => l.lng);
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);
        const minLng = Math.min(...lngs);
        const maxLng = Math.max(...lngs);
        
        // Add padding to bounds (20% padding to prevent markers on edges)
        const latRange = maxLat - minLat || 0.01;
        const lngRange = maxLng - minLng || 0.01;
        const latPadding = latRange * 0.2;
        const lngPadding = lngRange * 0.2;
        
        const bounds = {
            minLat: minLat - latPadding,
            maxLat: maxLat + latPadding,
            minLng: minLng - lngPadding,
            maxLng: maxLng + lngPadding
        };
        
        // Create traffic markers
        this.trafficData.locations.forEach(location => {
            const marker = this.createTrafficMarker(location, bounds);
            mapContainer.appendChild(marker);
        });
    }

    createTrafficMarker(location, bounds) {
        const marker = document.createElement('div');
        marker.className = 'traffic-marker';
        
        // Calculate position as percentage within bounds
        // Invert Longitude for X (Standard)
        const lngPercent = ((location.lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * 100;
        
        // Invert Latitude for Y (Top is 0%, larger lat is higher up physically but lower screen coordinate if top=0)
        // If lat increases (moves north), typical Y screen coordinate decreases (moves up).
        // So: (maxLat - location.lat) / totalRange
        const latPercent = ((bounds.maxLat - location.lat) / (bounds.maxLat - bounds.minLat)) * 100;
        
        marker.style.left = `${lngPercent}%`;
        marker.style.top = `${latPercent}%`;
        
        const congestion = location.congestion;
        let color = '#4ade80'; // Green for low
        
        if (congestion >= 70) {
            color = '#ef4444'; // Red for high
        } else if (congestion >= 40) {
            color = '#f59e0b'; // Orange for medium
        }
        
        marker.innerHTML = `
            <div class="marker-circle" style="background: ${color}; box-shadow: 0 0 20px ${color}">
                <span>${congestion}%</span>
            </div>
            <div class="marker-label">${location.name}</div>
        `;
        
        return marker;
    }

    updateSignalStatus() {
        const signalsContainer = document.getElementById('signals-container');
        if (!signalsContainer) return;

        signalsContainer.innerHTML = this.trafficData.signals.map(signal => `
            <div class="signal-status">
                <div class="signal-dot ${signal.status}"></div>
                <div class="signal-info">
                    <div class="signal-name">${signal.location}</div>
                    <div class="signal-cycle">Cycle: ${signal.cycle_time}s</div>
                </div>
                <div class="signal-controls">
                    <button class="btn btn-sm" onclick="trafficDashboard.adjustSignal(${signal.id}, -10)">-10s</button>
                    <button class="btn btn-sm" onclick="trafficDashboard.adjustSignal(${signal.id}, 10)">+10s</button>
                </div>
            </div>
        `).join('');
    }

    async adjustSignal(signalId, adjustment) {
        try {
            const signal = this.trafficData.signals.find(s => s.id === signalId);
            const newCycleTime = signal.cycle_time + adjustment;
            
            const response = await fetch('/api/update-signal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    signal_id: signalId,
                    cycle_time: newCycleTime
                })
            });
            
            if (response.ok) {
                await this.loadTrafficData();
                this.showNotification('Signal timing updated successfully', 'success');
            }
        } catch (error) {
            console.error('Error adjusting signal:', error);
            this.showNotification('Failed to update signal', 'error');
        }
    }

    async predictCongestion() {
        const hours = document.getElementById('prediction-hours').value;
        
        try {
            const response = await fetch('/api/predict-congestion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ hours: parseInt(hours) })
            });
            
            const data = await response.json();
            this.displayPredictions(data);
        } catch (error) {
            console.error('Error predicting congestion:', error);
        }
    }

    displayPredictions(data) {
        const container = document.getElementById('prediction-results');
        container.innerHTML = `
            <div class="prediction-card">
                <h3>Prediction Results</h3>
                <div class="prediction-chart">
                    <canvas id="prediction-chart"></canvas>
                </div>
                <div class="prediction-info">
                    <div class="confidence">Confidence: ${data.confidence}%</div>
                    <div class="recommendation">Recommendation: ${data.recommendation}</div>
                </div>
            </div>
        `;
        
        this.createPredictionChart(data.predictions);
    }

    createPredictionChart(predictions) {
        const ctx = document.getElementById('prediction-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: predictions.map((_, i) => `T+${i + 1}h`),
                datasets: [{
                    label: 'Predicted Congestion (%)',
                    data: predictions,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    async optimizeRoute() {
        const start = document.getElementById('route-start').value;
        const end = document.getElementById('route-end').value;
        
        if (!start || !end) {
            this.showNotification('Please enter both start and end locations', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/optimize-route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start: this.parseLocation(start),
                    end: this.parseLocation(end)
                })
            });
            
            const data = await response.json();
            this.displayRoutes(data.routes);
        } catch (error) {
            console.error('Error optimizing route:', error);
        }
    }

    parseLocation(input) {
        // Simple location parsing - in real app, use geocoding service
        return {
            lat: 40.7128 + (Math.random() - 0.5) * 0.1,
            lng: -74.0060 + (Math.random() - 0.5) * 0.1
        };
    }

    displayRoutes(routes) {
        const container = document.getElementById('route-results');
        container.innerHTML = routes.map((route, index) => `
            <div class="route-card ${index === 0 ? 'best-route' : ''}">
                <div class="route-header">
                    <h4>${route.name}</h4>
                    ${index === 0 ? '<span class="badge best-badge">BEST</span>' : ''}
                </div>
                <div class="route-stats">
                    <div class="route-stat">
                        <span class="stat-label">Time:</span>
                        <span class="stat-value">${route.time}</span>
                    </div>
                    <div class="route-stat">
                        <span class="stat-label">Distance:</span>
                        <span class="stat-value">${route.distance}</span>
                    </div>
                    <div class="route-stat">
                        <span class="stat-label">Congestion:</span>
                        <span class="stat-value congestion-${route.congestion.toLowerCase()}">${route.congestion}</span>
                    </div>
                </div>
                <div class="route-steps">
                    <h5>Route Steps:</h5>
                    <ol>
                        ${route.steps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                </div>
                <button class="btn btn-primary" onclick="trafficDashboard.selectRoute(${index})">
                    Select This Route
                </button>
            </div>
        `).join('');
    }

    selectRoute(index) {
        this.showNotification(`Route ${index + 1} selected. Navigation started.`, 'success');
        // In real app, integrate with navigation system
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    updateDashboard() {
        this.loadTrafficData();
    }

    setupEventListeners() {
        // Prediction form
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.addEventListener('click', () => this.predictCongestion());
        }
        
        // Route optimization form
        const optimizeBtn = document.getElementById('optimize-btn');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.optimizeRoute());
        }
        
        // Real-time updates toggle
        const realtimeToggle = document.getElementById('realtime-toggle');
        if (realtimeToggle) {
            realtimeToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startRealTimeUpdates();
                } else {
                    this.stopRealTimeUpdates();
                }
            });
        }
    }

    startRealTimeUpdates() {
        this.realTimeInterval = setInterval(() => this.updateDashboard(), 2000);
    }

    stopRealTimeUpdates() {
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
        }
    }
}

// Initialize dashboard
const trafficDashboard = new TrafficDashboard();

// Export for use in HTML
window.trafficDashboard = trafficDashboard;