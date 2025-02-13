import requests
import pandas as pd
import json
from datetime import datetime
import logging
import os

class DataCollector:
    def __init__(self, api_url, historical_data_path):
        self.api_url = api_url
        self.historical_data_path = historical_data_path
        self.logger = logging.getLogger(__name__)
        self.last_timestamp = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(historical_data_path), exist_ok=True)
        
    def fetch_current_data(self):
        """Fetch current data from API"""
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            
            # Check if this is new data
            current_timestamp = data['detailed_data']['timestamp']
            if self.last_timestamp == current_timestamp:
                return None
                
            self.last_timestamp = current_timestamp
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return None
            
    def process_json_data(self, json_data):
        """Process JSON data into DataFrame"""
        try:
            detailed = json_data['detailed_data']
            summary = json_data['summary_data']
            
            data = {
                'timestamp': detailed['timestamp'],
                'floor_1_energy_consumption': detailed['floor_1_energy_consumption'],
                'floor_2_energy_consumption': detailed['floor_2_energy_consumption'],
                'floor_3_energy_consumption': detailed['floor_3_energy_consumption'],
                'total_energy_consumption': summary['total_energy_consumption'],
                'weather_temperature': detailed['weather_temperature'],
                'weather_humidity': detailed['weather_humidity']
            }
            
            df = pd.DataFrame([data])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            return None
            
    def save_to_csv(self, df):
        """Save data to CSV file"""
        try:
            mode = 'a' if os.path.exists(self.historical_data_path) else 'w'
            header = not os.path.exists(self.historical_data_path)
            
            df.to_csv(self.historical_data_path, 
                     mode=mode, 
                     header=header, 
                     index=False)
            
            self.logger.info(f"Data point saved at {df['timestamp'].iloc[0]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            return False