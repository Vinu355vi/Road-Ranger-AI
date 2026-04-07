import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TrafficPredictionModel:
    """Advanced traffic prediction model using ensemble methods"""
    
    def __init__(self, model_dir='models/trained_models/'):
        self.model_dir = model_dir
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_importance = {}
        self.load_all_models()
        
    def load_all_models(self):
        """Load all pre-trained models"""
        os.makedirs(self.model_dir, exist_ok=True)
        
        model_types = ['congestion', 'accident', 'travel_time', 'volume']
        
        for model_type in model_types:
            model_path = os.path.join(self.model_dir, f'traffic_{model_type}_model.pkl')
            scaler_path = os.path.join(self.model_dir, f'traffic_{model_type}_scaler.pkl')
            
            if os.path.exists(model_path):
                try:
                    self.models[model_type] = joblib.load(model_path)
                    print(f"Loaded {model_type} model from {model_path}")
                except Exception as e:
                    print(f"Error loading {model_type} model: {e}")
                    self.models[model_type] = self.create_model(model_type)
            else:
                self.models[model_type] = self.create_model(model_type)
            
            if os.path.exists(scaler_path):
                try:
                    self.scalers[model_type] = joblib.load(scaler_path)
                except Exception as e:
                    print(f"Error loading {model_type} scaler: {e}")
                    self.scalers[model_type] = StandardScaler()
            else:
                self.scalers[model_type] = StandardScaler()
    
    def create_model(self, model_type):
        """Create a new model based on type"""
        if model_type == 'congestion':
            return RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'accident':
            return GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif model_type == 'travel_time':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        else:  # volume
            return GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=7,
                random_state=42
            )
    
    def prepare_features(self, data, model_type='congestion'):
        """Prepare features for specific model type"""
        df = pd.DataFrame([data]) if isinstance(data, dict) else data.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['day_of_month'] = df['timestamp'].dt.day
            df['month'] = df['timestamp'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Time of day categories
            df['time_of_day'] = pd.cut(
                df['hour'],
                bins=[-1, 5, 9, 16, 20, 23],
                labels=['night', 'morning_peak', 'day', 'evening_peak', 'night_late']
            )
        
        # Model-specific features
        if model_type == 'congestion':
            features = [
                'hour', 'day_of_week', 'month', 'is_weekend',
                'temperature', 'precipitation', 'visibility',
                'prev_hour_congestion', 'avg_last_3_hours',
                'vehicle_count', 'avg_speed', 'accident_count'
            ]
        elif model_type == 'accident':
            features = [
                'hour', 'day_of_week', 'is_weekend',
                'congestion', 'vehicle_count', 'avg_speed',
                'precipitation', 'visibility', 'road_condition',
                'previous_accidents_24h'
            ]
        elif model_type == 'travel_time':
            features = [
                'hour', 'day_of_week', 'is_weekend',
                'congestion', 'vehicle_count',
                'distance', 'road_type', 'signal_count',
                'weather_condition'
            ]
        else:  # volume
            features = [
                'hour', 'day_of_week', 'month', 'is_weekend',
                'day_of_month', 'is_holiday',
                'temperature', 'precipitation',
                'previous_day_volume', 'previous_week_volume'
            ]
        
        # Add missing features with default values
        for feature in features:
            if feature not in df.columns:
                if 'prev' in feature or 'previous' in feature:
                    df[feature] = 0
                elif feature in ['temperature', 'visibility']:
                    df[feature] = 20
                elif feature == 'precipitation':
                    df[feature] = 0
                elif feature == 'congestion':
                    df[feature] = 50
                elif feature == 'vehicle_count':
                    df[feature] = 100
                elif feature == 'avg_speed':
                    df[feature] = 40
                elif feature == 'accident_count':
                    df[feature] = 0
                else:
                    df[feature] = 0
        
        # Encode categorical features
        categorical_features = df.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_features:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))
        
        return df[features]
    
    def train(self, X_train, y_train, model_type='congestion'):
        """Train a specific model"""
        if model_type not in self.models:
            self.models[model_type] = self.create_model(model_type)
        
        # Prepare features
        X_processed = self.prepare_features(X_train, model_type)
        
        # Scale features
        X_scaled = self.scalers[model_type].fit_transform(X_processed)
        
        # Train model
        self.models[model_type].fit(X_scaled, y_train)
        
        # Calculate feature importance
        if hasattr(self.models[model_type], 'feature_importances_'):
            self.feature_importance[model_type] = dict(
                zip(X_processed.columns, self.models[model_type].feature_importances_)
            )
        
        # Save model and scaler
        self.save_model(model_type)
        
        return self.models[model_type]
    
    def predict(self, X, model_type='congestion'):
        """Make predictions using specific model"""
        if model_type not in self.models:
            raise ValueError(f"Model type '{model_type}' not found")
        
        # Prepare features
        X_processed = self.prepare_features(X, model_type)
        
        # Scale features
        X_scaled = self.scalers[model_type].transform(X_processed)
        
        # Make predictions
        predictions = self.models[model_type].predict(X_scaled)
        
        # Apply model-specific adjustments
        if model_type == 'congestion':
            predictions = np.clip(predictions, 0, 100)
        elif model_type == 'accident':
            predictions = np.clip(predictions, 0, None)
        elif model_type == 'travel_time':
            predictions = np.clip(predictions, 1, None)
        elif model_type == 'volume':
            predictions = np.clip(predictions, 0, None)
        
        return predictions
    
    def predict_congestion(self, features, hours_ahead=6):
        """Predict congestion for multiple hours ahead"""
        predictions = []
        confidences = []
        
        current_time = datetime.now()
        
        for i in range(1, hours_ahead + 1):
            # Create features for future hour
            future_time = current_time + timedelta(hours=i)
            
            future_features = {
                'timestamp': future_time,
                'hour': future_time.hour,
                'day_of_week': future_time.weekday(),
                'month': future_time.month,
                'is_weekend': 1 if future_time.weekday() in [5, 6] else 0,
                'temperature': features.get('temperature', 20),
                'precipitation': features.get('precipitation', 0),
                'visibility': features.get('visibility', 10),
                'prev_hour_congestion': predictions[-1] if predictions else features.get('current_congestion', 50),
                'avg_last_3_hours': np.mean([features.get('current_congestion', 50)] + predictions[-2:]) 
                                    if len(predictions) >= 2 else features.get('current_congestion', 50),
                'vehicle_count': features.get('vehicle_count', 100),
                'avg_speed': features.get('avg_speed', 40),
                'accident_count': features.get('accident_count', 0)
            }
            
            # Make prediction
            pred = self.predict(future_features, model_type='congestion')[0]
            predictions.append(pred)
            
            # Calculate confidence (simplified)
            hour = future_time.hour
            if 7 <= hour <= 9 or 16 <= hour <= 18:  # Peak hours
                confidence = 0.85 + (0.1 * (1 - abs(pred - 75) / 75))
            else:
                confidence = 0.90 + (0.1 * (1 - abs(pred - 50) / 50))
            
            confidences.append(min(0.95, max(0.70, confidence)))
        
        return predictions, confidences
    
    def predict_accident_risk(self, features):
        """Predict accident risk for current conditions"""
        risk_score = self.predict(features, model_type='accident')[0]
        
        # Convert to risk levels
        if risk_score < 0.1:
            risk_level = 'Low'
            color = 'green'
        elif risk_score < 0.3:
            risk_level = 'Medium'
            color = 'yellow'
        elif risk_score < 0.5:
            risk_level = 'High'
            color = 'orange'
        else:
            risk_level = 'Severe'
            color = 'red'
        
        return {
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'color': color,
            'recommendations': self.get_accident_recommendations(risk_level)
        }
    
    def get_accident_recommendations(self, risk_level):
        """Get recommendations based on accident risk level"""
        recommendations = {
            'Low': [
                'Normal operations',
                'Regular monitoring'
            ],
            'Medium': [
                'Increase patrol frequency',
                'Monitor high-risk intersections'
            ],
            'High': [
                'Activate emergency response teams',
                'Implement speed restrictions',
                'Increase CCTV monitoring'
            ],
            'Severe': [
                'Deploy all available resources',
                'Consider road closures',
                'Activate emergency broadcast system'
            ]
        }
        return recommendations.get(risk_level, [])
    
    def predict_travel_time(self, route_features):
        """Predict travel time for a route"""
        travel_time = self.predict(route_features, model_type='travel_time')[0]
        
        # Adjust based on current conditions
        congestion = route_features.get('congestion', 50)
        adjustment_factor = 1 + (congestion / 100 * 0.5)
        adjusted_time = travel_time * adjustment_factor
        
        return {
            'base_travel_time': float(travel_time),
            'adjusted_travel_time': float(adjusted_time),
            'congestion_impact': float(adjustment_factor - 1) * 100,
            'confidence': 0.85
        }
    
    def evaluate_model(self, X_test, y_test, model_type='congestion'):
        """Evaluate model performance"""
        predictions = self.predict(X_test, model_type)
        
        metrics = {
            'mae': float(mean_absolute_error(y_test, predictions)),
            'rmse': float(np.sqrt(mean_squared_error(y_test, predictions))),
            'r2': float(r2_score(y_test, predictions)),
            'mean_absolute_percentage_error': float(
                np.mean(np.abs((y_test - predictions) / y_test)) * 100
            )
        }
        
        return metrics
    
    def save_model(self, model_type):
        """Save model and scaler to disk"""
        model_path = os.path.join(self.model_dir, f'traffic_{model_type}_model.pkl')
        scaler_path = os.path.join(self.model_dir, f'traffic_{model_type}_scaler.pkl')
        
        try:
            joblib.dump(self.models[model_type], model_path)
            joblib.dump(self.scalers[model_type], scaler_path)
            print(f"Saved {model_type} model to {model_path}")
        except Exception as e:
            print(f"Error saving {model_type} model: {e}")
    
    def save_all_models(self):
        """Save all models and scalers"""
        for model_type in self.models.keys():
            self.save_model(model_type)
    
    def get_model_info(self, model_type='congestion'):
        """Get information about a model"""
        if model_type not in self.models:
            return None
        
        model = self.models[model_type]
        
        info = {
            'model_type': model_type,
            'model_class': model.__class__.__name__,
            'parameters': model.get_params() if hasattr(model, 'get_params') else {},
            'feature_importance': self.feature_importance.get(model_type, {}),
            'last_trained': datetime.now().isoformat(),
            'performance': {}
        }
        
        return info
    
    def generate_sample_data(self, n_samples=1000):
        """Generate sample training data"""
        np.random.seed(42)
        
        timestamps = pd.date_range(
            start='2024-01-01',
            periods=n_samples,
            freq='H'
        )
        
        data = {
            'timestamp': timestamps,
            'hour': timestamps.hour,
            'day_of_week': timestamps.dayofweek,
            'month': timestamps.month,
            'temperature': np.random.normal(20, 5, n_samples),
            'precipitation': np.random.exponential(0.5, n_samples),
            'visibility': np.random.normal(10, 3, n_samples),
            'vehicle_count': np.random.poisson(500, n_samples),
            'avg_speed': np.random.normal(50, 15, n_samples),
            'congestion': np.random.uniform(0, 100, n_samples),
            'accident_count': np.random.poisson(0.1, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create realistic patterns
        df['congestion'] = df.apply(lambda row: 
            row['congestion'] + 
            (20 if 7 <= row['hour'] <= 9 else 0) +  # Morning peak
            (30 if 16 <= row['hour'] <= 18 else 0) +  # Evening peak
            (10 if row['day_of_week'] in [0, 4] else 0) +  # Monday & Friday
            (-15 if row['day_of_week'] in [5, 6] else 0) +  # Weekend
            (row['precipitation'] * 10) +  # Rain effect
            np.random.normal(0, 10),  # Random noise
            axis=1
        )
        
        df['congestion'] = np.clip(df['congestion'], 0, 100)
        
        # Lag features
        df['prev_hour_congestion'] = df['congestion'].shift(1).fillna(50)
        df['avg_last_3_hours'] = df['congestion'].rolling(window=3).mean().fillna(50)
        
        return df