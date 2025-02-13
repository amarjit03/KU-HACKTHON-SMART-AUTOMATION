import numpy as np
import pandas as pd
from datetime import datetime
import time
import threading
import os
import requests
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Appliance:
    def __init__(self, name: str, active_power: float, standby_power: float, 
                 usage_pattern: Dict[str, float], typical_duration: int,
                 power_factor: float = 1.0):
        self.name = name
        self.active_power = active_power
        self.standby_power = standby_power
        self.usage_pattern = usage_pattern
        self.typical_duration = typical_duration
        self.power_factor = power_factor
        self.is_on = False
        self.start_time = None
        self.cycle_time = 0

    def update_state(self, hour: int) -> float:
        try:
            current_time = time.time()
            if not self.is_on:
                hour_prob = self.usage_pattern.get(str(hour), 0.1)
                if np.random.random() < hour_prob:
                    self.is_on = True
                    self.start_time = current_time
                    self.cycle_time = 0
                    return self.active_power
                return self.standby_power
            else:
                usage_time = current_time - self.start_time
                actual_duration = self.typical_duration * (1 + np.random.normal(0, 0.1))
                if usage_time > (actual_duration * 60):
                    self.is_on = False
                    return self.standby_power
                self.cycle_time += 1
                cycle_factor = 0.8 + 0.4 * np.sin(self.cycle_time / 30)
                return self.active_power * cycle_factor
        except Exception as e:
            logger.error(f"Error updating appliance state: {e}")
            return self.standby_power

class BuildingSimulation:
    def __init__(self):
        self.floors = 3
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, 'building_detailed_data.csv')
        self.summary_file = os.path.join(self.data_dir, 'building_summary_data.csv')
        self._initialize_simulation()

    def _initialize_simulation(self):
        self.running = False
        self.weather_api_key = None
        self.last_weather_update = 0
        self.weather_data = None
        self.weather_update_interval = 100
        self.thread = None
        self.appliances = self._initialize_appliances()
        self._initialize_files()

    def _get_usage_patterns(self) -> Dict[str, Dict[str, float]]:
        return {
            "morning": {str(h): 0.8 if 6 <= h <= 9 else 0.3 if 9 <= h <= 11 else 0.1 for h in range(24)},
            "evening": {str(h): 0.9 if 18 <= h <= 21 else 0.5 if 17 <= h <= 22 else 0.1 for h in range(24)},
            "cooking": {str(h): 0.8 if h in [7, 8, 12, 13, 18, 19] else 0.3 if h in [9, 14, 20] else 0.1 for h in range(24)},
            "all_day": {str(h): 0.3 for h in range(24)}
        }

    def _get_appliance_profiles(self) -> Dict:
        patterns = self._get_usage_patterns()
        return {
            "Refrigerator": {"active": 0.150, "standby": 0.150, "pattern": patterns["all_day"], "duration": 20, "power_factor": 0.95},
            "TV_LED_55": {"active": 0.160, "standby": 0.003, "pattern": patterns["evening"], "duration": 180, "power_factor": 0.9},
            "Washing_Machine": {"active": 0.500, "standby": 0.005, "pattern": patterns["morning"], "duration": 45, "power_factor": 0.8},
            "Air_Conditioner": {"active": 1.800, "standby": 0.015, "pattern": patterns["all_day"], "duration": 30, "power_factor": 0.85},
            "Electric_Kettle": {"active": 1.500, "standby": 0.000, "pattern": patterns["morning"], "duration": 5, "power_factor": 1.0},
            "Coffee_Machine": {"active": 1.200, "standby": 0.001, "pattern": patterns["morning"], "duration": 10, "power_factor": 0.98},
            "Gaming_PC": {"active": 0.500, "standby": 0.002, "pattern": patterns["evening"], "duration": 120, "power_factor": 0.95},
            "Smart_Speaker": {"active": 0.008, "standby": 0.002, "pattern": patterns["all_day"], "duration": 60, "power_factor": 0.95},
            "Security_Camera": {"active": 0.015, "standby": 0.010, "pattern": patterns["all_day"], "duration": 1440, "power_factor": 0.90},
            "Robot_Vacuum": {"active": 0.030, "standby": 0.002, "pattern": patterns["morning"], "duration": 120, "power_factor": 0.85},
            "Smart_Doorbell": {"active": 0.005, "standby": 0.002, "pattern": patterns["all_day"], "duration": 1440, "power_factor": 0.95},
            "Hair_Dryer": {"active": 1.800, "standby": 0.000, "pattern": patterns["morning"], "duration": 10, "power_factor": 1.0}
        }



    def _initialize_appliances(self) -> Dict[int, List[Appliance]]:
        """Initialize appliances for each floor"""
        appliances = {}
        profiles = self._get_appliance_profiles()
        
        for floor in range(1, self.floors + 1):
            appliances[floor] = [
                Appliance(
                    name=name,
                    active_power=data["active"],
                    standby_power=data["standby"],
                    usage_pattern=data["pattern"],
                    typical_duration=data["duration"],
                    power_factor=data["power_factor"]
                )
                for name, data in profiles.items()
            ]
        return appliances

    def _initialize_files(self):
        """Initialize CSV files with headers"""
        # Create headers for detailed data file
        detailed_headers = ['timestamp']
        for floor in range(1, self.floors + 1):
            floor_headers = [
                f'floor_{floor}_temperature',
                f'floor_{floor}_humidity',
                f'floor_{floor}_occupancy',
                f'floor_{floor}_energy_consumption',
                f'floor_{floor}_water_usage'
            ]
            for appliance in self.appliances[floor]:
                floor_headers.append(f'floor_{floor}_{appliance.name.lower()}_power')
            detailed_headers.extend(floor_headers)
        
        # Add weather headers
        weather_headers = [
            'weather_temperature',
            'weather_humidity',
            'weather_condition',
            'weather_wind_speed'
        ]
        detailed_headers.extend(weather_headers)
        
        # Create detailed data file if it doesn't exist
        if not os.path.exists(self.data_file):
            pd.DataFrame(columns=detailed_headers).to_csv(self.data_file, index=False)
        
        # Create headers for summary file
        summary_headers = [
            'timestamp',
            'total_occupancy',
            'total_energy_consumption',
            'total_water_usage',
            'average_temperature',
            'average_humidity',
            'weather_temperature',
            'peak_energy_floor',
            'total_appliance_consumption'
        ]
        
        # Create summary file if it doesn't exist
        if not os.path.exists(self.summary_file):
            pd.DataFrame(columns=summary_headers).to_csv(self.summary_file, index=False)

    def update_weather(self):
        """Update weather data from API or use default values"""
        try:
            current_time = time.time()
            if current_time - self.last_weather_update > self.weather_update_interval:
                if self.weather_api_key:
                    url = f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={self.weather_api_key}&units=metric"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        self.weather_data = {
                            'temperature': data['main']['temp'],
                            'humidity': data['main']['humidity'],
                            'condition': data['weather'][0]['main'],
                            'wind_speed': data['wind']['speed']
                        }
                        self.last_weather_update = current_time
                        logger.info("Weather data updated successfully")
                else:
                    self._use_default_weather()
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            self._use_default_weather()

    def _use_default_weather(self):
        """Set default weather data"""
        self.weather_data = {
            'temperature': 20,
            'humidity': 50,
            'condition': 'Clear',
            'wind_speed': 5
        }

    def generate_temperature(self, floor: int) -> float:
        """Generate temperature for a specific floor"""
        outside_temp = self.weather_data['temperature'] if self.weather_data else 20
        floor_factor = 0.5 * (floor - 1)  # Higher floors are slightly warmer
        time_variation = np.sin(time.time() / 3600) * 2  # Daily temperature cycle
        random_variation = np.random.normal(0, 0.5)  # Random fluctuations
        return outside_temp + floor_factor + time_variation + random_variation

    def generate_humidity(self, floor: int) -> float:
        """Generate humidity for a specific floor"""
        outside_humidity = self.weather_data['humidity'] if self.weather_data else 50
        time_variation = np.sin(time.time() / 3600) * 5
        random_variation = np.random.normal(0, 3)
        return min(max(outside_humidity + time_variation + random_variation, 30), 60)

    def generate_occupancy(self, floor: int) -> int:
        """Generate occupancy for a specific floor"""
        hour = datetime.now().hour
        
        # Peak evening hours
        if 17 <= hour <= 22:
            base_occupancy = np.random.poisson(4)
        # Working hours
        elif 9 <= hour <= 16:
            base_occupancy = np.random.poisson(2)
        # Night hours
        else:
            base_occupancy = np.random.poisson(1)
            
        return max(0, min(base_occupancy, 8))

    def generate_energy_consumption(self, floor: int, temperature: float, occupancy: int) -> float:
        """Calculate energy consumption based on various factors"""
        # Base load for miscellaneous small appliances
        base_consumption = 0.2
        
        # HVAC energy based on temperature difference from comfort zone (20-24°C)
        temp_factor = 0
        if temperature < 20:
            temp_factor = (20 - temperature) * 0.15  # Heating
        elif temperature > 24:
            temp_factor = (temperature - 24) * 0.2   # Cooling
        
        # Occupancy affects base energy usage
        occupancy_factor = occupancy * 0.1
        
        # Time of day factor
        hour = datetime.now().hour
        time_factor = 0.1 if 23 <= hour <= 5 else 0.3
        
        # Random variation (±5%)
        random_variation = np.random.normal(0, 0.05)
        
        total = base_consumption + temp_factor + occupancy_factor + time_factor
        return total * (1 + random_variation)

    def generate_water_usage(self, floor: int, occupancy: int) -> float:
        """Calculate water usage based on time and occupancy"""
        hour = datetime.now().hour
        
        # Base usage for different times of day
        if 6 <= hour <= 9:  # Morning peak
            base_usage = 0.5
        elif 17 <= hour <= 22:  # Evening peak
            base_usage = 0.4
        elif 23 <= hour <= 5:  # Night
            base_usage = 0.1
        else:  # Regular daytime
            base_usage = 0.3
        
        occupancy_factor = occupancy * 0.2
        random_variation = np.random.normal(0, 0.05)
        return max(0, (base_usage + occupancy_factor) * (1 + random_variation))

    def generate_building_data(self) -> Tuple[Dict, Dict]:
        """Generate complete building data including all measurements"""
        try:
            self.update_weather()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_hour = datetime.now().hour
            
            detailed_data = {'timestamp': timestamp}
            summary_data = {
                'timestamp': timestamp,
                'total_occupancy': 0,
                'total_energy_consumption': 0,
                'total_water_usage': 0,
                'total_appliance_consumption': 0
            }
            
            temperatures = []
            humidities = []
            floor_energy = {}
            
            # Generate data for each floor
            for floor in range(1, self.floors + 1):
                temperature = self.generate_temperature(floor)
                humidity = self.generate_humidity(floor)
                occupancy = self.generate_occupancy(floor)

                # Continuation of generate_building_data method...
                
                # Calculate appliance consumption for each appliance
                appliance_consumption = 0
                for appliance in self.appliances[floor]:
                    power = appliance.update_state(current_hour)
                    appliance_consumption += power
                    detailed_data[f'floor_{floor}_{appliance.name.lower()}_power'] = round(power, 3)
                
                # Calculate total energy and water consumption
                energy = self.generate_energy_consumption(floor, temperature, occupancy) + appliance_consumption
                water = self.generate_water_usage(floor, occupancy)
                
                # Update floor-specific data
                floor_data = {
                    f'floor_{floor}_temperature': round(temperature, 2),
                    f'floor_{floor}_humidity': round(humidity, 2),
                    f'floor_{floor}_occupancy': occupancy,
                    f'floor_{floor}_energy_consumption': round(energy, 3),
                    f'floor_{floor}_water_usage': round(water, 3)
                }
                detailed_data.update(floor_data)
                
                # Update summary calculations
                summary_data['total_occupancy'] += occupancy
                summary_data['total_energy_consumption'] += energy
                summary_data['total_water_usage'] += water
                summary_data['total_appliance_consumption'] += appliance_consumption
                
                temperatures.append(temperature)
                humidities.append(humidity)
                floor_energy[floor] = energy
            
            # Add weather data to detailed data
            if self.weather_data:
                detailed_data.update({
                    'weather_temperature': self.weather_data['temperature'],
                    'weather_humidity': self.weather_data['humidity'],
                    'weather_condition': self.weather_data['condition'],
                    'weather_wind_speed': self.weather_data['wind_speed']
                })
            
            # Complete summary calculations
            summary_data.update({
                'average_temperature': round(np.mean(temperatures), 2),
                'average_humidity': round(np.mean(humidities), 2),
                'weather_temperature': self.weather_data['temperature'] if self.weather_data else None,
                'peak_energy_floor': max(floor_energy, key=floor_energy.get)
            })
            
            return detailed_data, summary_data
        
        except Exception as e:
            logger.error(f"Error generating building data: {e}")
            raise

    def save_data(self, detailed_data: Dict, summary_data: Dict):
        """Save generated data to CSV files"""
        try:
            # Save detailed data
            pd.DataFrame([detailed_data]).to_csv(self.data_file, mode='a', header=False, index=False)
            
            # Save summary data
            pd.DataFrame([summary_data]).to_csv(self.summary_file, mode='a', header=False, index=False)
            
            logger.debug("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise

    def simulation_loop(self):
        """Main simulation loop that runs continuously when simulation is active"""
        logger.info("Simulation loop started")
        while self.running:
            try:
                # Generate and save data
                detailed_data, summary_data = self.generate_building_data()
                self.save_data(detailed_data, summary_data)
                
                # Wait for 30 seconds before next iteration
                time.sleep(30)
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                self.running = False
                break

    def start(self):
        """Start the simulation"""
        if not self.running:
            logger.info("Starting simulation")
            self.running = True
            self.thread = threading.Thread(target=self.simulation_loop)
            self.thread.start()

    def stop(self):
        """Stop the simulation"""
        logger.info("Stopping simulation")
        self.running = False
        if hasattr(self, 'thread') and self.thread is not None:
            self.thread.join()
            self.thread = None

    def set_weather_api_key(self, api_key: str):
        """Set the OpenWeather API key"""
        self.weather_api_key = api_key
        logger.info("Weather API key set successfully")

    def get_simulation_status(self) -> Dict:
        """Get current simulation status"""
        return {
            "running": self.running,
            "data_file": self.data_file,
            "summary_file": self.summary_file,
            "weather_api_configured": bool(self.weather_api_key),
            "floors": self.floors,
            "appliances_per_floor": len(self.appliances[1]) if self.appliances else 0
        }

    def get_total_consumption(self) -> Dict:
        """Get total energy and water consumption"""
        try:
            summary_df = pd.read_csv(self.summary_file)
            return {
                "total_energy": summary_df['total_energy_consumption'].sum(),
                "total_water": summary_df['total_water_usage'].sum(),
                "average_occupancy": summary_df['total_occupancy'].mean(),
                "peak_energy_consumption": summary_df['total_energy_consumption'].max()
            }
        except Exception as e:
            logger.error(f"Error calculating total consumption: {e}")
            return {}

    def cleanup(self):
        """Cleanup resources before shutting down"""
        try:
            self.stop()
            logger.info("Simulation cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")