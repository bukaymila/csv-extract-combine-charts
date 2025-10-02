# Handles metadata extraction from file paths

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def extract_metadata_from_path(file_path, main_folder_path):
    """
    Extract metadata from the file path and subfolder structure
    
    Args:
        file_path (Path): Path object for the CSV file
        main_folder_path (str): Path to the main folder
        
    Returns:
        dict: Dictionary containing metadata extracted from the path
    """
    try:
        # Extract subfolder names (excluding filename and main folder)
        relative_path = file_path.relative_to(main_folder_path)
        subfolders = list(relative_path.parent.parts)
        
        # Extract filename without extension
        filename = file_path.stem
        
        metadata = {
            'full_path': str(file_path),
            'filename': filename,
            'subfolders': subfolders,
            'parent_folder': str(file_path.parent.name),
            'file_size': file_path.stat().st_size
        }
        
        # Add dynamic fields based on subfolder structure
        for i, folder in enumerate(subfolders):
            metadata[f'subfolder_{i+1}'] = folder
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        return {}