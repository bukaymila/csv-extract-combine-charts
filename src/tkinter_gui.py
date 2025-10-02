# Tkinter GUI interface for the CSV Data Extractor

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import threading
import queue

class CSVExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Data Extractor")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('Green.TButton', background='green', foreground='white')
        self.style.configure('Blue.TButton', background='blue', foreground='white')
        self.style.configure('Red.TButton', background='red', foreground='white')
        
        # Variables
        self.main_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        
        # Progress tracking
        self.progress = tk.DoubleVar()
        self.progress_label = tk.StringVar(value="Ready")
        
        # Thread communication
        self.queue = queue.Queue()
        
        self.create_widgets()
        self.check_queue()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="CSV Data Extractor", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Main folder selection
        ttk.Label(main_frame, text="Main Folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.main_folder, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_main_folder).grid(row=2, column=2, padx=5, pady=5)
        
        # Output folder selection
        ttk.Label(main_frame, text="Output Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_folder, width=50).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_folder).grid(row=3, column=2, padx=5, pady=5)
        
        # Info about output files
        info_text = "Output files will be created:\n- Raw.csv (all data)\n- Temp.csv (temperature only)\n- RH.csv (humidity only)"
        ttk.Label(main_frame, text=info_text).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Separator
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Extract Data", command=self.extract_data, 
                  style='Green.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Extraction", command=self.test_extraction,
                  style='Blue.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit,
                  style='Red.TButton').pack(side=tk.LEFT, padx=5)
        
        # Separator
        separator3 = ttk.Separator(main_frame, orient='horizontal')
        separator3.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Progress bar
        ttk.Label(main_frame, textvariable=self.progress_label).grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)
        progress_bar = ttk.Progressbar(main_frame, variable=self.progress, maximum=100)
        progress_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Output console
        ttk.Label(main_frame, text="Output:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.output_text = scrolledtext.ScrolledText(main_frame, width=80, height=15)
        self.output_text.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(11, weight=1)
    
    def browse_main_folder(self):
        folder = filedialog.askdirectory(title="Select Main Folder")
        if folder:
            self.main_folder.set(folder)
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    def extract_data(self):
        if not self.validate_inputs():
            return
        
        # Disable buttons during processing
        self.set_buttons_state(tk.DISABLED)
        self.progress_label.set("Starting extraction...")
        
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
            from src.file_finder import get_csv_files
            from src.csv_processor import find_table_start
            
            csv_files = get_csv_files(main_folder)
            
            if csv_files:
                test_file = csv_files[0]
                table_start = find_table_start(test_file)
                
                message = f"Found {len(csv_files)} CSV files\n"
                message += f"Test file: {test_file.name}\n"
                message += f"Table starts at row: {table_start}\n"
                
                messagebox.showinfo("Test Results", message)
            else:
                messagebox.showinfo("Test Results", "No CSV files found in the selected folder")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during testing: {str(e)}")
    
    def run_extraction(self):
        try:
            main_folder = self.main_folder.get()
            output_folder = self.output_folder.get()
            
            # Import here to avoid circular imports
            from src.utils import process_all_files_with_progress
            from src.data_exporter import export_data
            
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
                    self.output_text.insert(tk.END, message + '\n')
                    self.output_text.see(tk.END)
                
                elif message_type == 'success':
                    message = args[0]
                    messagebox.showinfo("Success", message)
                    self.progress_label.set("Extraction completed successfully")
                    self.set_buttons_state(tk.NORMAL)
                
                elif message_type == 'error':
                    message = args[0]
                    messagebox.showerror("Error", message)
                    self.progress_label.set("Extraction failed")
                    self.set_buttons_state(tk.NORMAL)
                
                elif message_type == 'warning':
                    message = args[0]
                    messagebox.showwarning("Warning", message)
                    self.progress_label.set("Extraction completed with warnings")
                    self.set_buttons_state(tk.NORMAL)
                    
        except queue.Empty:
            pass
        
        # Check again after 100ms
        self.root.after(100, self.check_queue)
    
    def set_buttons_state(self, state):
        """Enable or disable all buttons"""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.state(['!disabled' if state == tk.NORMAL else 'disabled'])
    
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

def run_tkinter_gui():
    """Run the Tkinter GUI application"""
    root = tk.Tk()
    app = CSVExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_tkinter_gui()