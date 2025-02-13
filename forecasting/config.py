import os
from datetime import datetime

# API Configuration
API_URL = "http://127.0.0.1:5100/current"
POLLING_INTERVAL = 1  # 1 second

# Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# File Paths
HISTORICAL_DATA_PATH = os.path.join(DATA_DIR, 'historical_data.csv')
ERROR_TRACKING_PATH = os.path.join(DATA_DIR, 'error_tracking.csv')
MODEL_PATH = os.path.join(MODEL_DIR, 'lstm_model.h5')
LOG_FILE = os.path.join(LOG_DIR, f'energy_forecast_{datetime.now().strftime("%Y%m%d")}.log')

# Model Parameters
SEQUENCE_LENGTH = 100
FORECAST_STEPS = 6
ERROR_THRESHOLD = 0.15

# Feature Columns
FEATURE_COLUMNS = [
    'floor_1_energy_consumption',
    'floor_2_energy_consumption',
    'floor_3_energy_consumption',
    'total_energy_consumption',
    'weather_temperature',
    'weather_humidity'
]