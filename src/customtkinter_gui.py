# CustomTkinter GUI interface for CB Data Management

import customtkinter as ctk
from tkinter import filedialog, messagebox
import atexit
import os
from pathlib import Path
import threading
import queue
import sys
import pandas as pd
import matplotlib
from datetime import datetime, timedelta
import numpy as np

# Use Agg backend for better compatibility
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates

# Set appearance mode and color theme
ctk.set_appearance_mode("Dark")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# Set SVG fonttype
plt.rcParams['svg.fonttype'] = 'none'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class CBDataManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CB Data Management")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.iconbitmap(resource_path("img\icons8-cold-96.ico"))
        
        # Variables
        self.main_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        
        # Progress tracking
        self.progress = ctk.DoubleVar(value=0)
        self.progress_label = ctk.StringVar(value="Ready")
        
        # Thread communication
        self.queue = queue.Queue()
        self.after_id = None  # Store after callback ID
        
        # Chart variables
        self.temp_fig = None
        self.rh_fig = None
        self.temp_canvas = None
        self.rh_canvas = None
        self.processed_data = None
        
        # Set up proper cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.cleanup)
        
        self.create_widgets()
        self.check_queue()

    
    def create_widgets(self):
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Title frame
        title_frame = ctk.CTkFrame(self.root, corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="CB Data Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=20)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Add tabs
        self.tabview.add("Data Extraction")
        self.tabview.add("Charting")
        
        # Configure tab grid
        self.tabview.tab("Data Extraction").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Data Extraction").grid_rowconfigure(1, weight=1)
        self.tabview.tab("Charting").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Charting").grid_rowconfigure(0, weight=1)
        
        # Create Data Extraction tab content
        self.create_data_extraction_tab()
        
        # Create Charting tab content (placeholder for now)
        self.create_charting_tab()
        
        # Status bar
        status_frame = ctk.CTkFrame(self.root, corner_radius=0, height=30)
        status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(status_frame, text="Ready", text_color="gray")
        self.status_label.grid(row=0, column=0, sticky="w", padx=20)

    def on_closing(self):
        """Handle window closing event"""
        self.cleanup()
        self.root.quit()
        self.root.destroy()

    def cleanup(self):
        """Clean up resources before closing"""
        # Cancel any pending after callbacks
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        # Close matplotlib figures
        if self.temp_fig:
            plt.close(self.temp_fig)
            self.temp_fig = None
        
        if self.rh_fig:
            plt.close(self.rh_fig)
            self.rh_fig = None
        
        # Clear canvas references
        self.temp_canvas = None
        self.rh_canvas = None
        
        # Clear processed data
        self.processed_data = None
        
        # Clear the queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
    
    def create_data_extraction_tab(self):
        tab = self.tabview.tab("Data Extraction")
        
        # Main content frame
        main_frame = ctk.CTkFrame(tab, corner_radius=10)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(8, weight=1)
        
        # Tab title
        tab_title = ctk.CTkLabel(
            main_frame, 
            text="Data Extraction", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        tab_title.grid(row=0, column=0, columnspan=2, pady=(10, 20))
        
        # Main folder selection
        ctk.CTkLabel(main_frame, text="Main Folder:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=20, pady=(10, 5)
        )
        
        folder_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        folder_frame.grid(row=1, column=1, sticky="ew", padx=20, pady=(10, 5))
        folder_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkEntry(folder_frame, textvariable=self.main_folder).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(folder_frame, text="Browse", width=80, command=self.browse_main_folder).grid(
            row=0, column=1
        )
        
        # Output folder selection
        ctk.CTkLabel(main_frame, text="Output Folder:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="w", padx=20, pady=5
        )
        
        output_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        output_frame.grid(row=2, column=1, sticky="ew", padx=20, pady=5)
        output_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkEntry(output_frame, textvariable=self.output_folder).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(output_frame, text="Browse", width=80, command=self.browse_output_folder).grid(
            row=0, column=1
        )
        
        # Info about output files
        info_text = "Output files will be created:\n• Raw.csv (all data)\n• Temp.csv (temperature only)\n• RH.csv (humidity only)"
        info_label = ctk.CTkLabel(main_frame, text=info_text, justify="left")
        info_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=10)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(
            button_frame, 
            text="Extract Data", 
            command=self.extract_data,
            fg_color="#2AA876",
            hover_color="#228B69",
            width=120
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Test Extraction", 
            command=self.test_extraction,
            fg_color="#3B8ED0",
            hover_color="#3679B5",
            width=120
        ).pack(side="left", padx=10)
        
        # Progress section
        progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(progress_frame, textvariable=self.progress_label).grid(
            row=0, column=0, sticky="w"
        )
        
        ctk.CTkProgressBar(progress_frame, variable=self.progress).grid(
            row=1, column=0, sticky="ew", pady=(5, 0)
        )
        
        # Output console
        ctk.CTkLabel(main_frame, text="Output:", font=ctk.CTkFont(weight="bold")).grid(
            row=6, column=0, sticky="w", padx=20, pady=(20, 5)
        )
        
        self.output_text = ctk.CTkTextbox(main_frame, height=200)
        self.output_text.grid(
            row=7, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 20)
        )
    
    def create_charting_tab(self):
        tab = self.tabview.tab("Charting")
        
        # Configure tab grid
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        # Control frame for buttons and options
        control_frame = ctk.CTkFrame(tab, height=100)
        control_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_propagate(False)
        
        # Data file selection
        ctk.CTkLabel(control_frame, text="Data File:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 5)
        )
        
        self.data_file_var = ctk.StringVar(value="")
        file_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        file_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=(20, 5))
        file_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkEntry(file_frame, textvariable=self.data_file_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(file_frame, text="Browse", width=80, command=self.browse_data_file).grid(
            row=0, column=1
        )
        
        # Chart options
        options_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        options_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=5)
        
        ctk.CTkButton(
            options_frame,
            text="Load and Process Data",
            command=self.load_and_process_data,
            fg_color="#3B8ED0",
            hover_color="#3679B5",
            width=180
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            options_frame,
            text="Generate Charts",
            command=self.generate_charts,
            fg_color="#2AA876",
            hover_color="#228B69",
            width=120
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            options_frame,
            text="Export Charts",
            command=self.export_charts,
            fg_color="#D35B5B",
            hover_color="#B84A4A",
            width=120
        ).pack(side="left")
        
        # Chart display frame
        chart_frame = ctk.CTkFrame(tab)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)
        
        # Create notebook for charts
        self.chart_notebook = ctk.CTkTabview(chart_frame)
        self.chart_notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add tabs for temperature and humidity charts
        self.chart_notebook.add("Temperature Chart")
        self.chart_notebook.add("Humidity Chart")
        
        # Configure chart tabs
        self.chart_notebook.tab("Temperature Chart").grid_columnconfigure(0, weight=1)
        self.chart_notebook.tab("Temperature Chart").grid_rowconfigure(0, weight=1)
        self.chart_notebook.tab("Humidity Chart").grid_columnconfigure(0, weight=1)
        self.chart_notebook.tab("Humidity Chart").grid_rowconfigure(0, weight=1)
        
        # Initialize chart variables
        self.temp_fig = None
        self.rh_fig = None
        self.temp_canvas = None
        self.rh_canvas = None
        self.processed_data = None
    
    def load_charting_data(self):
        """Placeholder function for charting data loading"""
        messagebox.showinfo("Info", "Charting functionality will be implemented in the next phase.")
        self.status_label.configure(text="Charting tab selected - functionality coming soon")
    
    def browse_main_folder(self):
        folder = filedialog.askdirectory(title="Select Main Folder")
        if folder:
            self.main_folder.set(folder)
            self.status_label.configure(text=f"Main folder: {folder}")
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            self.status_label.configure(text=f"Output folder: {folder}")
    
    def extract_data(self):
        if not self.validate_inputs():
            return
        
        # Disable buttons during processing
        self.set_buttons_state("disabled")
        self.progress_label.set("Starting extraction...")
        self.status_label.configure(text="Extracting data...")
        
        # Clear output text
        self.output_text.delete("1.0", "end")
        
        # Run extraction in a separate thread
        thread = threading.Thread(target=self.run_extraction)
        thread.daemon = True
        thread.start()
    
    def test_extraction(self):
        main_folder = self.main_folder.get()
        if not main_folder or not os.path.exists(main_folder):
            messagebox.showerror("Error", "Please select a valid main folder")
            return
        
        try:
            # Add the src directory to the path
            src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
            if src_path not in sys.path:
                sys.path.append(src_path)
            
            from file_finder import get_csv_files
            from csv_processor import find_table_start
            
            csv_files = get_csv_files(main_folder)
            
            if csv_files:
                test_file = csv_files[0]
                table_start = find_table_start(test_file)
                
                message = f"Found {len(csv_files)} CSV files\n"
                message += f"Test file: {test_file.name}\n"
                message += f"Table starts at row: {table_start}\n"
                
                messagebox.showinfo("Test Results", message)
                self.status_label.configure(text="Test completed successfully")
            else:
                messagebox.showinfo("Test Results", "No CSV files found in the selected folder")
                self.status_label.configure(text="No CSV files found")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during testing: {str(e)}")
            self.status_label.configure(text="Test failed")
    
    def run_extraction(self):
        try:
            main_folder = self.main_folder.get()
            output_folder = self.output_folder.get()
            
            # Add the src directory to the path
            src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
            if src_path not in sys.path:
                sys.path.append(src_path)
            
            from utils import process_all_files_with_progress
            from data_exporter import export_data
            
            # Process files with progress updates
            def progress_callback(current, total, message):
                progress_percent = (current / total) * 100 if total > 0 else 0
                self.queue.put(('progress', progress_percent, message))
            
            raw_df, temp_df, rh_df = process_all_files_with_progress(
                main_folder, 
                progress_callback=progress_callback
            )
            
            # Export data
            success = export_data(raw_df, temp_df, rh_df, output_folder)
            if success:
                self.queue.put(('success', f'Data extraction completed successfully!\nOutput saved to {output_folder}'))
            else:
                self.queue.put(('error', 'Failed to export some data'))
                
        except Exception as e:
            self.queue.put(('error', f'An error occurred: {str(e)}'))
    
    def check_queue(self):
        """Check for messages from the worker thread"""
        try:
            while True:
                message_type, *args = self.queue.get_nowait()
                
                if message_type == 'progress':
                    progress, message = args
                    self.progress.set(progress)
                    self.progress_label.set(message)
                    self.output_text.insert("end", message + '\n')
                    self.output_text.see("end")
                    self.status_label.configure(text=message)
                
                elif message_type == 'success':
                    message = args[0]
                    messagebox.showinfo("Success", message)
                    self.progress_label.set("Extraction completed successfully")
                    self.status_label.configure(text="Extraction completed successfully")
                    self.set_buttons_state("normal")
                
                elif message_type == 'error':
                    message = args[0]
                    messagebox.showerror("Error", message)
                    self.progress_label.set("Extraction failed")
                    self.status_label.configure(text="Extraction failed")
                    self.set_buttons_state("normal")
                
                elif message_type == 'warning':
                    message = args[0]
                    messagebox.showwarning("Warning", message)
                    self.progress_label.set("Extraction completed with warnings")
                    self.status_label.configure(text="Extraction completed with warnings")
                    self.set_buttons_state("normal")
                    
        except queue.Empty:
            pass
        
        # Check again after 100ms and store the after ID
        self.after_id = self.root.after(100, self.check_queue)
    
    def set_buttons_state(self, state):
        """Enable or disable all buttons"""
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                if state == "normal":
                    widget.configure(state="normal")
                else:
                    widget.configure(state="disabled")
    
    def validate_inputs(self):
        main_folder = self.main_folder.get()
        output_folder = self.output_folder.get()
        
        if not main_folder or not os.path.exists(main_folder):
            messagebox.showerror("Error", "Please select a valid main folder")
            return False
            
        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return False
            
        return True
    
    def browse_data_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.data_file_var.set(file_path)
            self.status_label.configure(text=f"Data file: {os.path.basename(file_path)}")

    def load_and_process_data(self):
        file_path = self.data_file_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid data file")
            return
        
        try:
            self.status_label.configure(text="Loading and processing data...")
            
            # Load the CSV file
            df = pd.read_csv(file_path)
            
            # Extract temperature and humidity columns
            temp_columns = [col for col in df.columns if 'Temp' in col]
            rh_columns = [col for col in df.columns if 'RH' in col]
            
            if not temp_columns or not rh_columns:
                messagebox.showerror("Error", "No temperature or humidity data found in the file")
                return
            
            # Calculate time intervals (10-minute intervals in hours)
            num_rows = len(df)
            time_intervals = np.arange(0, num_rows * 10/60, 10/60)  # 10 minutes = 10/60 hours
            
            # Prepare data for plotting
            self.processed_data = {
                'time_intervals': time_intervals,
                'temperature_data': df[temp_columns],
                'humidity_data': df[rh_columns],
                'temp_columns': temp_columns,
                'rh_columns': rh_columns
            }
            
            self.status_label.configure(text=f"Data loaded: {len(temp_columns)} temp columns, {len(rh_columns)} RH columns")
            messagebox.showinfo("Success", f"Data loaded successfully!\n"
                                        f"Temperature columns: {len(temp_columns)}\n"
                                        f"Humidity columns: {len(rh_columns)}\n"
                                        f"Time points: {num_rows}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_label.configure(text="Data loading failed")

    def generate_charts(self):
        if self.processed_data is None:
            messagebox.showerror("Error", "Please load and process data first")
            return
        
        try:
            self.status_label.configure(text="Generating charts...")
            
            # Generate temperature chart
            self.create_temperature_chart()
            
            # Generate humidity chart
            self.create_humidity_chart()
            
            self.status_label.configure(text="Charts generated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate charts: {str(e)}")
            self.status_label.configure(text="Chart generation failed")

    def create_temperature_chart(self):
    # Clear previous chart and figures
        for widget in self.chart_notebook.tab("Temperature Chart").winfo_children():
            widget.destroy()
        
        if self.temp_fig:
            plt.close(self.temp_fig)
        
        # Create figure with explicit reference
        self.temp_fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot each temperature column
        time_intervals = self.processed_data['time_intervals']
        temp_data = self.processed_data['temperature_data']
        
        for col in self.processed_data['temp_columns']:
            # Get the label (folder_filename part)
            label_parts = col.split('_')
            label = '_'.join(label_parts[:-1])  # Remove the 'Temp' part
            ax.plot(time_intervals, temp_data[col], label=label, alpha=0.7, linewidth=1.5)
        
        # Customize chart
        ax.set_xlabel('Time (hours)', fontsize=12)
        ax.set_ylabel('Temperature', fontsize=12)
        ax.set_title('Temperature vs Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format x-axis to show hours properly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}'))
        
        plt.tight_layout()
        
        # Embed in tkinter with proper cleanup handling
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, self.chart_notebook.tab("Temperature Chart"))
        self.temp_canvas.draw()
        self.temp_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_humidity_chart(self):
        # Clear previous chart and figures
        for widget in self.chart_notebook.tab("Humidity Chart").winfo_children():
            widget.destroy()
        
        if self.rh_fig:
            plt.close(self.rh_fig)
        
        # Create figure with explicit reference
        self.rh_fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot each humidity column
        time_intervals = self.processed_data['time_intervals']
        rh_data = self.processed_data['humidity_data']
        
        for col in self.processed_data['rh_columns']:
            # Get the label (folder_filename part)
            label_parts = col.split('_')
            label = '_'.join(label_parts[:-1])  # Remove the 'RH' part
            ax.plot(time_intervals, rh_data[col], label=label, alpha=0.7, linewidth=1.5)
        
        # Customize chart
        ax.set_xlabel('Time (hours)', fontsize=12)
        ax.set_ylabel('Relative Humidity (%)', fontsize=12)
        ax.set_title('Relative Humidity vs Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format x-axis to show hours properly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}'))
        
        plt.tight_layout()
        
        # Embed in tkinter with proper cleanup handling
        self.rh_canvas = FigureCanvasTkAgg(self.rh_fig, self.chart_notebook.tab("Humidity Chart"))
        self.rh_canvas.draw()
        self.rh_canvas.get_tk_widget().pack(fill='both', expand=True)

    def export_charts(self):
        if self.temp_fig is None or self.rh_fig is None:
            messagebox.showerror("Error", "Please generate charts first")
            return
        
        try:
            # Ask for export directory
            export_dir = filedialog.askdirectory(title="Select Export Directory")
            if not export_dir:
                return
            
            # Export temperature chart
            temp_path = os.path.join(export_dir, "temperature_chart.svg")
            self.temp_fig.savefig(temp_path, dpi=300, bbox_inches='tight', format="svg")
            
            # Export humidity chart
            rh_path = os.path.join(export_dir, "humidity_chart.svg")
            self.rh_fig.savefig(rh_path, dpi=300, bbox_inches='tight', format="svg")
            
            # Export data summary
            summary_path = os.path.join(export_dir, "chart_data_summary.txt")
            with open(summary_path, 'w') as f:
                f.write("Chart Data Summary\n")
                f.write("=================\n\n")
                f.write(f"Temperature columns: {len(self.processed_data['temp_columns'])}\n")
                f.write(f"Humidity columns: {len(self.processed_data['rh_columns'])}\n")
                f.write(f"Time points: {len(self.processed_data['time_intervals'])}\n")
                f.write(f"Total duration: {self.processed_data['time_intervals'][-1]:.2f} hours\n\n")
                
                f.write("Temperature Columns:\n")
                for col in self.processed_data['temp_columns']:
                    f.write(f"  - {col}\n")
                
                f.write("\nHumidity Columns:\n")
                for col in self.processed_data['rh_columns']:
                    f.write(f"  - {col}\n")
            
            self.status_label.configure(text=f"Charts exported to {export_dir}")
            messagebox.showinfo("Success", f"Charts exported successfully to:\n{export_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export charts: {str(e)}")
            self.status_label.configure(text="Chart export failed")

def run_customtkinter_gui():
    """Run the CustomTkinter GUI application"""
    root = ctk.CTk()
    app = CBDataManagementGUI(root)
    
    try:
        root.mainloop()
    finally:
        # Ensure cleanup even if mainloop crashes
        app.cleanup()
        # Close any remaining matplotlib figures
        plt.close('all')

if __name__ == "__main__":
    run_customtkinter_gui()