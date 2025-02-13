# utils.py

def get_usage_patterns():
    """Return predefined usage patterns for appliances"""
    morning_pattern = {
        str(h): 0.8 if 6 <= h <= 9 else 
               0.3 if 9 <= h <= 11 else 
               0.1 for h in range(24)
    }
    
    evening_pattern = {
        str(h): 0.9 if 18 <= h <= 21 else
               0.5 if 17 <= h <= 22 else
               0.1 for h in range(24)
    }
    
    cooking_pattern = {
        str(h): 0.8 if h in [7, 8, 12, 13, 18, 19] else
               0.3 if h in [9, 14, 20] else
               0.1 for h in range(24)
    }
    
    all_day_pattern = {str(h): 0.3 for h in range(24)}
    
    return {
        'morning': morning_pattern,
        'evening': evening_pattern,
        'cooking': cooking_pattern,
        'all_day': all_day_pattern
    }

def get_appliance_data():
    """Return predefined appliance configurations"""
    patterns = get_usage_patterns()
    
    return {
        "Refrigerator": {
            "active": 0.150,
            "standby": 0.150,
            "pattern": patterns['all_day'],
            "duration": 20,
            "power_factor": 0.95
        },
        "TV_LED_55": {
            "active": 0.160,
            "standby": 0.003,
            "pattern": patterns['evening'],
            "duration": 180,
            "power_factor": 0.9
        },
        # Add more appliances here...
    }

def get_default_weather():
    """Return default weather data when API is not available"""
    return {
        'temperature': 20,
        'humidity': 50,
        'condition': 'Clear',
        'wind_speed': 5
    }