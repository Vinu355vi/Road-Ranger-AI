from flask import Blueprint, jsonify

api = Blueprint('api', __name__)

@api.route('/status', methods=['GET'])
def get_status():
    return jsonify({'status': 'running', 'message': 'Traffic Prediction API is active'})

@api.route('/traffic-data', methods=['GET'])
def get_traffic_data():
    # Mock data for demonstration
    data = {
        'locations': [
            {'id': 1, 'name': 'Main St & 1st Ave', 'lat': 40.7128, 'lng': -74.0060, 'congestion': 65},
            {'id': 2, 'name': 'Broadway & Wall St', 'lat': 40.7075, 'lng': -74.0113, 'congestion': 85},
            {'id': 3, 'name': '5th Ave & 42nd St', 'lat': 40.7589, 'lng': -73.9818, 'congestion': 30}
        ],
        'signals': [
            {'id': 1, 'location': 'Main St & 1st Ave', 'status': 'active', 'cycle_time': 60},
            {'id': 2, 'location': 'Broadway & Wall St', 'status': 'congested', 'cycle_time': 90},
            {'id': 3, 'location': '5th Ave & 42nd St', 'status': 'active', 'cycle_time': 45}
        ]
    }
    return jsonify(data)

@api.route('/update-signal', methods=['POST'])
def update_signal():
    return jsonify({'status': 'success', 'message': 'Signal updated'})

@api.route('/predict-congestion', methods=['POST'])
def predict_congestion():
    import random
    data = {
        'confidence': 85,
        'recommendation': 'Increase signal cycle at Main St',
        'predictions': [random.randint(40, 90) for _ in range(5)]
    }
    return jsonify(data)

@api.route('/optimize-route', methods=['POST'])
def optimize_route():
    data = {
        'routes': [
            {
                'name': 'Fastest Route',
                'time': '15 mins',
                'distance': '5.2 km',
                'congestion': 'Low',
                'steps': ['Turn right on Main', 'Keep left on Broadway', 'Arrive']
            },
            {
                'name': 'Alternative Route',
                'time': '22 mins',
                'distance': '6.1 km',
                'congestion': 'Medium',
                'steps': ['Turn left on 1st Ave', 'Right on Wall St', 'Arrive']
            }
        ]
    }
    return jsonify(data)
