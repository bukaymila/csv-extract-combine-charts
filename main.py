# Main application entry point

import sys
import os
import matplotlib

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Add this to handle matplotlib data files when packaged
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    matplotlib.use('Agg')
    os.environ['MATPLOTLIBDATA'] = os.path.join(sys._MEIPASS, 'mpl-data')

def main():
    """
    Main function to run the application
    """
    # Check if GUI should be used (no command line arguments)
    if len(sys.argv) == 1:
        try:
            from src.customtkinter_gui import run_customtkinter_gui
            run_customtkinter_gui()
        except ImportError:
            # Fallback to Tkinter if CustomTkinter is not available
            print("CustomTkinter not found, falling back to Tkinter")
            from src.tkinter_gui import run_tkinter_gui
            run_tkinter_gui()
    else:
        # Command line mode
        import logging
        from config.settings import setup_logging, DEFAULT_MAIN_FOLDER
        from src.utils import process_all_files
        from src.data_exporter import export_data
        
        # Parse command line arguments
        main_folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MAIN_FOLDER
        output_folder = sys.argv[2] if len(sys.argv) > 2 else "output"
        
        # Setup logging
        logger = setup_logging()
        
        try:
            logger.info("Starting CSV data extraction process")
            
            # Process all files
            raw_df, temp_df, rh_df = process_all_files(main_folder)
            
            # Export results
            success = export_data(raw_df, temp_df, rh_df, output_folder)
            if success:
                logger.info(f"Data extraction completed successfully. Output saved to {output_folder}")
            else:
                logger.error("Failed to export some data")
                
        except Exception as e:
            logger.error(f"Unexpected error in main process: {e}")

if __name__ == "__main__":
    main()