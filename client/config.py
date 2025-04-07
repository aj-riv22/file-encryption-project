import os
from pathlib import Path

class Config:
    # Server settings
    SERVER_URL = "http://localhost:8000"
    
    # Local settings
    DEFAULT_SYNC_DIR = str(Path.home() / "CloudStorage")
    
    # Create sync directory if it doesn't exist
    os.makedirs(DEFAULT_SYNC_DIR, exist_ok=True) 