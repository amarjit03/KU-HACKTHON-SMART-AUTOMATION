from flask import Flask, jsonify
from flask_cors import CORS
import logging
import random
from datetime import datetime
from models import BuildingSimulation


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Simplified CORS configuration


# Initialize simulation
try:
    simulation = BuildingSimulation()
    simulation.start()
    # Optionally set API key
    # simulation.set_weather_api_key('YOUR_API_KEY')
except Exception as e:
    logger.error(f"Failed to initialize simulation: {e}")
    simulation = None



@app.route('/start', methods=['GET'])
def start_simulation():
    try:
        if simulation:
            simulation.start()
            return jsonify({"status": "Simulation started"})
        return jsonify({"error": "Simulation not initialized"}), 500
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop', methods=['GET'])
def stop_simulation():
    try:
        if simulation:
            simulation.stop()
            return jsonify({"status": "Simulation stopped"})
        return jsonify({"error": "Simulation not initialized"}), 500
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    try:
        if simulation:
            return jsonify({
                "running": simulation.running,
                "detailed_data_file": simulation.data_file,
                "summary_data_file": simulation.summary_file
            })
        return jsonify({"error": "Simulation not initialized"}), 500
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/current', methods=['GET'])
def get_current_data():
    try:
        if simulation and simulation.running:
            detailed_data, summary_data = simulation.generate_building_data()
            response = jsonify({
                "detailed_data": detailed_data,
                "summary_data": summary_data
            })
            return response
        return jsonify({"error": "Simulation not running"}), 503
    except Exception as e:
        logger.error(f"Error getting current data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5100)


