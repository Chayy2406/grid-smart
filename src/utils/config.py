import yaml
import os

def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return default config
        return {
            "map": {
                "city": "Tempe, AZ",
                "network_type": "drive",
                "simplify": True
            },
            "traffic": {
                "api_key": "",
                "update_interval": 300
            },
            "routing": {
                "default_algorithm": "a_star",
                "default_travel_mode": "car"
            },
            "visualization": {
                "default_map_zoom": 14,
                "show_traffic_colors": True
            }
        }