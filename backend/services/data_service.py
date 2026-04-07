import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class DataService:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.join(self.data_dir, 'raw'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'processed'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'reports'), exist_ok=True)
    
    def generate_sample_data(self, days=30):
        """Generate sample traffic data for simulation"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        
        data = []
        for date in dates:
            hour = date.hour
            day_of_week = date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Base congestion pattern
            if 7 <= hour <= 9:  # Morning peak
                base_congestion = 80
            elif 16 <= hour <= 18:  # Evening peak
                base_congestion = 85
            elif 12 <= hour <= 14:  # Lunch time
                base_congestion = 65
            elif hour >= 22 or hour <= 5:  # Night
                base_congestion = 30
            else:
                base_congestion = 55
            
            # Add day of week effect
            if day_of_week in [0, 4]:  # Monday and Friday are busier
                base_congestion += 10
            elif day_of_week in [5, 6]:  # Weekend
                base_congestion -= 15
            
            # Add random variation
            congestion = max(10, min(100, base_congestion + np.random.normal(0, 10)))
            
            # Generate other metrics
            vehicle_count = int(1000 * (congestion / 100) + np.random.normal(0, 100))
            avg_speed = max(5, 60 - (congestion / 100 * 40) + np.random.normal(0, 5))
            accidents = 1 if np.random.random() < 0.02 else 0
            
            data.append({
                'timestamp': date.isoformat(),
                'congestion': round(congestion, 1),
                'vehicle_count': max(0, vehicle_count),
                'avg_speed': round(avg_speed, 1),
                'accidents': accidents,
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'temperature': 20 + np.random.normal(0, 5),
                'precipitation': max(0, np.random.normal(0, 2)),
                'visibility': max(1, 10 + np.random.normal(0, 3))
            })
        
        df = pd.DataFrame(data)
        return df
    
    def save_data(self, df, filename):
        """Save data to CSV file"""
        filepath = os.path.join(self.data_dir, 'processed', filename)
        df.to_csv(filepath, index=False)
        return filepath
    
    def load_data(self, filename):
        """Load data from CSV file"""
        filepath = os.path.join(self.data_dir, 'processed', filename)
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        else:
            return self.generate_sample_data()
    
    def process_realtime_data(self, raw_data):
        """Process real-time data from sensors"""
        processed_data = {
            'timestamp': datetime.now().isoformat(),
            'location_id': raw_data.get('location_id'),
            'congestion': raw_data.get('congestion', 50),
            'vehicle_count': raw_data.get('vehicle_count', 0),
            'avg_speed': raw_data.get('speed', 30),
            'vehicle_types': raw_data.get('vehicle_types', {}),
            'weather': raw_data.get('weather', {}),
            'incidents': raw_data.get('incidents', []),
            'confidence': raw_data.get('confidence', 0.95)
        }
        
        # Add derived metrics
        processed_data['congestion_level'] = self.get_congestion_level(processed_data['congestion'])
        processed_data['traffic_flow'] = self.calculate_traffic_flow(
            processed_data['vehicle_count'],
            processed_data['avg_speed']
        )
        
        return processed_data
    
    def get_congestion_level(self, congestion):
        """Convert congestion percentage to level"""
        if congestion >= 80:
            return 'severe'
        elif congestion >= 60:
            return 'heavy'
        elif congestion >= 40:
            return 'moderate'
        else:
            return 'light'
    
    def calculate_traffic_flow(self, vehicle_count, avg_speed):
        """Calculate traffic flow (vehicles per hour)"""
        # Assuming data is for 5-minute intervals
        flow = vehicle_count * 12  # Convert to hourly rate
        return int(flow)
    
    def aggregate_hourly_data(self, data_points):
        """Aggregate minute-level data to hourly"""
        df = pd.DataFrame(data_points)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        hourly = df.resample('H').agg({
            'congestion': 'mean',
            'vehicle_count': 'sum',
            'avg_speed': 'mean',
            'accidents': 'sum'
        }).round(2)
        
        return hourly.reset_index()
    
    def generate_report_data(self, start_date, end_date):
        """Generate data for reports"""
        # Load or generate historical data
        df = self.load_data('historical_traffic.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date range
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        filtered_df = df.loc[mask].copy()
        
        if filtered_df.empty:
            return None
        
        # Calculate report metrics
        report_data = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'avg_congestion': filtered_df['congestion'].mean(),
                'total_vehicles': filtered_df['vehicle_count'].sum(),
                'total_accidents': filtered_df['accidents'].sum(),
                'avg_speed': filtered_df['avg_speed'].mean(),
                'peak_congestion': filtered_df['congestion'].max(),
                'peak_hour': self.find_peak_hour(filtered_df)
            },
            'daily_patterns': self.analyze_daily_patterns(filtered_df),
            'hourly_patterns': self.analyze_hourly_patterns(filtered_df),
            'weekly_patterns': self.analyze_weekly_patterns(filtered_df),
            'trends': self.analyze_trends(filtered_df),
            'recommendations': self.generate_recommendations(filtered_df)
        }
        
        return report_data
    
    def find_peak_hour(self, df):
        """Find peak congestion hour"""
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby('hour')['congestion'].mean()
        peak_hour = hourly_avg.idxmax()
        return f"{peak_hour:02d}:00"
    
    def analyze_daily_patterns(self, df):
        """Analyze daily traffic patterns"""
        df['date'] = df['timestamp'].dt.date
        daily = df.groupby('date').agg({
            'congestion': 'mean',
            'vehicle_count': 'sum',
            'accidents': 'sum'
        }).round(2)
        
        return daily.reset_index().to_dict('records')
    
    def analyze_hourly_patterns(self, df):
        """Analyze hourly traffic patterns"""
        df['hour'] = df['timestamp'].dt.hour
        hourly = df.groupby('hour').agg({
            'congestion': 'mean',
            'vehicle_count': 'mean',
            'accidents': 'mean'
        }).round(2)
        
        return hourly.reset_index().to_dict('records')
    
    def analyze_weekly_patterns(self, df):
        """Analyze weekly traffic patterns"""
        df['day_of_week'] = df['timestamp'].dt.day_name()
        weekly = df.groupby('day_of_week').agg({
            'congestion': 'mean',
            'vehicle_count': 'mean',
            'accidents': 'mean'
        }).round(2)
        
        return weekly.reset_index().to_dict('records')
    
    def analyze_trends(self, df):
        """Analyze traffic trends"""
        df['date'] = df['timestamp'].dt.date
        trends = df.groupby('date').agg({
            'congestion': 'mean',
            'vehicle_count': 'sum'
        }).round(2)
        
        # Calculate 7-day moving average
        trends['congestion_ma'] = trends['congestion'].rolling(window=7).mean()
        trends['vehicle_count_ma'] = trends['vehicle_count'].rolling(window=7).mean()
        
        return trends.reset_index().to_dict('records')
    
    def generate_recommendations(self, df):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        avg_congestion = df['congestion'].mean()
        peak_congestion = df['congestion'].max()
        
        if avg_congestion > 70:
            recommendations.append({
                'priority': 'high',
                'title': 'Implement Congestion Pricing',
                'description': f'Average congestion ({avg_congestion:.1f}%) exceeds optimal levels',
                'impact': 'Expected 15-20% reduction in congestion'
            })
        
        if peak_congestion > 85:
            recommendations.append({
                'priority': 'high',
                'title': 'Optimize Peak Hour Signals',
                'description': f'Peak congestion ({peak_congestion:.1f}%) causing significant delays',
                'impact': 'Expected 25-30% reduction in peak hour delays'
            })
        
        accident_rate = df['accidents'].sum() / len(df) * 100
        if accident_rate > 0.5:
            recommendations.append({
                'priority': 'medium',
                'title': 'Improve Road Safety Measures',
                'description': f'Accident rate ({accident_rate:.2f}%) higher than target',
                'impact': 'Expected 40% reduction in accidents'
            })
        
        # Always include general recommendations
        recommendations.extend([
            {
                'priority': 'low',
                'title': 'Promote Public Transport',
                'description': 'Increase public transport frequency during peak hours',
                'impact': 'Expected 5-10% reduction in private vehicles'
            },
            {
                'priority': 'medium',
                'title': 'Implement Smart Parking',
                'description': 'Dynamic parking pricing and availability tracking',
                'impact': 'Expected 15% reduction in circling traffic'
            }
        ])
        
        return recommendations