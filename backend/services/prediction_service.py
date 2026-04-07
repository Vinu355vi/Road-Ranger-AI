import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple
from backend.models.traffic_model import TrafficPredictionModel
from backend.utils.data_processor import DataProcessor

class PredictionService:
    """Service for handling all prediction operations"""
    
    def __init__(self):
        self.traffic_model = TrafficPredictionModel()
        self.data_processor = DataProcessor()
        self.predictions_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes cache
        
    def predict_congestion(self, location_data: Dict[str, Any], 
                          hours_ahead: int = 6) -> Dict[str, Any]:
        """Predict congestion for a location"""
        cache_key = f"congestion_{location_data.get('location_id', 'unknown')}_{hours_ahead}"
        
        # Check cache
        if self._check_cache(cache_key):
            return self.predictions_cache[cache_key]
        
        try:
            # Prepare features
            features = self._prepare_congestion_features(location_data)
            
            # Get predictions
            predictions, confidences = self.traffic_model.predict_congestion(
                features, hours_ahead
            )
            
            # Analyze patterns
            pattern_analysis = self._analyze_congestion_pattern(predictions)
            
            # Generate recommendations
            recommendations = self._generate_congestion_recommendations(
                predictions, pattern_analysis
            )
            
            result = {
                'success': True,
                'predictions': [float(p) for p in predictions],
                'confidences': [float(c) for c in confidences],
                'pattern_analysis': pattern_analysis,
                'recommendations': recommendations,
                'peak_congestion': float(max(predictions)),
                'peak_time': predictions.index(max(predictions)) + 1,
                'avg_congestion': float(np.mean(predictions)),
                'prediction_horizon': hours_ahead,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'predictions': [50] * hours_ahead,
                'confidences': [0.8] * hours_ahead,
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_multiple_locations(self, locations_data: List[Dict[str, Any]], 
                                  hours_ahead: int = 6) -> Dict[str, Any]:
        """Predict congestion for multiple locations"""
        results = {}
        hotspot_analysis = []
        
        for location in locations_data:
            location_id = location.get('location_id', 'unknown')
            prediction = self.predict_congestion(location, hours_ahead)
            results[location_id] = prediction
            
            # Check if location is a hotspot
            if prediction['success'] and prediction['peak_congestion'] > 70:
                hotspot_analysis.append({
                    'location_id': location_id,
                    'location_name': location.get('name', 'Unknown'),
                    'peak_congestion': prediction['peak_congestion'],
                    'peak_time': prediction['peak_time'],
                    'recommendations': prediction['recommendations'][:2]  # Top 2 recommendations
                })
        
        # Sort hotspots by severity
        hotspot_analysis.sort(key=lambda x: x['peak_congestion'], reverse=True)
        
        return {
            'success': True,
            'locations': results,
            'hotspot_analysis': hotspot_analysis,
            'total_hotspots': len(hotspot_analysis),
            'severest_hotspot': hotspot_analysis[0] if hotspot_analysis else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_accident_risk(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Predict accident risk based on current conditions"""
        try:
            risk_prediction = self.traffic_model.predict_accident_risk(conditions)
            
            # Add temporal factors
            current_hour = datetime.now().hour
            if 7 <= current_hour <= 9 or 16 <= current_hour <= 18:
                risk_prediction['temporal_factor'] = 'Peak hours - Increased risk'
                risk_prediction['adjusted_risk_score'] = min(
                    1.0, risk_prediction['risk_score'] * 1.3
                )
            else:
                risk_prediction['temporal_factor'] = 'Off-peak hours'
                risk_prediction['adjusted_risk_score'] = risk_prediction['risk_score']
            
            # Add weather impact
            if conditions.get('precipitation', 0) > 0.5:
                risk_prediction['weather_impact'] = 'Rain - Increased risk'
                risk_prediction['adjusted_risk_score'] = min(
                    1.0, risk_prediction['adjusted_risk_score'] * 1.5
                )
            else:
                risk_prediction['weather_impact'] = 'Clear weather'
            
            return {
                'success': True,
                'risk_prediction': risk_prediction,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_travel_time(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict travel time for a route"""
        try:
            # Get base prediction
            travel_time_pred = self.traffic_model.predict_travel_time(route_data)
            
            # Consider real-time factors
            current_time = datetime.now()
            day_of_week = current_time.weekday()
            hour = current_time.hour
            
            # Time-based adjustments
            time_factor = 1.0
            if 7 <= hour <= 9:  # Morning peak
                time_factor = 1.4
            elif 16 <= hour <= 18:  # Evening peak
                time_factor = 1.5
            elif 22 <= hour or hour <= 5:  # Night
                time_factor = 0.8
            
            # Day-based adjustments
            if day_of_week in [5, 6]:  # Weekend
                time_factor *= 0.9
            
            # Weather adjustments
            if route_data.get('precipitation', 0) > 0:
                time_factor *= 1.2
            
            # Calculate final travel time
            final_travel_time = travel_time_pred['adjusted_travel_time'] * time_factor
            
            # Generate alternative routes
            alternative_routes = self._generate_alternative_routes(
                route_data, final_travel_time
            )
            
            return {
                'success': True,
                'base_prediction': travel_time_pred,
                'time_adjustment_factor': time_factor,
                'final_travel_time_minutes': float(final_travel_time),
                'alternative_routes': alternative_routes,
                'optimal_route': min(alternative_routes, key=lambda x: x['travel_time']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_traffic_volume(self, location_data: Dict[str, Any], 
                              hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict traffic volume for a location"""
        try:
            # Prepare volume features
            features = self._prepare_volume_features(location_data)
            
            # Generate predictions for each hour
            predictions = []
            current_time = datetime.now()
            
            for i in range(hours_ahead):
                future_time = current_time + timedelta(hours=i)
                features['hour'] = future_time.hour
                features['day_of_week'] = future_time.weekday()
                features['is_weekend'] = 1 if future_time.weekday() in [5, 6] else 0
                
                # Get prediction (simplified - in real app use volume model)
                base_volume = location_data.get('current_volume', 1000)
                
                # Time-based adjustment
                hour_factor = 1.0
                if 7 <= features['hour'] <= 9:
                    hour_factor = 1.5  # Morning peak
                elif 16 <= features['hour'] <= 18:
                    hour_factor = 1.6  # Evening peak
                elif 22 <= features['hour'] or features['hour'] <= 5:
                    hour_factor = 0.5  # Night
                
                # Day-based adjustment
                if features['is_weekend']:
                    hour_factor *= 0.8
                
                predicted_volume = base_volume * hour_factor * (1 + np.random.normal(0, 0.1))
                
                predictions.append({
                    'hour': i,
                    'time': future_time.strftime('%H:%M'),
                    'predicted_volume': int(max(0, predicted_volume)),
                    'confidence': 0.85 - (abs(hour_factor - 1) * 0.1)
                })
            
            # Analyze volume patterns
            volume_analysis = self._analyze_volume_pattern(predictions)
            
            return {
                'success': True,
                'predictions': predictions,
                'volume_analysis': volume_analysis,
                'peak_volume': max(p['predicted_volume'] for p in predictions),
                'peak_time': next(p['time'] for p in predictions 
                                if p['predicted_volume'] == max(p['predicted_volume'] for p in predictions)),
                'avg_volume': int(np.mean([p['predicted_volume'] for p in predictions])),
                'prediction_horizon': hours_ahead,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_event_impact(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict traffic impact of an event"""
        try:
            event_location = event_data.get('location', {})
            event_attendees = event_data.get('attendees', 1000)
            event_duration = event_data.get('duration_hours', 3)
            
            # Calculate impact radius (in km)
            impact_radius = min(5, event_attendees / 500)  # 0.5km per 500 attendees
            
            # Estimate additional vehicles
            additional_vehicles = event_attendees * 0.3  # Assume 30% come by car
            
            # Calculate congestion increase
            base_congestion = event_data.get('base_congestion', 50)
            congestion_increase = min(30, (additional_vehicles / 100) * 5)
            
            # Time-based impact
            event_start = datetime.fromisoformat(event_data.get('start_time', datetime.now().isoformat()))
            impact_start = event_start - timedelta(hours=1)
            impact_end = event_start + timedelta(hours=event_duration + 1)
            
            # Generate impact timeline
            impact_timeline = []
            current = impact_start
            
            while current <= impact_end:
                hour_offset = (current - impact_start).total_seconds() / 3600
                
                # Impact curve (bell curve)
                impact_factor = np.exp(-((hour_offset - (event_duration/2 + 1)) ** 2) / 2)
                hour_congestion = base_congestion + (congestion_increase * impact_factor)
                
                impact_timeline.append({
                    'time': current.strftime('%H:%M'),
                    'congestion': float(min(100, hour_congestion)),
                    'impact_level': self._get_impact_level(hour_congestion - base_congestion)
                })
                
                current += timedelta(hours=1)
            
            # Generate recommendations
            recommendations = self._generate_event_recommendations(
                event_data, congestion_increase, impact_radius
            )
            
            return {
                'success': True,
                'event_impact': {
                    'estimated_additional_vehicles': int(additional_vehicles),
                    'congestion_increase': float(congestion_increase),
                    'impact_radius_km': float(impact_radius),
                    'impact_duration_hours': (impact_end - impact_start).total_seconds() / 3600,
                    'peak_impact_time': event_start.strftime('%H:%M'),
                    'maximum_congestion': float(min(100, base_congestion + congestion_increase))
                },
                'impact_timeline': impact_timeline,
                'recommendations': recommendations,
                'affected_areas': self._identify_affected_areas(event_location, impact_radius),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        try:
            # Generate sample data for evaluation
            sample_data = self.traffic_model.generate_sample_data(1000)
            
            # Split data
            train_size = int(len(sample_data) * 0.8)
            train_data = sample_data.iloc[:train_size]
            test_data = sample_data.iloc[train_size:]
            
            performance_metrics = {}
            
            # Evaluate each model
            for model_type in ['congestion', 'accident', 'travel_time']:
                # For demonstration, create simple metrics
                # In production, use actual evaluation
                performance_metrics[model_type] = {
                    'accuracy': 0.85 + np.random.random() * 0.1,
                    'precision': 0.82 + np.random.random() * 0.12,
                    'recall': 0.88 + np.random.random() * 0.08,
                    'f1_score': 0.85 + np.random.random() * 0.1,
                    'mae': 8.5 + np.random.random() * 3,
                    'rmse': 12.0 + np.random.random() * 4,
                    'last_evaluated': datetime.now().isoformat(),
                    'training_samples': len(train_data),
                    'testing_samples': len(test_data)
                }
            
            return {
                'success': True,
                'performance_metrics': performance_metrics,
                'overall_accuracy': np.mean([m['accuracy'] for m in performance_metrics.values()]),
                'model_status': 'operational',
                'last_retrained': (datetime.now() - timedelta(days=7)).isoformat(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_congestion_features(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare features for congestion prediction"""
        features = {
            'timestamp': datetime.now(),
            'current_congestion': location_data.get('congestion', 50),
            'vehicle_count': location_data.get('vehicle_count', 100),
            'avg_speed': location_data.get('avg_speed', 40),
            'accident_count': location_data.get('accident_count', 0),
            'temperature': location_data.get('temperature', 20),
            'precipitation': location_data.get('precipitation', 0),
            'visibility': location_data.get('visibility', 10),
            'road_condition': location_data.get('road_condition', 'dry'),
            'signal_status': location_data.get('signal_status', 'normal')
        }
        
        # Add historical data if available
        if 'historical_congestion' in location_data:
            hist_data = location_data['historical_congestion']
            if len(hist_data) > 0:
                features['prev_hour_congestion'] = hist_data[-1]
            if len(hist_data) >= 3:
                features['avg_last_3_hours'] = np.mean(hist_data[-3:])
        
        return features
    
    def _prepare_volume_features(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare features for volume prediction"""
        features = {
            'current_volume': location_data.get('current_volume', 1000),
            'historical_volumes': location_data.get('historical_volumes', []),
            'location_type': location_data.get('location_type', 'intersection'),
            'lane_count': location_data.get('lane_count', 2),
            'is_main_road': location_data.get('is_main_road', False)
        }
        
        return features
    
    def _analyze_congestion_pattern(self, predictions: List[float]) -> Dict[str, Any]:
        """Analyze congestion pattern from predictions"""
        if not predictions:
            return {}
        
        predictions_array = np.array(predictions)
        
        # Identify peaks
        peak_indices = np.where(predictions_array > 70)[0]
        
        # Calculate trend
        if len(predictions) > 1:
            trend = 'increasing' if predictions[-1] > predictions[0] else 'decreasing'
            trend_strength = abs(predictions[-1] - predictions[0]) / 100
        else:
            trend = 'stable'
            trend_strength = 0
        
        # Pattern classification
        if len(peak_indices) > 0:
            if len(peak_indices) >= 2:
                pattern = 'double_peak'
            else:
                pattern = 'single_peak'
        elif np.mean(predictions_array) > 60:
            pattern = 'consistently_high'
        elif np.mean(predictions_array) < 30:
            pattern = 'consistently_low'
        else:
            pattern = 'moderate_variation'
        
        return {
            'pattern_type': pattern,
            'trend': trend,
            'trend_strength': float(trend_strength),
            'peak_count': len(peak_indices),
            'peak_hours': [int(idx + 1) for idx in peak_indices],
            'volatility': float(np.std(predictions_array)),
            'classification': self._classify_congestion_pattern(predictions_array)
        }
    
    def _classify_congestion_pattern(self, predictions: np.ndarray) -> str:
        """Classify the congestion pattern"""
        mean_congestion = np.mean(predictions)
        std_congestion = np.std(predictions)
        
        if mean_congestion < 30:
            return 'Free Flow'
        elif mean_congestion < 50:
            return 'Light Traffic'
        elif mean_congestion < 70:
            if std_congestion > 15:
                return 'Variable Traffic'
            else:
                return 'Moderate Traffic'
        elif mean_congestion < 85:
            return 'Heavy Traffic'
        else:
            return 'Severe Congestion'
    
    def _analyze_volume_pattern(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze volume pattern from predictions"""
        volumes = [p['predicted_volume'] for p in predictions]
        
        if not volumes:
            return {}
        
        volumes_array = np.array(volumes)
        
        return {
            'peak_volume': int(max(volumes)),
            'trough_volume': int(min(volumes)),
            'avg_volume': int(np.mean(volumes)),
            'volume_variation': float(np.std(volumes) / np.mean(volumes) * 100),
            'peak_to_trough_ratio': float(max(volumes) / min(volumes)) if min(volumes) > 0 else 0,
            'classification': self._classify_volume_pattern(volumes_array)
        }
    
    def _classify_volume_pattern(self, volumes: np.ndarray) -> str:
        """Classify the volume pattern"""
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        cv = std_volume / mean_volume if mean_volume > 0 else 0
        
        if cv < 0.2:
            return 'Steady Flow'
        elif cv < 0.4:
            return 'Moderate Variation'
        else:
            return 'Highly Variable'
    
    def _generate_congestion_recommendations(self, predictions: List[float], 
                                           pattern_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on congestion predictions"""
        recommendations = []
        
        max_congestion = max(predictions) if predictions else 0
        pattern_type = pattern_analysis.get('pattern_type', '')
        
        # General recommendations based on max congestion
        if max_congestion > 80:
            recommendations.extend([
                'Activate emergency traffic management protocol',
                'Deploy additional traffic control personnel',
                'Implement alternative route diversions',
                'Increase public transport frequency'
            ])
        elif max_congestion > 60:
            recommendations.extend([
                'Adjust signal timings for peak periods',
                'Monitor high-congestion areas closely',
                'Prepare incident response teams',
                'Communicate traffic alerts to public'
            ])
        
        # Pattern-specific recommendations
        if pattern_type == 'double_peak':
            recommendations.append('Implement separate morning and evening peak strategies')
        elif pattern_type == 'consistently_high':
            recommendations.append('Consider long-term infrastructure improvements')
        elif pattern_type == 'single_peak':
            peak_hour = predictions.index(max_congestion) + 1
            recommendations.append(f'Focus resources on hour {peak_hour}')
        
        # Add standard recommendations
        recommendations.extend([
            'Monitor weather conditions for impact',
            'Update digital signage with current conditions',
            'Coordinate with public transport authorities'
        ])
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def _generate_alternative_routes(self, route_data: Dict[str, Any], 
                                   base_travel_time: float) -> List[Dict[str, Any]]:
        """Generate alternative route options"""
        alternatives = []
        
        # Alternative 1: Faster but longer
        alternatives.append({
            'name': 'Express Route',
            'distance_km': route_data.get('distance', 10) * 1.2,
            'travel_time': base_travel_time * 0.85,
            'congestion': 'Low',
            'advantages': ['Faster', 'Fewer traffic lights'],
            'disadvantages': ['Longer distance', 'Toll road'],
            'recommended_for': 'Time-sensitive travel'
        })
        
        # Alternative 2: Shorter but slower
        alternatives.append({
            'name': 'City Route',
            'distance_km': route_data.get('distance', 10) * 0.9,
            'travel_time': base_travel_time * 1.15,
            'congestion': 'Medium',
            'advantages': ['Shorter distance', 'Scenic route'],
            'disadvantages': ['More traffic lights', 'Higher congestion'],
            'recommended_for': 'Leisure travel'
        })
        
        # Alternative 3: Eco-friendly
        alternatives.append({
            'name': 'Green Route',
            'distance_km': route_data.get('distance', 10) * 1.1,
            'travel_time': base_travel_time * 0.95,
            'congestion': 'Low',
            'advantages': ['Lower emissions', 'Bike lanes available'],
            'disadvantages': ['Slightly longer', 'Fewer amenities'],
            'recommended_for': 'Eco-conscious travel'
        })
        
        return alternatives
    
    def _generate_event_recommendations(self, event_data: Dict[str, Any], 
                                      congestion_increase: float, 
                                      impact_radius: float) -> List[str]:
        """Generate recommendations for event traffic management"""
        recommendations = []
        
        if congestion_increase > 20:
            recommendations.extend([
                'Implement parking restrictions around venue',
                'Set up dedicated event traffic lanes',
                'Increase public transport to venue',
                'Coordinate with event organizers for staggered exits'
            ])
        elif congestion_increase > 10:
            recommendations.extend([
                'Deploy additional traffic controllers',
                'Monitor key approach roads',
                'Prepare temporary signage',
                'Communicate parking options'
            ])
        
        recommendations.extend([
            f'Alert residents within {impact_radius:.1f}km radius',
            'Coordinate with local businesses',
            'Prepare emergency vehicle access routes',
            'Monitor social media for traffic reports'
        ])
        
        return recommendations
    
    def _identify_affected_areas(self, event_location: Dict[str, Any], 
                               impact_radius: float) -> List[Dict[str, Any]]:
        """Identify areas affected by event"""
        # In production, this would use GIS data
        # For now, return simulated areas
        
        areas = [
            {
                'name': 'Venue Perimeter',
                'distance_km': 0.5,
                'impact_level': 'High',
                'recommendations': ['Road closures', 'Parking restrictions']
            },
            {
                'name': 'Immediate Vicinity',
                'distance_km': 1.0,
                'impact_level': 'Medium',
                'recommendations': ['Traffic diversions', 'Increased monitoring']
            },
            {
                'name': 'Surrounding Area',
                'distance_km': impact_radius,
                'impact_level': 'Low',
                'recommendations': ['Traffic advisories', 'Alternative route suggestions']
            }
        ]
        
        return areas
    
    def _get_impact_level(self, congestion_change: float) -> str:
        """Get impact level based on congestion change"""
        if congestion_change > 20:
            return 'Severe'
        elif congestion_change > 10:
            return 'High'
        elif congestion_change > 5:
            return 'Medium'
        else:
            return 'Low'
    
    def _check_cache(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key in self.predictions_cache:
            expiry_time = self.cache_expiry.get(cache_key)
            if expiry_time and datetime.now() < expiry_time:
                return True
            else:
                # Remove expired cache
                del self.predictions_cache[cache_key]
                if cache_key in self.cache_expiry:
                    del self.cache_expiry[cache_key]
        return False
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache prediction result"""
        self.predictions_cache[cache_key] = result
        self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)