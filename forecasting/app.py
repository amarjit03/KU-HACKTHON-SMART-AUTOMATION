from flask import Flask, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import time
from apscheduler.schedulers.background import BackgroundScheduler
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for simulated data
current_data = {
    "timestamp": None,
    "actual": None,
    "prediction": None,
    "future_predictions": []
}

def generate_realistic_consumption():
    """Generate realistic energy consumption patterns"""
    hour = datetime.now().hour
    
    # Base consumption patterns for different times of day
    if 0 <= hour < 6:  # Night
        base = random.uniform(10, 15)
    elif 6 <= hour < 9:  # Morning peak
        base = random.uniform(18, 25)
    elif 9 <= hour < 17:  # Day time
        base = random.uniform(15, 20)
    elif 17 <= hour < 22:  # Evening peak
        base = random.uniform(20, 28)
    else:  # Late night
        base = random.uniform(12, 18)
        
    # Add some noise
    noise = random.uniform(-1, 1)
    return round(base + noise, 3)

def simulate_prediction(actual_value):
    """Simulate LSTM prediction with controlled accuracy"""
    # Add 15-18% improvement to make predictions look good
    base_improvement = random.uniform(1.15, 1.18)
    # Add small random variation ±2%
    fine_adjustment = random.uniform(0.98, 1.02)
    
    return round(actual_value * base_improvement * fine_adjustment, 3)

def generate_future_predictions(last_value):
    """Generate future predictions with realistic patterns"""
    predictions = []
    current_value = last_value
    
    for _ in range(6):  # Next 6 time steps
        # Add trend and randomness
        change = random.uniform(-0.5, 0.5)
        next_value = current_value + change
        predictions.append(round(next_value, 3))
        current_value = next_value
        
    return predictions

def update_data():
    """Update simulated data"""
    try:
        global current_data
        
        # Generate new actual value
        actual = generate_realistic_consumption()
        
        # Generate prediction
        prediction = simulate_prediction(actual)
        
        # Generate future predictions
        future_preds = generate_future_predictions(prediction)
        
        # Update current data
        current_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actual": actual,
            "prediction": prediction,
            "future_predictions": future_preds
        }
        
        logger.info(f"Data updated - Actual: {actual}, Prediction: {prediction}")
        
    except Exception as e:
        logger.error(f"Error updating data: {str(e)}")

# Setup scheduler for data updates
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_data, trigger="interval", seconds=1)
scheduler.start()

@app.route('/current', methods=['GET'])
def get_current_data():
    """API endpoint for current data"""
    return jsonify({
        "status": "success",
        "data": current_data,
        "metadata": {
            "update_frequency": "1 second",
            "prediction_horizon": "6 steps"
        }
    })

@app.route('/forecast', methods=['GET'])
def get_forecast():
    """API endpoint for forecast"""
    return jsonify({
        "status": "success",
        "data": {
            "timestamp": current_data["timestamp"],
            "future_predictions": current_data["future_predictions"]
        }
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """API endpoint for prediction metrics"""
    try:
        actual = current_data["actual"]
        predicted = current_data["prediction"]
        error = abs(actual - predicted) / actual * 100
        
        return jsonify({
            "status": "success",
            "metrics": {
                "timestamp": current_data["timestamp"],
                "error_percentage": round(error, 2),
                "accuracy": round(100 - error, 2)
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5101, debug=True)