import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class TrafficService:
    def __init__(self):
        self.traffic_data = self.initialize_sample_data()
    
    def initialize_sample_data(self):
        """Initialize sample traffic data"""
        locations = [
            {
                'id': i + 1,
                'name': f"Location {i + 1}",
                'lat': 40.7128 + random.uniform(-0.1, 0.1),
                'lng': -74.0060 + random.uniform(-0.1, 0.1),
                'congestion': random.randint(20, 90),
                'avg_speed': random.randint(20, 60),
                'vehicle_count': random.randint(50, 500),
                'accidents': random.randint(0, 3)
            }
            for i in range(20)
        ]
        
        signals = [
            {
                'id': i + 1,
                'location': f"Intersection {i + 1}",
                'status': random.choice(['normal', 'congested', 'heavy']),
                'cycle_time': random.randint(90, 200),
                'efficiency': random.randint(70, 95)
            }
            for i in range(10)
        ]
        
        return {
            'locations': locations,
            'signals': signals,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_traffic_data(self):
        """Get current traffic data with simulated updates"""
        # Simulate real-time changes
        for location in self.traffic_data['locations']:
            change = random.randint(-5, 5)
            location['congestion'] = max(10, min(100, location['congestion'] + change))
            location['vehicle_count'] = max(0, location['vehicle_count'] + random.randint(-20, 20))
            location['avg_speed'] = max(5, location['avg_speed'] + random.randint(-5, 5))
        
        for signal in self.traffic_data['signals']:
            if signal['status'] == 'congested':
                signal['cycle_time'] = random.randint(160, 220)
            elif signal['status'] == 'heavy':
                signal['cycle_time'] = random.randint(140, 180)
            else:
                signal['cycle_time'] = random.randint(90, 130)
            
            # Randomly change status
            if random.random() < 0.1:  # 10% chance to change status
                signal['status'] = random.choice(['normal', 'congested', 'heavy'])
        
        self.traffic_data['last_updated'] = datetime.now().isoformat()
        return self.traffic_data
    
    def get_historical_data(self, hours=24):
        """Generate historical traffic data"""
        timestamps = [(datetime.now() - timedelta(hours=i)).strftime('%H:%M') for i in range(hours, -1, -1)]
        
        data = {
            'timestamps': timestamps,
            'congestion': [random.randint(30, 90) for _ in range(hours + 1)],
            'accidents': [random.randint(0, 5) for _ in range(hours + 1)],
            'avg_speed': [random.randint(20, 60) for _ in range(hours + 1)],
            'vehicle_count': [random.randint(100, 800) for _ in range(hours + 1)]
        }
        
        return data
    
    def update_signal(self, signal_id, cycle_time):
        """Update traffic signal timing"""
        for signal in self.traffic_data['signals']:
            if signal['id'] == signal_id:
                signal['cycle_time'] = cycle_time
                
                # Update status based on cycle time
                if cycle_time > 180:
                    signal['status'] = 'congested'
                elif cycle_time > 150:
                    signal['status'] = 'heavy'
                else:
                    signal['status'] = 'normal'
                
                signal['last_updated'] = datetime.now().isoformat()
                return True
        
        return False
    
    def get_congestion_heatmap(self):
        """Generate congestion heatmap data"""
        heatmap_data = []
        
        for location in self.traffic_data['locations']:
            heatmap_data.append({
                'lat': location['lat'],
                'lng': location['lng'],
                'weight': location['congestion'] / 100,
                'congestion': location['congestion']
            })
        
        return heatmap_data
    
    def get_alerts(self):
        """Get traffic alerts"""
        alerts = []
        
        # Check for high congestion
        for location in self.traffic_data['locations']:
            if location['congestion'] > 80:
                alerts.append({
                    'type': 'danger',
                    'message': f"High congestion at {location['name']} ({location['congestion']}%)",
                    'location': location['name'],
                    'time': datetime.now().strftime('%H:%M'),
                    'priority': 'high'
                })
        
        # Check for accidents
        for location in self.traffic_data['locations']:
            if location['accidents'] > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f"{location['accidents']} accident(s) reported at {location['name']}",
                    'location': location['name'],
                    'time': datetime.now().strftime('%H:%M'),
                    'priority': 'medium'
                })
        
        # Check for inefficient signals
        for signal in self.traffic_data['signals']:
            if signal['efficiency'] < 75:
                alerts.append({
                    'type': 'info',
                    'message': f"Low efficiency at {signal['location']} ({signal['efficiency']}%)",
                    'location': signal['location'],
                    'time': datetime.now().strftime('%H:%M'),
                    'priority': 'low'
                })
        
        return alerts
    
    def get_statistics(self):
        """Get traffic statistics"""
        locations = self.traffic_data['locations']
        signals = self.traffic_data['signals']
        
        total_congestion = sum(loc['congestion'] for loc in locations)
        avg_congestion = total_congestion / len(locations)
        
        total_vehicles = sum(loc['vehicle_count'] for loc in locations)
        total_accidents = sum(loc['accidents'] for loc in locations)
        
        congested_signals = sum(1 for signal in signals if signal['status'] == 'congested')
        avg_signal_efficiency = sum(signal['efficiency'] for signal in signals) / len(signals)
        
        return {
            'avg_congestion': round(avg_congestion, 1),
            'total_vehicles': total_vehicles,
            'total_accidents': total_accidents,
            'congested_signals': congested_signals,
            'avg_signal_efficiency': round(avg_signal_efficiency, 1),
            'locations_monitored': len(locations),
            'signals_controlled': len(signals)
        }