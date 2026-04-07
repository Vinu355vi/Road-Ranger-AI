/**
 * Charts.js - Traffic Data Visualization
 * Handles all chart rendering for the traffic prediction system
 */

class TrafficCharts {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = this.getChartConfigs();
    }
    
    getChartConfigs() {
        return {
            line: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4361ee',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#ffffff',
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.4
                    },
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    }
                }
            },
            bar: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            },
            pie: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };
    }
    
    createChart(canvasId, type, data, customOptions = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas with id ${canvasId} not found`);
            return null;
        }
        
        // Destroy existing chart if it exists
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }
        
        // Merge base config with custom options
        const baseConfig = this.chartConfigs[type] || this.chartConfigs.line;
        const options = this.deepMerge(baseConfig, customOptions);
        
        // Create new chart
        const chart = new Chart(canvas.getContext('2d'), {
            type: type,
            data: data,
            options: options
        });
        
        // Store reference
        this.charts.set(canvasId, chart);
        
        return chart;
    }
    
    deepMerge(target, source) {
        const output = Object.assign({}, target);
        
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        
        return output;
    }
    
    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
    
    destroyChart(canvasId) {
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
            this.charts.delete(canvasId);
        }
    }
    
    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
    
    // Specific chart creation methods
    createCongestionChart(canvasId, labels, datasets) {
        const data = {
            labels: labels,
            datasets: datasets.map((dataset, index) => ({
                label: dataset.label || `Dataset ${index + 1}`,
                data: dataset.data,
                borderColor: dataset.color || this.getColor(index),
                backgroundColor: this.addAlpha(dataset.color || this.getColor(index), 0.1),
                borderWidth: 2,
                fill: dataset.fill !== undefined ? dataset.fill : true
            }))
        };
        
        return this.createChart(canvasId, 'line', data);
    }
    
    createHourlyPatternChart(canvasId, hourlyData) {
        const labels = Array.from({length: 24}, (_, i) => `${i}:00`);
        
        const data = {
            labels: labels,
            datasets: [{
                label: 'Average Congestion (%)',
                data: hourlyData,
                borderColor: '#f72585',
                backgroundColor: 'rgba(247, 37, 133, 0.1)',
                borderWidth: 3,
                fill: true
            }]
        };
        
        const options = {
            plugins: {
                annotation: {
                    annotations: {
                        morningPeak: {
                            type: 'box',
                            xMin: 7,
                            xMax: 9,
                            backgroundColor: 'rgba(255, 193, 7, 0.2)',
                            borderColor: 'rgba(255, 193, 7, 0.5)',
                            borderWidth: 1,
                            label: {
                                display: true,
                                content: 'Morning Peak',
                                position: 'start',
                                color: '#ffc107'
                            }
                        },
                        eveningPeak: {
                            type: 'box',
                            xMin: 16,
                            xMax: 18,
                            backgroundColor: 'rgba(220, 53, 69, 0.2)',
                            borderColor: 'rgba(220, 53, 69, 0.5)',
                            borderWidth: 1,
                            label: {
                                display: true,
                                content: 'Evening Peak',
                                position: 'end',
                                color: '#dc3545'
                            }
                        }
                    }
                }
            }
        };
        
        return this.createChart(canvasId, 'line', data, options);
    }
    
    createDailyPatternChart(canvasId, dailyData) {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const colors = days.map((_, i) => {
            if (i === 0 || i === 4) return '#dc3545'; // Monday & Friday - red
            if (i === 5 || i === 6) return '#28a745'; // Weekend - green
            return '#4361ee'; // Other days - blue
        });
        
        const data = {
            labels: days,
            datasets: [{
                label: 'Average Congestion (%)',
                data: dailyData,
                backgroundColor: colors,
                borderColor: colors.map(c => this.adjustColor(c, -20)),
                borderWidth: 2
            }]
        };
        
        return this.createChart(canvasId, 'bar', data);
    }
    
    createSignalEfficiencyChart(canvasId, signals) {
        const data = {
            labels: signals.map(s => s.name),
            datasets: [{
                label: 'Efficiency (%)',
                data: signals.map(s => s.efficiency),
                backgroundColor: signals.map(s => 
                    s.efficiency >= 90 ? 'rgba(40, 167, 69, 0.8)' :
                    s.efficiency >= 75 ? 'rgba(255, 193, 7, 0.8)' :
                    'rgba(220, 53, 69, 0.8)'
                ),
                borderColor: signals.map(s => 
                    s.efficiency >= 90 ? '#28a745' :
                    s.efficiency >= 75 ? '#ffc107' :
                    '#dc3545'
                ),
                borderWidth: 1
            }]
        };
        
        const options = {
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        };
        
        return this.createChart(canvasId, 'bar', data, options);
    }
    
    createVehicleTypeChart(canvasId, vehicleData) {
        const data = {
            labels: vehicleData.labels,
            datasets: [{
                data: vehicleData.values,
                backgroundColor: [
                    'rgba(67, 97, 238, 0.8)',
                    'rgba(76, 201, 240, 0.8)',
                    'rgba(114, 9, 183, 0.8)',
                    'rgba(247, 37, 133, 0.8)',
                    'rgba(248, 150, 30, 0.8)'
                ],
                borderColor: [
                    '#4361ee',
                    '#4cc9f0',
                    '#7209b7',
                    '#f72585',
                    '#f8961e'
                ],
                borderWidth: 2
            }]
        };
        
        return this.createChart(canvasId, 'pie', data);
    }
    
    createPredictionComparisonChart(canvasId, actualData, predictedData) {
        const labels = actualData.map((_, i) => `T+${i + 1}h`);
        
        const data = {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Congestion',
                    data: actualData,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 3,
                    borderDash: [5, 5]
                },
                {
                    label: 'Predicted Congestion',
                    data: predictedData,
                    borderColor: '#f72585',
                    backgroundColor: 'rgba(247, 37, 133, 0.1)',
                    borderWidth: 3,
                    fill: true
                }
            ]
        };
        
        const options = {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label;
                            const value = context.parsed.y;
                            const diff = Math.abs(actualData[context.dataIndex] - predictedData[context.dataIndex]);
                            return `${label}: ${value}% (Diff: ${diff.toFixed(1)}%)`;
                        }
                    }
                }
            }
        };
        
        return this.createChart(canvasId, 'line', data, options);
    }
    
    createHeatmapChart(canvasId, hourlyData, dailyData) {
        // Create 24x7 heatmap data
        const data = {
            datasets: [{
                label: 'Congestion Heatmap',
                data: this.prepareHeatmapData(hourlyData, dailyData),
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex].v;
                    if (value >= 80) return '#ff0000';
                    if (value >= 60) return '#ff9900';
                    if (value >= 40) return '#ffff00';
                    return '#00ff00';
                },
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                hoverBackgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex].v;
                    return `rgba(${value * 2.55}, ${255 - value * 2.55}, 0, 0.8)`;
                }
            }]
        };
        
        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][context[0].raw.x];
                            const hour = `${context[0].raw.y}:00`;
                            return `${day} at ${hour}`;
                        },
                        label: function(context) {
                            return `Congestion: ${context.raw.v}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                    reverse: true,
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        };
        
        return this.createChart(canvasId, 'scatter', data, options);
    }
    
    prepareHeatmapData(hourlyData, dailyData) {
        const data = [];
        
        // Create 24x7 grid
        for (let hour = 0; hour < 24; hour++) {
            for (let day = 0; day < 7; day++) {
                // Base value from hourly pattern
                let value = hourlyData[hour] || 50;
                
                // Adjust based on day
                if (day === 0 || day === 4) { // Monday & Friday
                    value += 10;
                } else if (day === 5 || day === 6) { // Weekend
                    value -= 15;
                }
                
                // Add daily variation if available
                if (dailyData && dailyData[day]) {
                    value = (value + dailyData[day]) / 2;
                }
                
                // Add some randomness
                value += Math.random() * 10 - 5;
                value = Math.max(10, Math.min(100, value));
                
                data.push({
                    x: day,
                    y: hour,
                    v: Math.round(value)
                });
            }
        }
        
        return data;
    }
    
    createAnomalyChart(canvasId, timeSeries, anomalies) {
        const labels = timeSeries.map((_, i) => `Point ${i + 1}`);
        
        const data = {
            labels: labels,
            datasets: [
                {
                    label: 'Traffic Flow',
                    data: timeSeries,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    pointRadius: 0
                },
                {
                    label: 'Anomalies',
                    data: this.markAnomalies(timeSeries, anomalies),
                    borderColor: '#f72585',
                    backgroundColor: 'rgba(247, 37, 133, 0.3)',
                    borderWidth: 0,
                    pointRadius: 6,
                    pointBackgroundColor: '#f72585',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    showLine: false
                }
            ]
        };
        
        return this.createChart(canvasId, 'line', data);
    }
    
    markAnomalies(timeSeries, anomalies) {
        return timeSeries.map((value, index) => 
            anomalies.includes(index) ? value : null
        );
    }
    
    getColor(index) {
        const colors = [
            '#f72585', '#7209b7', '#3a0ca3', '#4361ee', '#4cc9f0',
            '#f8961e', '#f9c74f', '#90be6d', '#43aa8b', '#577590'
        ];
        return colors[index % colors.length];
    }
    
    addAlpha(color, alpha) {
        if (color.startsWith('rgb')) {
            return color.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
        } else if (color.startsWith('#')) {
            const r = parseInt(color.slice(1, 3), 16);
            const g = parseInt(color.slice(3, 5), 16);
            const b = parseInt(color.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        return color;
    }
    
    adjustColor(color, amount) {
        let usePound = false;
        
        if (color[0] === "#") {
            color = color.slice(1);
            usePound = true;
        }
        
        const num = parseInt(color, 16);
        let r = (num >> 16) + amount;
        let g = ((num >> 8) & 0x00FF) + amount;
        let b = (num & 0x0000FF) + amount;
        
        r = Math.min(Math.max(0, r), 255);
        g = Math.min(Math.max(0, g), 255);
        b = Math.min(Math.max(0, b), 255);
        
        return (usePound ? "#" : "") + 
               (b | (g << 8) | (r << 16)).toString(16).padStart(6, '0');
    }
    
    updateChartData(canvasId, newData) {
        if (!this.charts.has(canvasId)) {
            console.error(`Chart ${canvasId} not found`);
            return;
        }
        
        const chart = this.charts.get(canvasId);
        
        // Update data
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        
        if (newData.datasets) {
            chart.data.datasets = newData.datasets.map((dataset, index) => {
                if (chart.data.datasets[index]) {
                    return {
                        ...chart.data.datasets[index],
                        ...dataset
                    };
                }
                return dataset;
            });
        }
        
        chart.update();
    }
    
    resizeChart(canvasId) {
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).resize();
        }
    }
    
    resizeAllCharts() {
        this.charts.forEach(chart => chart.resize());
    }
    
    exportChartAsImage(canvasId, filename = 'chart') {
        if (!this.charts.has(canvasId)) {
            console.error(`Chart ${canvasId} not found`);
            return;
        }
        
        const chart = this.charts.get(canvasId);
        const image = chart.toBase64Image();
        
        // Create download link
        const link = document.createElement('a');
        link.href = image;
        link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Initialize charts manager
const trafficCharts = new TrafficCharts();

// Export for use in other files
window.trafficCharts = trafficCharts;