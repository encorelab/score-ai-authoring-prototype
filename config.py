import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# Paths to configuration files
ACTIVITY_CONFIG_FILE = "activity_config_template.json"
ACTIVITY_CONFIG_SCHEMA_FILE = "activity_config_schema.json"

def load_activity_config():
    """Loads the activity configuration from the JSON file."""
    with open(ACTIVITY_CONFIG_FILE, "r") as f:
        return json.load(f)
    
def load_activity_config_schema():
    """Loads the activity configuration schema from the JSON file."""
    with open(ACTIVITY_CONFIG_SCHEMA_FILE, "r") as f:
        return json.load(f)
