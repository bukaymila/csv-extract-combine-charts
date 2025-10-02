# Handles CSV file processing and table extraction

import pandas as pd
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def find_table_start(file_path, search_term='date', offset=1):
    """
    Find the starting row of the table (offset rows below the search term)
    
    Args:
        file_path (Path): Path to the CSV file
        search_term (str): Term to search for to locate the table
        offset (int): Number of rows below the search term where table starts
        
    Returns:
        int: Row index where the table starts, or -1 if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Look for the search term (case-insensitive)
        for i, line in enumerate(lines):
            if re.search(rf'\b{search_term}\b', line, re.IGNORECASE):
                # Table starts offset rows below this line
                table_start = i + offset
                if table_start < len(lines):
                    logger.info(f"Found table starting at row {table_start + 1}")  # +1 for 1-based indexing
                    return table_start
                else:
                    logger.warning(f"'{search_term}' found at end of file in {file_path.name}")
                    return -1
        
        logger.warning(f"Word '{search_term}' not found in {file_path.name}")
        return -1
        
    except Exception as e:
        logger.error(f"Error finding table start in {file_path}: {e}")
        return -1

def read_csv_file(file_path, metadata, expected_columns=4):
    """
    Read CSV file starting from the table and extract first 4 columns
    
    Args:
        file_path (Path): Path to the CSV file
        metadata (dict): Metadata extracted from the file path
        expected_columns (int): Expected number of columns in the table
        
    Returns:
        tuple: (raw_df, temp_df, rh_df) - Three DataFrames with different data
    """
    try:
        # Find where the table starts
        table_start = find_table_start(file_path)
        
        if table_start == -1:
            logger.warning(f"Could not find table start in {file_path.name}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Read CSV file starting from the table row
        df = pd.read_csv(
            file_path,
            skiprows=table_start,
            encoding='utf-8',  # Adjust encoding if needed
            low_memory=False   # Prevents mixed type warnings
        )
        
        # Check if we have at least the expected columns
        if len(df.columns) < expected_columns:
            logger.warning(
                f"Expected at least {expected_columns} columns but found {len(df.columns)} in {file_path.name}. "
                f"Columns: {list(df.columns)}"
            )
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Extract only the first 4 columns
        df = df.iloc[:, :expected_columns]
        
        # Rename columns to standard names
        df.columns = ["Date", "Time", "Temp", "RH"]
        
        # Add metadata for hierarchical structure
        parent_folder = metadata.get('parent_folder', 'Unknown')
        filename = metadata.get('filename', 'Unknown')
        
        # Create hierarchical column names for raw data
        hierarchical_columns = {}
        for col in df.columns:
            hierarchical_columns[col] = f"{parent_folder}_{filename}_{col}"
        
        raw_df = df.rename(columns=hierarchical_columns)
        
        # Create separate DataFrames for Temp and RH
        temp_df = df[["Date", "Time", "Temp"]].copy()
        temp_df.columns = ["Date", "Time", f"{parent_folder}_{filename}_Temp"]
        
        rh_df = df[["Date", "Time", "RH"]].copy()
        rh_df.columns = ["Date", "Time", f"{parent_folder}_{filename}_RH"]
        
        logger.info(f"Successfully read {len(df)} rows from {file_path.name}")
        return raw_df, temp_df, rh_df
        
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()