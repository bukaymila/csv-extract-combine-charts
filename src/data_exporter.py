# Handles data export functionality

import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

def export_data(raw_df, temp_df, rh_df, output_folder):
    """
    Export the three DataFrames to CSV files in the output folder
    
    Args:
        raw_df (pd.DataFrame): Raw combined data
        temp_df (pd.DataFrame): Temperature data
        rh_df (pd.DataFrame): Relative humidity data
        output_folder (str): Path to the output folder
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Define output file paths
        raw_output_path = os.path.join(output_folder, "Raw.csv")
        temp_output_path = os.path.join(output_folder, "Temp.csv")
        rh_output_path = os.path.join(output_folder, "RH.csv")
        
        # Export each DataFrame
        success = True
        
        if not raw_df.empty:
            raw_df.to_csv(raw_output_path, index=False)
            logger.info(f"Raw data exported successfully to {raw_output_path}")
        else:
            logger.warning("No raw data to export")
            success = False
        
        if not temp_df.empty:
            temp_df.to_csv(temp_output_path, index=False)
            logger.info(f"Temperature data exported successfully to {temp_output_path}")
        else:
            logger.warning("No temperature data to export")
            success = False
        
        if not rh_df.empty:
            rh_df.to_csv(rh_output_path, index=False)
            logger.info(f"RH data exported successfully to {rh_output_path}")
        else:
            logger.warning("No RH data to export")
            success = False
        
        return success
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return False