import json
import hashlib
from datetime import datetime, timedelta
import random
import string
from functools import wraps
from flask import request, jsonify

class Helpers:
    @staticmethod
    def generate_id(prefix=''):
        """Generate a unique ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}{timestamp}_{random_str}"
    
    @staticmethod
    def format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S'):
        """Format timestamp"""
        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return timestamp.strftime(format_str)
    
    @staticmethod
    def parse_time_range(time_range):
        """Parse time range string to datetime objects"""
        now = datetime.now()
        
        if time_range == '1h':
            start = now - timedelta(hours=1)
        elif time_range == '6h':
            start = now - timedelta(hours=6)
        elif time_range == '24h':
            start = now - timedelta(hours=24)
        elif time_range == '7d':
            start = now - timedelta(days=7)
        elif time_range == '30d':
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(hours=24)  # Default to 24 hours
        
        return start, now
    
    @staticmethod
    def calculate_percentage_change(old_value, new_value):
        """Calculate percentage change"""
        if old_value == 0:
            return 100 if new_value > 0 else 0
        
        return ((new_value - old_value) / abs(old_value)) * 100
    
    @staticmethod
    def get_color_for_value(value, min_val=0, max_val=100, reverse=False):
        """Get color for a value (gradient from green to red)"""
        # Normalize value between 0 and 1
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))
        
        if reverse:
            normalized = 1 - normalized
        
        # Green to Red gradient
        if normalized < 0.5:
            # Green to Yellow
            r = int(255 * (normalized * 2))
            g = 255
            b = 0
        else:
            # Yellow to Red
            r = 255
            g = int(255 * ((1 - normalized) * 2))
            b = 0
        
        return f'rgb({r}, {g}, {b})'
    
    @staticmethod
    def get_congestion_color(congestion):
        """Get color based on congestion level"""
        if congestion >= 80:
            return '#ff0000'  # Red
        elif congestion >= 60:
            return '#ff9900'  # Orange
        elif congestion >= 40:
            return '#ffff00'  # Yellow
        else:
            return '#00ff00'  # Green
    
    @staticmethod
    def format_number(number, decimals=1):
        """Format number with commas and decimal places"""
        if number is None:
            return '0'
        
        if abs(number) >= 1000000:
            return f"{number/1000000:.{decimals}f}M"
        elif abs(number) >= 1000:
            return f"{number/1000:.{decimals}f}K"
        else:
            return f"{number:.{decimals}f}"
    
    @staticmethod
    def validate_coordinates(lat, lng):
        """Validate latitude and longitude coordinates"""
        try:
            lat = float(lat)
            lng = float(lng)
            
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return True, (lat, lng)
            else:
                return False, "Coordinates out of valid range"
        except ValueError:
            return False, "Invalid coordinate format"
    
    @staticmethod
    def calculate_distance(lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates in kilometers"""
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        radius = 6371  # Earth's radius in km
        
        return radius * c
    
    @staticmethod
    def estimate_travel_time(distance_km, avg_speed_kph=40):
        """Estimate travel time in minutes"""
        if avg_speed_kph <= 0:
            return 0
        
        time_hours = distance_km / avg_speed_kph
        return time_hours * 60  # Convert to minutes
    
    @staticmethod
    def generate_route_hash(start, end, waypoints=None):
        """Generate hash for route"""
        route_str = f"{start}|{end}"
        
        if waypoints:
            route_str += f"|{','.join(waypoints)}"
        
        return hashlib.md5(route_str.encode()).hexdigest()[:8]
    
    @staticmethod
    def api_key_required(f):
        """Decorator for API key authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            # In production, validate against database
            if not api_key or api_key != 'dev-api-key-123':
                return jsonify({
                    'error': 'Valid API key required',
                    'status': 401
                }), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    @staticmethod
    def rate_limit(max_requests=100, window_minutes=1):
        """Simple rate limiting decorator"""
        requests = {}
        
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                ip = request.remote_addr
                now = datetime.now()
                window_start = now - timedelta(minutes=window_minutes)
                
                # Clean old requests
                if ip in requests:
                    requests[ip] = [req_time for req_time in requests[ip] 
                                   if req_time > window_start]
                
                # Check rate limit
                if ip in requests and len(requests[ip]) >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_minutes * 60
                    }), 429
                
                # Add current request
                if ip not in requests:
                    requests[ip] = []
                requests[ip].append(now)
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    @staticmethod
    def sanitize_input(input_str, max_length=1000):
        """Sanitize user input"""
        if not input_str:
            return ''
        
        # Remove potentially dangerous characters
        sanitized = ''.join(c for c in input_str if c.isprintable())
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def generate_report_filename(report_type, timestamp=None):
        """Generate filename for reports"""
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        safe_type = report_type.lower().replace(' ', '_')
        
        return f"traffic_report_{safe_type}_{date_str}.pdf"
    
    @staticmethod
    def calculate_co2_savings(vehicles_rerouted, avg_distance_km):
        """Calculate CO2 savings from traffic optimization"""
        # Average CO2 emissions per km for a car: 0.12 kg
        co2_per_km = 0.12
        
        total_distance = vehicles_rerouted * avg_distance_km
        co2_saved = total_distance * co2_per_km
        
        return co2_saved
    
    @staticmethod
    def calculate_fuel_savings(vehicles_rerouted, avg_distance_km, 
                              congestion_reduction_percent):
        """Calculate fuel savings from congestion reduction"""
        # Average fuel consumption: 8L/100km
        # Fuel wasted in congestion: 40% more
        base_consumption = 8  # L/100km
        congestion_waste = 0.4  # 40% extra fuel in congestion
        
        fuel_saved_per_vehicle = (avg_distance_km / 100) * base_consumption * \
                                congestion_waste * (congestion_reduction_percent / 100)
        
        total_fuel_saved = vehicles_rerouted * fuel_saved_per_vehicle
        
        return total_fuel_saved
    
    @staticmethod
    def get_traffic_trend_icon(trend_value):
        """Get icon for traffic trend"""
        if trend_value > 5:
            return '↗️'  # Rising sharply
        elif trend_value > 0:
            return '↗'   # Rising
        elif trend_value < -5:
            return '↘️'  # Falling sharply
        elif trend_value < 0:
            return '↘'   # Falling
        else:
            return '→'   # Stable