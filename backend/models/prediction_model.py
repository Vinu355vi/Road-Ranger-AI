import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import json

class TrafficPredictionModel:
    def __init__(self, model_path=None):
        self.model = None
        self.scaler = StandardScaler()
        self.features = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'temperature', 'precipitation', 'visibility',
            'prev_hour_congestion', 'avg_last_3_hours'
        ]
        self.model_path = model_path or 'models/trained_models/traffic_rf_model.pkl'
        self.load_model()
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"Model loaded from {self.model_path}")
            else:
                print("No pre-trained model found. Initializing new model.")
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
    
    def save_model(self):
        """Save model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def prepare_features(self, data):
        """Prepare features for prediction"""
        df = pd.DataFrame(data)
        
        # Extract time-based features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Ensure all required features are present
        for feature in self.features:
            if feature not in df.columns:
                if feature == 'prev_hour_congestion':
                    df[feature] = df.get('congestion', 50)
                elif feature == 'avg_last_3_hours':
                    df[feature] = df.get('congestion', 50)
                else:
                    df[feature] = 0
        
        return df[self.features]
    
    def train(self, X, y):
        """Train the model"""
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.save_model()
            return True
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def predict(self, features):
        """Make predictions"""
        try:
            if self.model is None:
                self.load_model()
            
            # Prepare features
            X = self.prepare_features(features)
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            predictions = self.model.predict(X_scaled)
            
            # Clip predictions to valid range
            predictions = np.clip(predictions, 0, 100)
            
            return predictions.tolist()
        except Exception as e:
            print(f"Error making predictions: {e}")
            # Return dummy predictions if model fails
            return [50] * len(features)
    
    def predict_future(self, current_data, hours_ahead=6):
        """Predict congestion for future hours"""
        predictions = []
        
        for i in range(1, hours_ahead + 1):
            # Create features for future hour
            future_time = datetime.now() + timedelta(hours=i)
            
            future_features = {
                'timestamp': future_time,
                'hour': future_time.hour,
                'day_of_week': future_time.weekday(),
                'month': future_time.month,
                'is_weekend': 1 if future_time.weekday() in [5, 6] else 0,
                'temperature': current_data.get('temperature', 20),
                'precipitation': current_data.get('precipitation', 0),
                'visibility': current_data.get('visibility', 10),
                'prev_hour_congestion': predictions[-1] if predictions else current_data.get('congestion', 50),
                'avg_last_3_hours': np.mean([current_data.get('congestion', 50)] + predictions[-2:]) if len(predictions) >= 2 else current_data.get('congestion', 50)
            }
            
            # Make prediction for this hour
            pred = self.predict([future_features])[0]
            predictions.append(pred)
        
        return predictions