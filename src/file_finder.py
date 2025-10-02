# Handles finding and managing CSV files

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_csv_files(main_folder_path):
    """
    Recursively find all CSV files in the main folder and its subfolders
    
    Args:
        main_folder_path (str): Path to the main folder
        
    Returns:
        list: List of Path objects for all CSV files found
    """
    try:
        csv_files = list(Path(main_folder_path).rglob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")
        return csv_files
    except Exception as e:
        logger.error(f"Error finding CSV files: {e}")
        return []