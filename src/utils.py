# Utility functions

import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def process_single_file(file_path, main_folder_path):
    """
    Process a single CSV file: extract metadata and read data
    
    Args:
        file_path (Path): Path to the CSV file
        main_folder_path (str): Path to the main folder
        
    Returns:
        tuple: (raw_df, temp_df, rh_df) - Three DataFrames with different data
    """
    from src.metadata_extractor import extract_metadata_from_path
    from src.csv_processor import read_csv_file
    
    metadata = extract_metadata_from_path(file_path, main_folder_path)
    if metadata:
        return read_csv_file(file_path, metadata)
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def process_all_files(main_folder_path):
    """
    Process all CSV files in the main folder and subfolders
    
    Args:
        main_folder_path (str): Path to the main folder
        
    Returns:
        tuple: (raw_df, temp_df, rh_df) - Three combined DataFrames
    """
    from src.file_finder import get_csv_files
    
    csv_files = get_csv_files(main_folder_path)
    
    if not csv_files:
        logger.warning("No CSV files found!")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    raw_data = []
    temp_data = []
    rh_data = []
    
    for i, csv_file in enumerate(csv_files):
        logger.info(f"Processing file {i+1}/{len(csv_files)}: {csv_file.name}")
        
        raw_df, temp_df, rh_df = process_single_file(csv_file, main_folder_path)
        
        if not raw_df.empty:
            raw_data.append(raw_df)
        if not temp_df.empty:
            temp_data.append(temp_df)
        if not rh_df.empty:
            rh_data.append(rh_df)
    
    # Combine all data
    raw_combined = combine_dataframes_horizontally(raw_data)
    temp_combined = combine_dataframes_horizontally(temp_data)
    rh_combined = combine_dataframes_horizontally(rh_data)
    
    return raw_combined, temp_combined, rh_combined

def process_all_files_with_progress(main_folder_path, progress_callback=None):
    """
    Process all CSV files in the main folder and subfolders with progress reporting
    
    Args:
        main_folder_path (str): Path to the main folder
        progress_callback (function): Callback function for progress updates
        
    Returns:
        tuple: (raw_df, temp_df, rh_df) - Three combined DataFrames
    """
    from src.file_finder import get_csv_files
    
    csv_files = get_csv_files(main_folder_path)
    
    if not csv_files:
        logger.warning("No CSV files found!")
        if progress_callback:
            progress_callback(0, 0, "No CSV files found")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    raw_data = []
    temp_data = []
    rh_data = []
    total_files = len(csv_files)
    
    for i, csv_file in enumerate(csv_files):
        if progress_callback:
            progress_callback(i, total_files, f"Processing {csv_file.name}")
        
        logger.info(f"Processing file {i+1}/{total_files}: {csv_file.name}")
        
        raw_df, temp_df, rh_df = process_single_file(csv_file, main_folder_path)
        
        if not raw_df.empty:
            raw_data.append(raw_df)
        if not temp_df.empty:
            temp_data.append(temp_df)
        if not rh_df.empty:
            rh_data.append(rh_df)
    
    # Combine all data
    raw_combined = combine_dataframes_horizontally(raw_data)
    temp_combined = combine_dataframes_horizontally(temp_data)
    rh_combined = combine_dataframes_horizontally(rh_data)
    
    if progress_callback:
        progress_callback(total_files, total_files, "Processing complete")
    
    return raw_combined, temp_combined, rh_combined

def combine_dataframes_horizontally(dataframes):
    """
    Combine DataFrames horizontally with proper alignment
    
    Args:
        dataframes (list): List of DataFrames to combine
        
    Returns:
        pandas.DataFrame: Combined DataFrame
    """
    if not dataframes:
        return pd.DataFrame()
    
    # Find the maximum number of rows
    max_rows = max(len(df) for df in dataframes)
    
    # Align all DataFrames to the same number of rows
    aligned_dfs = []
    for df in dataframes:
        if len(df) < max_rows:
            # Add empty rows to match the maximum
            empty_rows = pd.DataFrame(
                {col: [None] * (max_rows - len(df)) for col in df.columns},
                index=range(len(df), max_rows)
            )
            aligned_df = pd.concat([df, empty_rows])
        else:
            aligned_df = df
        
        aligned_dfs.append(aligned_df)
    
    # Combine all DataFrames horizontally
    combined_df = pd.concat(aligned_dfs, axis=1)
    
    logger.info(f"Combined data shape: {combined_df.shape}")
    return combined_df