from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import random
import threading
import time


app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

@app.route('/favicon.ico')
def favicon():
    return "", 204

# Simulated traffic data
traffic_data = {
    'locations': [
        {'id': 1, 'name': 'Downtown Intersection', 'lat': 40.7128, 'lng': -74.0060, 'congestion': 65},
        {'id': 2, 'name': 'City Center', 'lat': 40.7580, 'lng': -73.9855, 'congestion': 80},
        {'id': 3, 'name': 'Suburb Junction', 'lat': 40.7549, 'lng': -73.9840, 'congestion': 45},
        {'id': 4, 'name': 'Bridge Approach', 'lat': 40.7505, 'lng': -73.9934, 'congestion': 90},
        {'id': 5, 'name': 'Highway Exit', 'lat': 40.7571, 'lng': -73.9898, 'congestion': 75},
        {'id': 6, 'name': 'Commercial District', 'lat': 40.7614, 'lng': -73.9776, 'congestion': 60},
        {'id': 7, 'name': 'Residential Area', 'lat': 40.7489, 'lng': -73.9680, 'congestion': 35},
        {'id': 8, 'name': 'Industrial Zone', 'lat': 40.7420, 'lng': -73.9560, 'congestion': 50}
    ],
    'signals': [
        {'id': 1, 'location': 'Main St & 1st Ave', 'status': 'normal', 'cycle_time': 120},
        {'id': 2, 'location': 'Broadway & 5th', 'status': 'congested', 'cycle_time': 180},
        {'id': 3, 'location': 'Park Ave & 10th', 'status': 'normal', 'cycle_time': 100},
        {'id': 4, 'location': 'River Rd & Bridge', 'status': 'heavy', 'cycle_time': 200}
    ]
}

# Background thread to simulate real-time updates
def update_traffic_data():
    while True:
        time.sleep(5)
        for loc in traffic_data['locations']:
            change = random.randint(-10, 10)
            loc['congestion'] = max(10, min(100, loc['congestion'] + change))
        
        for signal in traffic_data['signals']:
            if signal['status'] == 'congested':
                signal['cycle_time'] = random.randint(160, 220)
            elif signal['status'] == 'heavy':
                signal['cycle_time'] = random.randint(140, 180)
            else:
                signal['cycle_time'] = random.randint(90, 130)

# Background loop is disabled in serverless (Vercel) to avoid long-running workers.
if os.environ.get('VERCEL') != '1':
    update_thread = threading.Thread(target=update_traffic_data, daemon=True)
    update_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/traffic-map')
def traffic_map():
    return render_template('traffic-map.html')

@app.route('/predictions')
def predictions():
    return render_template('prediction.html')

@app.route('/traffic-control')
def traffic_control():
    return render_template('traffic-control.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

# API Endpoints
@app.route('/api/traffic-data')
def get_traffic_data():
    return jsonify(traffic_data)

@app.route('/api/historical-data')
def get_historical_data():
    # Generate sample historical data
    dates = [(datetime.now() - timedelta(hours=i)).strftime('%H:%M') for i in range(24, -1, -1)]
    congestion = [random.randint(30, 90) for _ in range(25)]
    accidents = [random.randint(0, 5) for _ in range(25)]
    
    return jsonify({
        'timestamps': dates,
        'congestion': congestion,
        'accidents': accidents,
        'avg_speed': [random.randint(20, 60) for _ in range(25)]
    })

@app.route('/api/predict-congestion', methods=['POST'])
def predict_congestion():
    data = request.json
    location = data.get('location', 'downtown')
    hours = data.get('hours', 1)
    
    # Simulated prediction
    predictions = []
    current = traffic_data['locations'][0]['congestion']
    
    for i in range(1, hours + 1):
        prediction = current + random.randint(-15, 20)
        predictions.append(max(10, min(100, prediction)))
    
    return jsonify({
        'predictions': predictions,
        'confidence': random.randint(75, 95),
        'recommendation': 'Adjust signal timing' if predictions[0] > 70 else 'Normal operation'
    })

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    data = request.json
    start = data.get('start', {'lat': 40.7128, 'lng': -74.0060})
    end = data.get('end', {'lat': 40.7580, 'lng': -73.9855})
    
    # Simulated route optimization
    routes = [
        {
            'name': 'Fastest Route',
            'time': '25 mins',
            'distance': '5.2 miles',
            'congestion': 'Medium',
            'steps': ['Start on Main St', 'Turn right on 5th Ave', 'Continue for 2 miles', 'Turn left on Broadway', 'Destination on right']
        },
        {
            'name': 'Alternative Route',
            'time': '28 mins',
            'distance': '5.8 miles',
            'congestion': 'Low',
            'steps': ['Start on Main St', 'Turn left on River Rd', 'Take highway exit 3', 'Merge onto Expressway', 'Exit at 5th St']
        }
    ]
    
    return jsonify({'routes': routes})

@app.route('/api/update-signal', methods=['POST'])
def update_signal():
    data = request.json
    signal_id = data.get('signal_id')
    new_cycle = data.get('cycle_time')
    
    for signal in traffic_data['signals']:
        if signal['id'] == signal_id:
            signal['cycle_time'] = new_cycle
            signal['status'] = 'heavy' if new_cycle > 150 else 'normal'
            break
    
    return jsonify({'success': True, 'message': f'Signal {signal_id} updated'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)