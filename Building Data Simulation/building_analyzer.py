from flask import Flask, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildingAnalyzer:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.detailed_file = os.path.join(data_dir, "building_detailed_data.csv")
        self.summary_file = os.path.join(data_dir, "building_summary_data.csv")
        self.floors = 3

    def read_data(self, num_rows=600):
        """Read CSV with robust error handling"""
        try:
            # Read CSV with flexible parsing options
            df = pd.read_csv(
                self.detailed_file,
                on_bad_lines='skip',  # Skip problematic lines
                dtype={
                    'timestamp': str,
                    'weather_condition': str
                }
            )
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            
            # Get most recent records
            df = df.sort_values('timestamp', ascending=False).head(num_rows)
            return df
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            raise

    def get_latest_data(self):
        """Get latest building data for dashboard"""
        try:
            df = self.read_data()
            if df.empty:
                return self._create_empty_response()

            # Get latest row
            latest = df.iloc[0]
            response = {
                "building_status": {
                    "total_energy": 0,
                    "total_water": 0,
                    "total_occupancy": 0,
                    "average_temperature": 0,
                    "average_humidity": 0
                },
                "floors": {},
                "weather": {
                    "temperature": round(float(latest.get('weather_temperature', 0)), 1),
                    "humidity": round(float(latest.get('weather_humidity', 0)), 1),
                    "condition": str(latest.get('weather_condition', 'Unknown')),
                    "wind_speed": round(float(latest.get('weather_wind_speed', 0)), 1)
                },
                "timestamp": latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            }

            # Process each floor
            temps = []
            humids = []
            for floor in range(1, self.floors + 1):
                floor_data = {
                    "temperature": round(float(latest.get(f'floor_{floor}_temperature', 0)), 1),
                    "humidity": round(float(latest.get(f'floor_{floor}_humidity', 0)), 1),
                    "occupancy": int(latest.get(f'floor_{floor}_occupancy', 0)),
                    "energy": round(float(latest.get(f'floor_{floor}_energy_consumption', 0)), 2),
                    "water": round(float(latest.get(f'floor_{floor}_water_usage', 0)), 2),
                    "appliances": self._get_floor_appliances(latest, floor)
                }
                
                response["floors"][f"floor_{floor}"] = floor_data
                response["building_status"]["total_energy"] += floor_data["energy"]
                response["building_status"]["total_water"] += floor_data["water"]
                response["building_status"]["total_occupancy"] += floor_data["occupancy"]
                temps.append(floor_data["temperature"])
                humids.append(floor_data["humidity"])

            # Calculate building averages
            response["building_status"]["average_temperature"] = round(np.mean(temps), 1)
            response["building_status"]["average_humidity"] = round(np.mean(humids), 1)
            response["building_status"]["total_energy"] = round(response["building_status"]["total_energy"], 2)
            response["building_status"]["total_water"] = round(response["building_status"]["total_water"], 2)

            # Add historical trends
            response["trends"] = self._calculate_trends(df)

            return response

        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return self._create_empty_response()

    def _get_floor_appliances(self, row, floor):
        """Extract appliance data for a floor"""
        appliances = {}
        # Get all columns that match the pattern floor_X_*_power
        power_cols = [col for col in row.index if col.startswith(f'floor_{floor}_') and col.endswith('_power')]
        
        for col in power_cols:
            # Extract appliance name from column name
            appliance = col.replace(f'floor_{floor}_', '').replace('_power', '')
            appliances[appliance] = round(float(row.get(col, 0)), 3)
        
        return appliances

    def _calculate_trends(self, df, periods=12):
        """Calculate trends for the dashboard"""
        try:
            # Resample data to 5-minute intervals
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            trends = {
                "energy": [],
                "temperature": [],
                "occupancy": []
            }
            
            # Calculate total energy consumption trend
            for floor in range(1, self.floors + 1):
                if f'floor_{floor}_energy_consumption' in df.columns:
                    trends["energy"].extend([{
                        "time": index.strftime('%H:%M'),
                        "value": round(float(value), 2),
                        "floor": floor
                    } for index, value in df[f'floor_{floor}_energy_consumption'].head(periods).items()])
                
                if f'floor_{floor}_temperature' in df.columns:
                    trends["temperature"].extend([{
                        "time": index.strftime('%H:%M'),
                        "value": round(float(value), 1),
                        "floor": floor
                    } for index, value in df[f'floor_{floor}_temperature'].head(periods).items()])
                
                if f'floor_{floor}_occupancy' in df.columns:
                    trends["occupancy"].extend([{
                        "time": index.strftime('%H:%M'),
                        "value": int(value),
                        "floor": floor
                    } for index, value in df[f'floor_{floor}_occupancy'].head(periods).items()])

            return trends
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {"energy": [], "temperature": [], "occupancy": []}

    def _create_empty_response(self):
        """Create empty response structure"""
        return {
            "building_status": {
                "total_energy": 0,
                "total_water": 0,
                "total_occupancy": 0,
                "average_temperature": 0,
                "average_humidity": 0
            },
            "floors": {
                f"floor_{floor}": {
                    "temperature": 0,
                    "humidity": 0,
                    "occupancy": 0,
                    "energy": 0,
                    "water": 0,
                    "appliances": {}
                } for floor in range(1, self.floors + 1)
            },
            "weather": {
                "temperature": 0,
                "humidity": 0,
                "condition": "Unknown",
                "wind_speed": 0
            },
            "trends": {
                "energy": [],
                "temperature": [],
                "occupancy": []
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/latest')
def get_latest():
    """API endpoint for getting latest building data"""
    try:
        analyzer = BuildingAnalyzer()
        data = analyzer.get_latest_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)