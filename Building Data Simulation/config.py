# config.py
import os

class Config:
    # Base directory of the project
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Data directory configuration
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DETAILED_DATA_FILE = os.path.join(DATA_DIR, 'building_detailed_data.csv')
    SUMMARY_DATA_FILE = os.path.join(DATA_DIR, 'building_summary_data.csv')
    
    # Flask configuration
    DEBUG = True
    PORT = 5000
    HOST = '0.0.0.0'
    
    # Weather API configuration
    # WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'YOUR_API_KEY')  # Get from environment variable
    WEATHER_API_KEY = "206fb1817346b7dd52f067c66447aa1a"
    WEATHER_UPDATE_INTERVAL = 600  # 10 minutes
    DEFAULT_CITY = 'Raipur'
    
    # Building configuration
    FLOORS = 3
    MIN_TEMPERATURE = 18
    MAX_TEMPERATURE = 28
    MIN_HUMIDITY = 30
    MAX_HUMIDITY = 70
    MAX_OCCUPANCY = 8
    
    # Data retention configuration
    MAX_DATA_FILE_SIZE = 1000000000  # 1GB in bytes
    DATA_RETENTION_DAYS = 30  # Number of days to keep data
    
    # Logging configuration
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'simulation.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def init_directories(cls):
        """Initialize necessary directories"""
        directories = [cls.DATA_DIR, cls.LOG_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)