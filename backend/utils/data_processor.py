import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """Advanced data processing for traffic prediction system"""
    
    def __init__(self):
        self.scaler_params = {}
        self.feature_stats = {}
        self.imputation_values = {}
        
    def process_real_time_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time traffic sensor data"""
        processed = {
            'timestamp': datetime.now().isoformat(),
            'location_id': raw_data.get('location_id', 'unknown'),
            'sensor_type': raw_data.get('sensor_type', 'unknown'),
            'raw_measurements': raw_data
        }
        
        # Process vehicle counts
        if 'vehicle_counts' in raw_data:
            processed.update(self._process_vehicle_counts(raw_data['vehicle_counts']))
        
        # Process speed data
        if 'speed_measurements' in raw_data:
            processed.update(self._process_speed_data(raw_data['speed_measurements']))
        
        # Process congestion data
        if 'congestion_indicators' in raw_data:
            processed.update(self._process_congestion_data(raw_data['congestion_indicators']))
        
        # Process incident data
        if 'incident_reports' in raw_data:
            processed.update(self._process_incident_data(raw_data['incident_reports']))
        
        # Calculate derived metrics
        processed.update(self._calculate_derived_metrics(processed))
        
        # Add data quality indicators
        processed.update(self._assess_data_quality(processed))
        
        return processed
    
    def process_historical_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process historical traffic data"""
        if not raw_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Convert timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Detect and handle outliers
        df = self._handle_outliers(df)
        
        # Feature engineering
        df = self._engineer_features(df)
        
        # Normalize data
        df = self._normalize_data(df)
        
        return df
    
    def prepare_training_data(self, historical_data: pd.DataFrame, 
                            target_column: str = 'congestion',
                            forecast_horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for model training"""
        if historical_data.empty:
            return pd.DataFrame(), pd.Series()
        
        # Create lag features
        df_lagged = self._create_lag_features(historical_data, target_column, forecast_horizon)
        
        # Create rolling statistics
        df_rolling = self._create_rolling_features(df_lagged, target_column)
        
        # Create time-based features
        df_time = self._create_time_features(df_rolling)
        
        # Create interaction features
        df_interactions = self._create_interaction_features(df_time)
        
        # Prepare target variable
        X = df_interactions.drop(columns=[target_column], errors='ignore')
        y = df_interactions[target_column].shift(-forecast_horizon).dropna()
        X = X.iloc[:-forecast_horizon]
        
        # Ensure alignment
        X = X.iloc[:len(y)]
        y = y.iloc[:len(X)]
        
        return X, y
    
    def process_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process weather data for traffic prediction"""
        processed = {
            'timestamp': datetime.now().isoformat(),
            'temperature_c': weather_data.get('temperature', 20),
            'precipitation_mm': weather_data.get('precipitation', 0),
            'humidity_percent': weather_data.get('humidity', 50),
            'wind_speed_kmh': weather_data.get('wind_speed', 10),
            'visibility_km': weather_data.get('visibility', 10),
            'weather_condition': weather_data.get('condition', 'clear'),
            'pressure_hpa': weather_data.get('pressure', 1013)
        }
        
        # Calculate weather impact scores
        processed.update(self._calculate_weather_impact(processed))
        
        # Generate weather alerts
        processed['alerts'] = self._generate_weather_alerts(processed)
        
        return processed
    
    def process_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process event data for traffic impact prediction"""
        processed = {
            'event_id': event_data.get('id', 'unknown'),
            'event_name': event_data.get('name', 'Unknown Event'),
            'event_type': event_data.get('type', 'other'),
            'start_time': event_data.get('start_time'),
            'end_time': event_data.get('end_time'),
            'location': event_data.get('location', {}),
            'expected_attendance': event_data.get('attendance', 0),
            'description': event_data.get('description', '')
        }
        
        # Calculate traffic impact metrics
        processed.update(self._calculate_event_impact(processed))
        
        # Generate event recommendations
        processed['recommendations'] = self._generate_event_recommendations(processed)
        
        return processed
    
    def aggregate_data(self, data_points: List[Dict[str, Any]], 
                      aggregation_level: str = 'hourly') -> pd.DataFrame:
        """Aggregate data at different time levels"""
        if not data_points:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_points)
        
        if 'timestamp' not in df.columns:
            return df
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        if aggregation_level == 'minutely':
            resampled = df.resample('1min')
        elif aggregation_level == '5min':
            resampled = df.resample('5min')
        elif aggregation_level == '15min':
            resampled = df.resample('15min')
        elif aggregation_level == 'hourly':
            resampled = df.resample('1H')
        elif aggregation_level == 'daily':
            resampled = df.resample('1D')
        else:
            resampled = df.resample('1H')
        
        # Define aggregation rules for different columns
        aggregation_rules = {}
        for col in df.columns:
            if col in ['congestion', 'avg_speed', 'temperature']:
                aggregation_rules[col] = 'mean'
            elif col in ['vehicle_count', 'accident_count']:
                aggregation_rules[col] = 'sum'
            elif col in ['location_id', 'sensor_type']:
                aggregation_rules[col] = 'first'
            else:
                aggregation_rules[col] = 'mean'
        
        aggregated = resampled.agg(aggregation_rules)
        return aggregated.reset_index()
    
    def detect_anomalies(self, data: pd.DataFrame, 
                        method: str = 'statistical',
                        sensitivity: float = 3.0) -> Dict[str, Any]:
        """Detect anomalies in traffic data"""
        if data.empty:
            return {'anomalies': [], 'anomaly_scores': {}}
        
        anomalies = {}
        
        if method == 'statistical':
            anomalies = self._statistical_anomaly_detection(data, sensitivity)
        elif method == 'machine_learning':
            anomalies = self._ml_anomaly_detection(data)
        elif method == 'seasonal':
            anomalies = self._seasonal_anomaly_detection(data)
        
        # Add anomaly explanations
        anomalies['explanations'] = self._explain_anomalies(anomalies.get('anomalies', []))
        
        return anomalies
    
    def calculate_traffic_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive traffic metrics"""
        if data.empty:
            return {}
        
        metrics = {}
        
        # Basic metrics
        if 'congestion' in data.columns:
            metrics['congestion'] = self._calculate_congestion_metrics(data['congestion'])
        
        if 'vehicle_count' in data.columns:
            metrics['volume'] = self._calculate_volume_metrics(data['vehicle_count'])
        
        if 'avg_speed' in data.columns:
            metrics['speed'] = self._calculate_speed_metrics(data['avg_speed'])
        
        if 'accident_count' in data.columns:
            metrics['safety'] = self._calculate_safety_metrics(data['accident_count'])
        
        # Derived metrics
        if all(col in data.columns for col in ['vehicle_count', 'avg_speed']):
            metrics['flow'] = self._calculate_flow_metrics(
                data['vehicle_count'], data['avg_speed']
            )
        
        # Performance metrics
        metrics['performance'] = self._calculate_performance_metrics(metrics)
        
        return metrics
    
    def _process_vehicle_counts(self, counts: Dict[str, Any]) -> Dict[str, Any]:
        """Process vehicle count data"""
        processed = {
            'total_vehicles': counts.get('total', 0),
            'vehicle_categories': {}
        }
        
        # Process by vehicle type
        if 'by_type' in counts:
            for vehicle_type, count in counts['by_type'].items():
                processed['vehicle_categories'][vehicle_type] = {
                    'count': count,
                    'percentage': (count / processed['total_vehicles'] * 100) 
                                  if processed['total_vehicles'] > 0 else 0
                }
        
        # Process by lane
        if 'by_lane' in counts:
            processed['lane_distribution'] = counts['by_lane']
        
        return processed
    
    def _process_speed_data(self, speed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process speed measurement data"""
        processed = {
            'avg_speed': speed_data.get('average', 0),
            'speed_distribution': {}
        }
        
        # Calculate speed percentiles
        if 'measurements' in speed_data:
            measurements = speed_data['measurements']
            if measurements:
                processed['speed_distribution'] = {
                    'p10': np.percentile(measurements, 10),
                    'p25': np.percentile(measurements, 25),
                    'p50': np.percentile(measurements, 50),
                    'p75': np.percentile(measurements, 75),
                    'p90': np.percentile(measurements, 90),
                    'std': np.std(measurements),
                    'cv': (np.std(measurements) / np.mean(measurements)) 
                          if np.mean(measurements) > 0 else 0
                }
        
        return processed
    
    def _process_congestion_data(self, congestion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process congestion indicator data"""
        processed = {
            'congestion_level': congestion_data.get('level', 'unknown'),
            'congestion_score': congestion_data.get('score', 0)
        }
        
        # Calculate congestion index
        if 'indicators' in congestion_data:
            indicators = congestion_data['indicators']
            if indicators:
                processed['congestion_index'] = self._calculate_congestion_index(indicators)
        
        return processed
    
    def _process_incident_data(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incident report data"""
        processed = {
            'incident_count': len(incident_data.get('reports', [])),
            'incidents': []
        }
        
        for incident in incident_data.get('reports', []):
            processed_incident = {
                'type': incident.get('type', 'unknown'),
                'severity': incident.get('severity', 'low'),
                'location': incident.get('location', {}),
                'timestamp': incident.get('timestamp'),
                'description': incident.get('description', ''),
                'status': incident.get('status', 'active'),
                'impact_score': self._calculate_incident_impact(incident)
            }
            processed['incidents'].append(processed_incident)
        
        return processed
    
    def _calculate_derived_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived traffic metrics"""
        derived = {}
        
        # Traffic density
        if 'total_vehicles' in data and 'road_length' in data.get('raw_measurements', {}):
            road_length = data['raw_measurements']['road_length']
            if road_length > 0:
                derived['traffic_density'] = data['total_vehicles'] / road_length
        
        # Level of Service (LOS)
        if 'avg_speed' in data:
            derived['level_of_service'] = self._calculate_level_of_service(data['avg_speed'])
        
        # Travel Time Index
        if 'avg_speed' in data:
            free_flow_speed = 60  # km/h
            derived['travel_time_index'] = free_flow_speed / max(1, data['avg_speed'])
        
        # Congestion delay
        if 'avg_speed' in data:
            derived['congestion_delay'] = max(0, (60 / max(1, data['avg_speed'])) - 1)
        
        # Environmental impact
        if 'total_vehicles' in data and 'avg_speed' in data:
            derived['estimated_co2'] = self._estimate_co2_emissions(
                data['total_vehicles'], data['avg_speed']
            )
        
        return derived
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data quality"""
        quality = {
            'completeness_score': 0,
            'accuracy_score': 0,
            'timeliness_score': 0,
            'consistency_score': 0,
            'overall_quality': 'unknown'
        }
        
        # Calculate completeness
        required_fields = ['total_vehicles', 'avg_speed', 'congestion_score']
        present_fields = [field for field in required_fields if field in data]
        quality['completeness_score'] = len(present_fields) / len(required_fields) * 100
        
        # Calculate accuracy (simplified)
        if 'avg_speed' in data:
            if 0 <= data['avg_speed'] <= 120:
                quality['accuracy_score'] = 90
            else:
                quality['accuracy_score'] = 50
        
        # Calculate timeliness
        if 'timestamp' in data:
            data_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            age_minutes = (datetime.now() - data_time).total_seconds() / 60
            
            if age_minutes < 5:
                quality['timeliness_score'] = 100
            elif age_minutes < 15:
                quality['timeliness_score'] = 80
            elif age_minutes < 60:
                quality['timeliness_score'] = 60
            else:
                quality['timeliness_score'] = 40
        
        # Calculate overall quality
        avg_score = np.mean([
            quality['completeness_score'],
            quality['accuracy_score'],
            quality['timeliness_score']
        ])
        
        if avg_score >= 90:
            quality['overall_quality'] = 'excellent'
        elif avg_score >= 75:
            quality['overall_quality'] = 'good'
        elif avg_score >= 60:
            quality['overall_quality'] = 'fair'
        else:
            quality['overall_quality'] = 'poor'
        
        quality['quality_score'] = avg_score
        
        return quality
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in DataFrame"""
        if df.empty:
            return df
        
        # Store imputation values for future use
        for column in df.select_dtypes(include=[np.number]).columns:
            if column not in self.imputation_values:
                self.imputation_values[column] = {
                    'mean': df[column].mean(),
                    'median': df[column].median(),
                    'mode': df[column].mode()[0] if not df[column].mode().empty else 0
                }
        
        # Impute missing values
        for column in df.columns:
            if df[column].isnull().any():
                if column in self.imputation_values:
                    # Use median for numerical columns
                    df[column] = df[column].fillna(self.imputation_values[column]['median'])
                else:
                    # Use forward fill then backward fill
                    df[column] = df[column].fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame, 
                        method: str = 'iqr') -> pd.DataFrame:
        """Detect and handle outliers"""
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        for column in df.select_dtypes(include=[np.number]).columns:
            if method == 'iqr':
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Cap outliers instead of removing
                df_clean[column] = df[column].clip(lower_bound, upper_bound)
            
            elif method == 'zscore':
                z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                df_clean[column] = np.where(
                    z_scores > 3,
                    df[column].median(),
                    df[column]
                )
        
        return df_clean
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw data"""
        if df.empty:
            return df
        
        df_features = df.copy()
        
        # Time-based features
        if 'timestamp' in df_features.columns:
            df_features['hour'] = df_features['timestamp'].dt.hour
            df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
            df_features['day_of_month'] = df_features['timestamp'].dt.day
            df_features['month'] = df_features['timestamp'].dt.month
            df_features['is_weekend'] = df_features['day_of_week'].isin([5, 6]).astype(int)
            
            # Time of day categories
            df_features['time_of_day'] = pd.cut(
                df_features['hour'],
                bins=[-1, 5, 9, 16, 20, 23],
                labels=['night', 'morning_peak', 'day', 'evening_peak', 'night_late']
            )
            
            # Is it rush hour?
            df_features['is_rush_hour'] = (
                ((df_features['hour'] >= 7) & (df_features['hour'] <= 9)) |
                ((df_features['hour'] >= 16) & (df_features['hour'] <= 18))
            ).astype(int)
        
        # Traffic flow features
        if all(col in df_features.columns for col in ['vehicle_count', 'avg_speed']):
            df_features['traffic_flow'] = df_features['vehicle_count'] * df_features['avg_speed'] / 1000
            df_features['density'] = df_features['vehicle_count'] / max(1, df_features['avg_speed'])
        
        # Congestion features
        if 'congestion' in df_features.columns:
            df_features['congestion_category'] = pd.cut(
                df_features['congestion'],
                bins=[-1, 30, 50, 70, 85, 101],
                labels=['free', 'light', 'moderate', 'heavy', 'severe']
            )
        
        # Lag features
        if 'congestion' in df_features.columns:
            for lag in [1, 2, 3, 4, 5, 6, 12, 24]:
                df_features[f'congestion_lag_{lag}'] = df_features['congestion'].shift(lag)
        
        # Rolling statistics
        if 'congestion' in df_features.columns:
            for window in [3, 6, 12, 24]:
                df_features[f'congestion_ma_{window}'] = (
                    df_features['congestion'].rolling(window=window).mean()
                )
                df_features[f'congestion_std_{window}'] = (
                    df_features['congestion'].rolling(window=window).std()
                )
        
        return df_features
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize data for modeling"""
        if df.empty:
            return df
        
        df_normalized = df.copy()
        
        # Normalize numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numerical_cols:
            if col not in self.scaler_params:
                self.scaler_params[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std()
                }
            
            # Skip if std is 0
            if self.scaler_params[col]['std'] > 0:
                df_normalized[col] = (
                    df[col] - self.scaler_params[col]['mean']
                ) / self.scaler_params[col]['std']
        
        return df_normalized
    
    def _create_lag_features(self, df: pd.DataFrame, target_column: str, 
                           forecast_horizon: int) -> pd.DataFrame:
        """Create lag features for time series"""
        df_lagged = df.copy()
        
        # Create lags for target variable
        for lag in range(1, forecast_horizon + 6):  # Extra lags for features
            df_lagged[f'{target_column}_lag_{lag}'] = df_lagged[target_column].shift(lag)
        
        # Create lags for other important features
        other_features = ['vehicle_count', 'avg_speed', 'accident_count']
        for feature in other_features:
            if feature in df.columns:
                for lag in [1, 2, 3]:
                    df_lagged[f'{feature}_lag_{lag}'] = df_lagged[feature].shift(lag)
        
        return df_lagged
    
    def _create_rolling_features(self, df: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """Create rolling window features"""
        df_rolling = df.copy()
        
        windows = [3, 6, 12, 24]
        
        for window in windows:
            # Rolling mean and std
            df_rolling[f'{target_column}_rolling_mean_{window}'] = (
                df_rolling[target_column].rolling(window=window).mean()
            )
            df_rolling[f'{target_column}_rolling_std_{window}'] = (
                df_rolling[target_column].rolling(window=window).std()
            )
            
            # Rolling min and max
            df_rolling[f'{target_column}_rolling_min_{window}'] = (
                df_rolling[target_column].rolling(window=window).min()
            )
            df_rolling[f'{target_column}_rolling_max_{window}'] = (
                df_rolling[target_column].rolling(window=window).max()
            )
        
        return df_rolling
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features"""
        df_time = df.copy()
        
        if 'timestamp' in df_time.columns:
            # Cyclical encoding for hour and day_of_week
            df_time['hour_sin'] = np.sin(2 * np.pi * df_time['hour'] / 24)
            df_time['hour_cos'] = np.cos(2 * np.pi * df_time['hour'] / 24)
            
            df_time['day_sin'] = np.sin(2 * np.pi * df_time['day_of_week'] / 7)
            df_time['day_cos'] = np.cos(2 * np.pi * df_time['day_of_week'] / 7)
            
            df_time['month_sin'] = np.sin(2 * np.pi * df_time['month'] / 12)
            df_time['month_cos'] = np.cos(2 * np.pi * df_time['month'] / 12)
        
        return df_time
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features"""
        df_interactions = df.copy()
        
        # Interaction between congestion and time
        if all(col in df.columns for col in ['congestion', 'hour']):
            df_interactions['congestion_hour_interaction'] = df['congestion'] * df['hour'] / 24
        
        # Interaction between volume and speed
        if all(col in df.columns for col in ['vehicle_count', 'avg_speed']):
            df_interactions['volume_speed_interaction'] = (
                df['vehicle_count'] * df['avg_speed'] / 1000
            )
        
        # Quadratic terms
        if 'congestion' in df.columns:
            df_interactions['congestion_squared'] = df['congestion'] ** 2
        
        if 'vehicle_count' in df.columns:
            df_interactions['vehicle_count_squared'] = df['vehicle_count'] ** 2
        
        return df_interactions
    
    def _calculate_congestion_index(self, indicators: List[float]) -> float:
        """Calculate comprehensive congestion index"""
        if not indicators:
            return 0
        
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Weight for each indicator
        weighted_sum = sum(w * i for w, i in zip(weights, indicators[:len(weights)]))
        
        return min(100, weighted_sum * 100)
    
    def _calculate_incident_impact(self, incident: Dict[str, Any]) -> float:
        """Calculate impact score for an incident"""
        impact = 0
        
        # Severity impact
        severity_weights = {
            'low': 1,
            'medium': 3,
            'high': 5,
            'critical': 10
        }
        impact += severity_weights.get(incident.get('severity', 'low'), 1)
        
        # Type impact
        type_weights = {
            'accident': 5,
            'breakdown': 2,
            'roadwork': 3,
            'weather': 4,
            'event': 3
        }
        impact += type_weights.get(incident.get('type', 'other'), 1)
        
        # Location impact (main road vs side road)
        if incident.get('location', {}).get('is_main_road', False):
            impact *= 2
        
        return min(10, impact)
    
    def _calculate_level_of_service(self, speed: float) -> str:
        """Calculate Level of Service (LOS) based on speed"""
        if speed >= 80:
            return 'A'  # Free flow
        elif speed >= 65:
            return 'B'  # Reasonably free flow
        elif speed >= 50:
            return 'C'  # Stable flow
        elif speed >= 40:
            return 'D'  # Approaching unstable flow
        elif speed >= 30:
            return 'E'  # Unstable flow
        else:
            return 'F'  # Forced flow
    
    def _estimate_co2_emissions(self, vehicle_count: int, avg_speed: float) -> float:
        """Estimate CO2 emissions in kg"""
        # Average CO2 per km per vehicle: 0.12 kg
        # Assuming average trip length: 10 km
        co2_per_vehicle_km = 0.12
        avg_trip_length = 10
        
        total_distance = vehicle_count * avg_trip_length
        total_co2 = total_distance * co2_per_vehicle_km
        
        # Adjust for speed (lower speed = higher emissions)
        if avg_speed < 20:
            total_co2 *= 1.5  # 50% more emissions in heavy traffic
        elif avg_speed < 40:
            total_co2 *= 1.2  # 20% more emissions in moderate traffic
        
        return total_co2
    
    def _calculate_weather_impact(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weather impact on traffic"""
        impact = {
            'traffic_impact_score': 0,
            'speed_reduction_percent': 0,
            'accident_risk_increase': 0,
            'visibility_impact': 'none'
        }
        
        # Precipitation impact
        precipitation = weather_data.get('precipitation_mm', 0)
        if precipitation > 10:
            impact['traffic_impact_score'] += 8
            impact['speed_reduction_percent'] += 30
            impact['accident_risk_increase'] += 4
        elif precipitation > 5:
            impact['traffic_impact_score'] += 5
            impact['speed_reduction_percent'] += 20
            impact['accident_risk_increase'] += 2
        elif precipitation > 0:
            impact['traffic_impact_score'] += 2
            impact['speed_reduction_percent'] += 10
            impact['accident_risk_increase'] += 1
        
        # Visibility impact
        visibility = weather_data.get('visibility_km', 10)
        if visibility < 1:
            impact['traffic_impact_score'] += 10
            impact['speed_reduction_percent'] += 50
            impact['accident_risk_increase'] += 5
            impact['visibility_impact'] = 'severe'
        elif visibility < 3:
            impact['traffic_impact_score'] += 6
            impact['speed_reduction_percent'] += 30
            impact['accident_risk_increase'] += 3
            impact['visibility_impact'] = 'moderate'
        elif visibility < 5:
            impact['traffic_impact_score'] += 3
            impact['speed_reduction_percent'] += 15
            impact['accident_risk_increase'] += 2
            impact['visibility_impact'] = 'light'
        
        # Wind impact
        wind_speed = weather_data.get('wind_speed_kmh', 10)
        if wind_speed > 50:
            impact['traffic_impact_score'] += 5
            impact['speed_reduction_percent'] += 20
        
        return impact
    
    def _generate_weather_alerts(self, weather_data: Dict[str, Any]) -> List[str]:
        """Generate weather alerts for traffic management"""
        alerts = []
        
        precipitation = weather_data.get('precipitation_mm', 0)
        visibility = weather_data.get('visibility_km', 10)
        wind_speed = weather_data.get('wind_speed_kmh', 10)
        
        if precipitation > 20:
            alerts.append('Heavy rain alert - Reduce speed limits')
        elif precipitation > 10:
            alerts.append('Rain alert - Increase monitoring')
        
        if visibility < 1:
            alerts.append('Dense fog alert - Activate fog protocols')
        elif visibility < 3:
            alerts.append('Reduced visibility - Use caution')
        
        if wind_speed > 60:
            alerts.append('High wind alert - Monitor high-profile vehicles')
        
        return alerts
    
    def _calculate_event_impact(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate traffic impact of an event"""
        attendance = event_data.get('expected_attendance', 0)
        event_type = event_data.get('event_type', 'other')
        
        impact = {
            'additional_vehicles': int(attendance * 0.3),  # 30% by car
            'congestion_increase_percent': 0,
            'parking_demand': int(attendance * 0.25),  # 25% need parking
            'public_transport_demand': int(attendance * 0.4)  # 40% by public transport
        }
        
        # Event type adjustments
        type_multipliers = {
            'sports': 1.5,
            'concert': 1.3,
            'festival': 1.4,
            'conference': 1.1,
            'protest': 2.0
        }
        
        multiplier = type_multipliers.get(event_type, 1.0)
        impact['additional_vehicles'] = int(impact['additional_vehicles'] * multiplier)
        
        # Calculate congestion increase
        base_vehicles = 1000  # Base traffic
        total_vehicles = base_vehicles + impact['additional_vehicles']
        impact['congestion_increase_percent'] = (
            (total_vehicles / base_vehicles - 1) * 100 * multiplier
        )
        
        return impact
    
    def _generate_event_recommendations(self, event_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for event traffic management"""
        attendance = event_data.get('expected_attendance', 0)
        event_type = event_data.get('event_type', 'other')
        
        recommendations = []
        
        if attendance > 10000:
            recommendations.extend([
                'Implement comprehensive traffic management plan',
                'Set up temporary parking areas',
                'Increase public transport frequency',
                'Deploy traffic control personnel'
            ])
        elif attendance > 5000:
            recommendations.extend([
                'Monitor key approach routes',
                'Coordinate with event organizers',
                'Prepare temporary signage',
                'Alert nearby residents'
            ])
        else:
            recommendations.extend([
                'Monitor traffic conditions',
                'Prepare for increased activity',
                'Coordinate with local authorities'
            ])
        
        # Event type specific recommendations
        if event_type == 'sports':
            recommendations.append('Prepare for post-event traffic surge')
        elif event_type == 'concert':
            recommendations.append('Manage queueing traffic at venue entrance')
        elif event_type == 'protest':
            recommendations.append('Prepare for possible road closures')
        
        return recommendations
    
    def _statistical_anomaly_detection(self, df: pd.DataFrame, 
                                      sensitivity: float) -> Dict[str, Any]:
        """Statistical anomaly detection using IQR method"""
        anomalies = []
        anomaly_scores = {}
        
        for column in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - sensitivity * IQR
            upper_bound = Q3 + sensitivity * IQR
            
            # Find anomalies
            column_anomalies = df[
                (df[column] < lower_bound) | (df[column] > upper_bound)
            ].index.tolist()
            
            if column_anomalies:
                anomalies.extend([
                    {
                        'timestamp': df.loc[idx, 'timestamp'].isoformat() 
                        if 'timestamp' in df.columns else str(idx),
                        'column': column,
                        'value': float(df.loc[idx, column]),
                        'bounds': {'lower': float(lower_bound), 'upper': float(upper_bound)}
                    }
                    for idx in column_anomalies
                ])
                
                # Calculate anomaly scores
                for idx in column_anomalies:
                    score_key = f"{idx}_{column}"
                    value = df.loc[idx, column]
                    
                    if value < lower_bound:
                        score = (lower_bound - value) / IQR if IQR > 0 else 0
                    else:
                        score = (value - upper_bound) / IQR if IQR > 0 else 0
                    
                    anomaly_scores[score_key] = float(score)
        
        return {
            'anomalies': anomalies,
            'anomaly_scores': anomaly_scores,
            'method': 'statistical_iqr',
            'sensitivity': sensitivity
        }
    
    def _ml_anomaly_detection(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Machine learning based anomaly detection"""
        # This is a placeholder for ML-based anomaly detection
        # In production, implement Isolation Forest, One-Class SVM, etc.
        
        return {
            'anomalies': [],
            'anomaly_scores': {},
            'method': 'machine_learning',
            'status': 'not_implemented'
        }
    
    def _seasonal_anomaly_detection(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Seasonal anomaly detection"""
        # Placeholder for seasonal decomposition based anomaly detection
        
        return {
            'anomalies': [],
            'anomaly_scores': {},
            'method': 'seasonal',
            'status': 'not_implemented'
        }
    
    def _explain_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate explanations for detected anomalies"""
        explanations = []
        
        for anomaly in anomalies:
            column = anomaly.get('column', '')
            value = anomaly.get('value', 0)
            bounds = anomaly.get('bounds', {})
            
            if value < bounds.get('lower', 0):
                explanation = (
                    f"Unusually low {column} value ({value:.2f}) detected. "
                    f"Expected minimum: {bounds.get('lower', 0):.2f}"
                )
            else:
                explanation = (
                    f"Unusually high {column} value ({value:.2f}) detected. "
                    f"Expected maximum: {bounds.get('upper', 0):.2f}"
                )
            
            explanations.append(explanation)
        
        return explanations
    
    def _calculate_congestion_metrics(self, congestion_data: pd.Series) -> Dict[str, Any]:
        """Calculate congestion-specific metrics"""
        if congestion_data.empty:
            return {}
        
        return {
            'mean': float(congestion_data.mean()),
            'median': float(congestion_data.median()),
            'std': float(congestion_data.std()),
            'min': float(congestion_data.min()),
            'max': float(congestion_data.max()),
            'percentiles': {
                '25': float(congestion_data.quantile(0.25)),
                '50': float(congestion_data.quantile(0.50)),
                '75': float(congestion_data.quantile(0.75)),
                '90': float(congestion_data.quantile(0.90))
            },
            'congestion_index': float(congestion_data.mean() / 100)
        }
    
    def _calculate_volume_metrics(self, volume_data: pd.Series) -> Dict[str, Any]:
        """Calculate volume-specific metrics"""
        if volume_data.empty:
            return {}
        
        return {
            'total': int(volume_data.sum()),
            'mean': float(volume_data.mean()),
            'median': float(volume_data.median()),
            'peak': int(volume_data.max()),
            'trough': int(volume_data.min()),
            'peak_hour_volume': int(volume_data.max()),
            'avg_daily_volume': int(volume_data.mean() * 24)
        }
    
    def _calculate_speed_metrics(self, speed_data: pd.Series) -> Dict[str, Any]:
        """Calculate speed-specific metrics"""
        if speed_data.empty:
            return {}
        
        return {
            'mean': float(speed_data.mean()),
            'median': float(speed_data.median()),
            'std': float(speed_data.std()),
            'min': float(speed_data.min()),
            'max': float(speed_data.max()),
            'free_flow_ratio': float(speed_data.mean() / 60)  # Compared to 60 km/h free flow
        }
    
    def _calculate_safety_metrics(self, accident_data: pd.Series) -> Dict[str, Any]:
        """Calculate safety-specific metrics"""
        if accident_data.empty:
            return {}
        
        total_accidents = int(accident_data.sum())
        
        return {
            'total': total_accidents,
            'rate_per_1000_vehicles': float(total_accidents / max(1, accident_data.count()) * 1000),
            'trend': 'decreasing' if len(accident_data) > 1 and 
                    accident_data.iloc[-1] < accident_data.iloc[0] else 'stable'
        }
    
    def _calculate_flow_metrics(self, volume_data: pd.Series, 
                              speed_data: pd.Series) -> Dict[str, Any]:
        """Calculate flow-specific metrics"""
        if volume_data.empty or speed_data.empty:
            return {}
        
        flow = volume_data * speed_data
        
        return {
            'mean_flow': float(flow.mean()),
            'peak_flow': float(flow.max()),
            'flow_efficiency': float(flow.mean() / (volume_data.max() * speed_data.max())),
            'capacity_utilization': float(volume_data.mean() / volume_data.max() * 100)
        }
    
    def _calculate_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance metrics"""
        performance = {
            'overall_score': 0,
            'congestion_score': 0,
            'efficiency_score': 0,
            'safety_score': 0,
            'reliability_score': 0
        }
        
        # Calculate individual scores
        if 'congestion' in metrics:
            congestion_mean = metrics['congestion'].get('mean', 50)
            performance['congestion_score'] = max(0, 100 - congestion_mean)
        
        if 'flow' in metrics:
            efficiency = metrics['flow'].get('flow_efficiency', 0.5)
            performance['efficiency_score'] = efficiency * 100
        
        if 'safety' in metrics:
            accident_rate = metrics['safety'].get('rate_per_1000_vehicles', 10)
            performance['safety_score'] = max(0, 100 - accident_rate * 10)
        
        # Calculate reliability score (simplified)
        if 'congestion' in metrics:
            congestion_std = metrics['congestion'].get('std', 15)
            performance['reliability_score'] = max(0, 100 - congestion_std * 2)
        
        # Calculate overall score
        weights = {
            'congestion': 0.4,
            'efficiency': 0.3,
            'safety': 0.2,
            'reliability': 0.1
        }
        
        performance['overall_score'] = (
            performance['congestion_score'] * weights['congestion'] +
            performance['efficiency_score'] * weights['efficiency'] +
            performance['safety_score'] * weights['safety'] +
            performance['reliability_score'] * weights['reliability']
        )
        
        # Add performance level
        overall = performance['overall_score']
        if overall >= 90:
            performance['level'] = 'Excellent'
        elif overall >= 75:
            performance['level'] = 'Good'
        elif overall >= 60:
            performance['level'] = 'Fair'
        else:
            performance['level'] = 'Poor'
        
        return performance