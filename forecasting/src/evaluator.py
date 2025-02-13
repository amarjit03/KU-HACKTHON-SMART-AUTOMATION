import pandas as pd
import numpy as np
import logging
import os

class Evaluator:
    def __init__(self, error_threshold, error_tracking_path):
        self.error_threshold = error_threshold
        self.error_tracking_path = error_tracking_path
        self.logger = logging.getLogger(__name__)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(error_tracking_path), exist_ok=True)
        
    def calculate_error(self, actual, predicted):
        """Calculate percentage error"""
        return abs(actual - predicted) / actual * 100
        
    def track_error(self, timestamp, actual, predicted):
        """Track and save significant errors"""
        try:
            error = self.calculate_error(actual, predicted)
            
            if error > self.error_threshold:
                error_data = {
                    'timestamp': timestamp,
                    'actual': actual,
                    'predicted': predicted,
                    'error_percentage': error
                }
                
                df = pd.DataFrame([error_data])
                mode = 'a' if os.path.exists(self.error_tracking_path) else 'w'
                header = not os.path.exists(self.error_tracking_path)
                
                df.to_csv(self.error_tracking_path, 
                         mode=mode, 
                         header=header, 
                         index=False)
                
                self.logger.warning(f"High prediction error: {error:.2f}%")
                
            return error <= self.error_threshold
            
        except Exception as e:
            self.logger.error(f"Error tracking error: {str(e)}")
            return False