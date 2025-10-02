# Configuration settings for the application

import logging
from pathlib import Path

# Default paths
DEFAULT_MAIN_FOLDER = "path/to/your/main/folder"
DEFAULT_OUTPUT_FILE = "combined_data.csv"

# Logging configuration
def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('csv_extraction.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Other configuration constants
SUPPORTED_OUTPUT_FORMATS = ['csv', 'parquet', 'excel']
TABLE_START_OFFSET = 2  # Rows below 'date' where table starts
EXPECTED_COLUMNS = 4    # Expected number of columns in the table