"""
Centralized logging configuration.
Provides a standard logger with rotating file handling and console output.
"""

import logging
import logging.handlers
import os

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log file path
LOG_FILE = os.path.join(LOG_DIR, "system_events.log")

def setup_logger(name: str):
    """
    Sets up a logger with:
    1. RotatingFileHandler (max 5MB, keep 3 backups)
    2. StreamHandler (console output)
    3. JSON-like formatting for easy parsing
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times if logger is reused
    if logger.hasHandlers():
        return logger
        
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
    )
    
    # File Handler (Rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_recent_logs(lines: int = 50) -> list[str]:
    """Reads the last N lines from the log file."""
    if not os.path.exists(LOG_FILE):
        return ["Log file does not exist yet."]
        
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            # Simple approach: read all and slice (safe for 5MB files)
            # For strict efficiency with HUGE files, use seek()
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception as e:
        return [f"Error reading log file: {e}"]
