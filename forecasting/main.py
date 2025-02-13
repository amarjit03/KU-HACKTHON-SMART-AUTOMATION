import os
import time
import logging
from logging.handlers import RotatingFileHandler
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Import local modules
from src.data_collector import DataCollector
from src.forecaster import EnergyForecaster
from src.evaluator import Evaluator
from config import *

def setup_logging():
    """Setup logging configuration"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def make_prediction(historical_df, current_data, forecaster, evaluator):
    """Make predictions with proper error handling"""
    try:
        if len(historical_df) < SEQUENCE_LENGTH:
            return None
            
        # Prepare sequence
        sequence = forecaster.prepare_sequence(historical_df)
        if sequence is None or len(sequence) == 0:
            return None
            
        # Make prediction
        predictions = forecaster.predict(sequence[-1:], FORECAST_STEPS)
        if predictions is None:
            return None
            
        # Get actual value
        actual = current_data['summary_data']['total_energy_consumption']
        predicted = predictions[0]
        
        # Evaluate prediction
        is_accurate = evaluator.track_error(
            current_data['detailed_data']['timestamp'],
            actual,
            predicted
        )
        
        return {
            'timestamp': current_data['detailed_data']['timestamp'],
            'actual': round(float(actual), 3),
            'predictions': [round(float(p), 3) for p in predictions],
            'is_accurate': is_accurate
        }
        
    except Exception as e:
        logging.error(f"Error in prediction pipeline: {str(e)}")
        return None

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting energy consumption forecasting service...")
    
    # Create required directories
    for directory in [DATA_DIR, MODEL_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    try:
        # Initialize components
        collector = DataCollector(API_URL, HISTORICAL_DATA_PATH)
        forecaster = EnergyForecaster(SEQUENCE_LENGTH)
        evaluator = Evaluator(ERROR_THRESHOLD, ERROR_TRACKING_PATH)
        
        logger.info("All components initialized successfully")
        prediction_counter = 0
        
        while True:
            try:
                # Fetch current data
                current_data = collector.fetch_current_data()
                
                if current_data:
                    # Process and save data
                    df = collector.process_json_data(current_data)
                    if df is not None:
                        collector.save_to_csv(df)
                        prediction_counter += 1
                        
                        # Make predictions every 60 seconds
                        if prediction_counter >= 60:
                            historical_df = pd.read_csv(HISTORICAL_DATA_PATH)
                            result = make_prediction(
                                historical_df,
                                current_data,
                                forecaster,
                                evaluator
                            )
                            
                            if result:
                                logger.info(f"Prediction Results: {json.dumps(result, indent=2)}")
                            prediction_counter = 0
                
                time.sleep(POLLING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Shutting down forecasting service...")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise

if __name__ == "__main__":
    main()