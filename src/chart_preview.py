# Chart preview functionality for future use with matplotlib

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def create_sample_chart(dataframe, chart_type='bar'):
    """
    Create a sample chart from the dataframe (for future use)
    
    Args:
        dataframe (pd.DataFrame): Data to visualize
        chart_type (str): Type of chart to create
        
    Returns:
        str: Base64 encoded image of the chart
    """
    if dataframe.empty:
        return None
    
    try:
        # Sample chart - you'll need to customize this based on your data
        plt.figure(figsize=(8, 6))
        
        if chart_type == 'bar':
            # Example: Count of records by parent folder
            if 'parent_folder' in dataframe.columns:
                counts = dataframe['parent_folder'].value_counts().head(10)
                counts.plot(kind='bar')
                plt.title('Top 10 Parent Folders')
                plt.xlabel('Parent Folder')
                plt.ylabel('Count')
            else:
                # Fallback: just show row count
                plt.text(0.5, 0.5, 'Sample Chart Preview\n\nCustomize based on your data structure', 
                         ha='center', va='center', transform=plt.gca().transAxes)
                plt.title('Data Extraction Complete')
        
        plt.tight_layout()
        
        # Save to bytes buffer and encode as base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return img_str
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None