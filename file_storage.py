import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import json
import datetime
from pathlib import Path
import threading

class FileStorageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local File Storage")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Storage directories
        self.base_dir = Path.home() / "FileStorage"
        self.all_files_dir = self.base_dir / "All_Files"
        self.pen_drive_dir = self.base_dir / "Pen_Drive"
        self.logs_file = self.base_dir / "activity_logs.json"
        
        # Create directories
        self.all_files_dir.mkdir(parents=True, exist_ok=True)
        self.pen_drive_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.selected_files = {"all": [], "pen": []}
        self.select_mode = {"all": False, "pen": False}
        
        # Load logs
        self.logs = self.load_logs()
        
        self.setup_ui()
        self.refresh_file_lists()
        self.log_activity("system", "Application started", "")
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Local File Storage", 
            font=('Helvetica', 20, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        subtitle = ttk.Label(
            main_frame, 
            text="Manage files across All Files and Pen Drive locations",
            font=('Helvetica', 10)
        )
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # === All Files Section ===
        all_files_frame = ttk.LabelFrame(main_frame, text="All Files", padding="10")
        all_files_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        all_files_frame.columnconfigure(0, weight=1)
        all_files_frame.rowconfigure(1, weight=1)
        
        # File count
        self.all_files_count = ttk.Label(all_files_frame, text="0 files")
        self.all_files_count.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # File list
        self.all_files_listbox = tk.Listbox(
            all_files_frame, 
            selectmode=tk.MULTIPLE,
            height=15,
            font=('Consolas', 10)
        )
        self.all_files_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        all_scroll = ttk.Scrollbar(all_files_frame, orient=tk.VERTICAL, command=self.all_files_listbox.yview)
        all_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.all_files_listbox.configure(yscrollcommand=all_scroll.set)
        
        # Bind click for selection
        self.all_files_listbox.bind('<Button-1>', lambda e: self.on_file_click(e, 'all'))
        self.all_files_listbox.bind('<Double-Button-1>', lambda e: self.preview_file('all'))
        
        # Buttons
        all_btn_frame = ttk.Frame(all_files_frame)
        all_btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(
            all_btn_frame, 
            text="Upload Files", 
            command=lambda: self.upload_files('all')
        ).pack(side=tk.LEFT, padx=2)
        
        self.all_select_btn = ttk.Button(
            all_btn_frame, 
            text="Select Files", 
            command=lambda: self.toggle_select_mode('all')
        )
        self.all_select_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            all_btn_frame, 
            text="Preview", 
            command=lambda: self.preview_file('all')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            all_btn_frame, 
            text="Delete", 
            command=lambda: self.delete_file('all')
        ).pack(side=tk.LEFT, padx=2)
        
        # === Transfer Controls ===
        transfer_frame = ttk.Frame(main_frame)
        transfer_frame.grid(row=2, column=1, padx=10)
        
        ttk.Button(
            transfer_frame, 
            text="Copy to Pen Drive →", 
            command=lambda: self.copy_files('all', 'pen')
        ).pack(pady=5)
        
        ttk.Button(
            transfer_frame, 
            text="← Copy to All Files", 
            command=lambda: self.copy_files('pen', 'all')
        ).pack(pady=5)
        
        ttk.Separator(transfer_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(
            transfer_frame, 
            text="Move to Pen Drive →", 
            command=lambda: self.move_files('all', 'pen')
        ).pack(pady=5)
        
        ttk.Button(
            transfer_frame, 
            text="← Move to All Files", 
            command=lambda: self.move_files('pen', 'all')
        ).pack(pady=5)
        
        # === Pen Drive Section ===
        pen_drive_frame = ttk.LabelFrame(main_frame, text="Pen Drive", padding="10")
        pen_drive_frame.grid(row=2, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        pen_drive_frame.columnconfigure(0, weight=1)
        pen_drive_frame.rowconfigure(1, weight=1)
        
        # File count
        self.pen_drive_count = ttk.Label(pen_drive_frame, text="0 files")
        self.pen_drive_count.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # File list
        self.pen_drive_listbox = tk.Listbox(
            pen_drive_frame, 
            selectmode=tk.MULTIPLE,
            height=15,
            font=('Consolas', 10)
        )
        self.pen_drive_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        pen_scroll = ttk.Scrollbar(pen_drive_frame, orient=tk.VERTICAL, command=self.pen_drive_listbox.yview)
        pen_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.pen_drive_listbox.configure(yscrollcommand=pen_scroll.set)
        
        # Bind click for selection
        self.pen_drive_listbox.bind('<Button-1>', lambda e: self.on_file_click(e, 'pen'))
        self.pen_drive_listbox.bind('<Double-Button-1>', lambda e: self.preview_file('pen'))
        
        # Buttons
        pen_btn_frame = ttk.Frame(pen_drive_frame)
        pen_btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(
            pen_btn_frame, 
            text="Upload Files", 
            command=lambda: self.upload_files('pen')
        ).pack(side=tk.LEFT, padx=2)
        
        self.pen_select_btn = ttk.Button(
            pen_btn_frame, 
            text="Select Files", 
            command=lambda: self.toggle_select_mode('pen')
        )
        self.pen_select_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            pen_btn_frame, 
            text="Preview", 
            command=lambda: self.preview_file('pen')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            pen_btn_frame, 
            text="Delete", 
            command=lambda: self.delete_file('pen')
        ).pack(side=tk.LEFT, padx=2)
        
        # === Logs Section ===
        logs_frame = ttk.LabelFrame(main_frame, text="Activity Logs", padding="10")
        logs_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame, 
            height=10, 
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log buttons
        logs_btn_frame = ttk.Frame(logs_frame)
        logs_btn_frame.grid(row=1, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(
            logs_btn_frame, 
            text="Clear Logs", 
            command=self.clear_logs
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            logs_btn_frame, 
            text="Save Logs to File", 
            command=self.save_logs
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            logs_btn_frame, 
            text="Refresh", 
            command=self.refresh_file_lists
        ).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def on_file_click(self, event, location):
        if not self.select_mode[location]:
            # Clear other selections if not in select mode
            pass
            
    def toggle_select_mode(self, location):
        self.select_mode[location] = not self.select_mode[location]
        
        if location == 'all':
            btn = self.all_select_btn
            listbox = self.all_files_listbox
        else:
            btn = self.pen_select_btn
            listbox = self.pen_drive_listbox
            
        if self.select_mode[location]:
            btn.configure(text="Done Selecting")
            listbox.configure(selectmode=tk.MULTIPLE)
        else:
            btn.configure(text="Select Files")
            listbox.configure(selectmode=tk.SINGLE)
            self.selected_files[location] = []
            
    def get_selected_indices(self, location):
        if location == 'all':
            return self.all_files_listbox.curselection()
        else:
            return self.pen_drive_listbox.curselection()
            
    def get_file_path(self, filename, location):
        if location == 'all':
            return self.all_files_dir / filename
        else:
            return self.pen_drive_dir / filename
            
    def get_files_in_location(self, location):
        if location == 'all':
            return [f for f in self.all_files_dir.iterdir() if f.is_file()]
        else:
            return [f for f in self.pen_drive_dir.iterdir() if f.is_file()]
            
    def refresh_file_lists(self):
        # Clear lists
        self.all_files_listbox.delete(0, tk.END)
        self.pen_drive_listbox.delete(0, tk.END)
        
        # Populate All Files
        all_files = self.get_files_in_location('all')
        for f in sorted(all_files, key=lambda x: x.name.lower()):
            size = self.format_size(f.stat().st_size)
            self.all_files_listbox.insert(tk.END, f"{f.name} ({size})")
            
        # Populate Pen Drive
        pen_files = self.get_files_in_location('pen')
        for f in sorted(pen_files, key=lambda x: x.name.lower()):
            size = self.format_size(f.stat().st_size)
            self.pen_drive_listbox.insert(tk.END, f"{f.name} ({size})")
            
        # Update counts
        self.all_files_count.configure(text=f"{len(all_files)} files")
        self.pen_drive_count.configure(text=f"{len(pen_files)} files")
        
        # Refresh logs display
        self.refresh_logs_display()
        
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def upload_files(self, location):
        files = filedialog.askopenfilenames(
            title=f"Select files to upload to {'All Files' if location == 'all' else 'Pen Drive'}",
            filetypes=[
                ("All files", "*.*"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Documents", "*.pdf *.doc *.docx *.txt"),
                ("Videos", "*.mp4 *.avi *.mkv *.mov"),
            ]
        )
        
        if not files:
            return
            
        dest_dir = self.all_files_dir if location == 'all' else self.pen_drive_dir
        location_name = "All Files" if location == 'all' else "Pen Drive"
        
        for file_path in files:
            try:
                src = Path(file_path)
                dest = dest_dir / src.name
                
                # Handle duplicate names
                counter = 1
                while dest.exists():
                    stem = src.stem
                    suffix = src.suffix
                    dest = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                    
                shutil.copy2(src, dest)
                self.log_activity("add", f"File uploaded to {location_name}", src.name)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload {src.name}: {str(e)}")
                
        self.refresh_file_lists()
        self.status_bar.configure(text=f"Uploaded {len(files)} file(s) to {location_name}")
        
    def delete_file(self, location):
        indices = self.get_selected_indices(location)
        if not indices:
            messagebox.showwarning("No Selection", "Please select a file to delete")
            return
            
        files = self.get_files_in_location(location)
        location_name = "All Files" if location == 'all' else "Pen Drive"
        
        # Get selected filenames
        selected_files = []
        for idx in indices:
            selected_files.append(files[idx])
            
        # Confirm deletion
        if len(selected_files) == 1:
            msg = f"Are you sure you want to delete '{selected_files[0].name}'?"
        else:
            msg = f"Are you sure you want to delete {len(selected_files)} files?"
            
        if not messagebox.askyesno("Confirm Delete", msg):
            return
            
        for file_path in selected_files:
            try:
                file_path.unlink()
                self.log_activity("delete", f"File deleted from {location_name}", file_path.name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {file_path.name}: {str(e)}")
                
        self.refresh_file_lists()
        self.status_bar.configure(text=f"Deleted {len(selected_files)} file(s) from {location_name}")
        
    def copy_files(self, from_loc, to_loc):
        indices = self.get_selected_indices(from_loc)
        if not indices:
            messagebox.showwarning("No Selection", f"Please select files to copy from {'All Files' if from_loc == 'all' else 'Pen Drive'}")
            return
            
        from_files = self.get_files_in_location(from_loc)
        to_dir = self.all_files_dir if to_loc == 'all' else self.pen_drive_dir
        from_name = "All Files" if from_loc == 'all' else "Pen Drive"
        to_name = "All Files" if to_loc == 'all' else "Pen Drive"
        
        copied = 0
        for idx in indices:
            src = from_files[idx]
            dest = to_dir / src.name
            
            # Handle duplicate names
            counter = 1
            original_dest = dest
            while dest.exists():
                stem = src.stem
                suffix = src.suffix
                dest = to_dir / f"{stem}_{counter}{suffix}"
                counter += 1
                
            try:
                shutil.copy2(src, dest)
                self.log_activity("copy", f"File copied from {from_name} to {to_name}", src.name)
                copied += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy {src.name}: {str(e)}")
                
        self.refresh_file_lists()
        self.status_bar.configure(text=f"Copied {copied} file(s) from {from_name} to {to_name}")
        
    def move_files(self, from_loc, to_loc):
        indices = self.get_selected_indices(from_loc)
        if not indices:
            messagebox.showwarning("No Selection", f"Please select files to move from {'All Files' if from_loc == 'all' else 'Pen Drive'}")
            return
            
        from_files = self.get_files_in_location(from_loc)
        to_dir = self.all_files_dir if to_loc == 'all' else self.pen_drive_dir
        from_name = "All Files" if from_loc == 'all' else "Pen Drive"
        to_name = "All Files" if to_loc == 'all' else "Pen Drive"
        
        moved = 0
        for idx in indices:
            src = from_files[idx]
            dest = to_dir / src.name
            
            # Handle duplicate names
            counter = 1
            while dest.exists():
                stem = src.stem
                suffix = src.suffix
                dest = to_dir / f"{stem}_{counter}{suffix}"
                counter += 1
                
            try:
                shutil.move(str(src), str(dest))
                self.log_activity("move", f"File moved from {from_name} to {to_name}", src.name)
                moved += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move {src.name}: {str(e)}")
                
        self.refresh_file_lists()
        self.status_bar.configure(text=f"Moved {moved} file(s) from {from_name} to {to_name}")
        
    def preview_file(self, location):
        indices = self.get_selected_indices(location)
        if not indices:
            messagebox.showwarning("No Selection", "Please select a file to preview")
            return
            
        if len(indices) > 1:
            messagebox.showwarning("Multiple Selection", "Please select only one file to preview")
            return
            
        files = self.get_files_in_location(location)
        file_path = files[indices[0]]
        location_name = "All Files" if location == 'all' else "Pen Drive"
        
        self.log_activity("view", f"File viewed in {location_name}", file_path.name)
        
        # Open with default application
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {str(e)}")
            
    def log_activity(self, action, details, filename):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details,
            "filename": filename
        }
        self.logs.insert(0, log_entry)
        self.save_logs_to_file()
        self.refresh_logs_display()
        
    def refresh_logs_display(self):
        self.logs_text.delete(1.0, tk.END)
        
        for log in self.logs[:100]:  # Show last 100 logs
            timestamp = datetime.datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            action = log["action"].upper()
            details = log["details"]
            filename = log["filename"]
            
            log_line = f"[{timestamp}] [{action:8}] {details}"
            if filename:
                log_line += f": {filename}"
            log_line += "\n"
            
            self.logs_text.insert(tk.END, log_line)
            
    def load_logs(self):
        if self.logs_file.exists():
            try:
                with open(self.logs_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_logs_to_file(self):
        with open(self.logs_file, 'w') as f:
            json.dump(self.logs, f, indent=2)
            
    def clear_logs(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all logs?"):
            self.logs = []
            self.save_logs_to_file()
            self.refresh_logs_display()
            self.log_activity("system", "Logs cleared", "")
            
    def save_logs(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"activity_logs_{datetime.datetime.now().strftime('%Y%m%d')}"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                for log in self.logs:
                    timestamp = datetime.datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    action = log["action"].upper()
                    details = log["details"]
                    filename = log["filename"]
                    
                    line = f"[{timestamp}] [{action}] {details}"
                    if filename:
                        line += f": {filename}"
                    f.write(line + "\n")
                    
            messagebox.showinfo("Success", f"Logs saved to {file_path}")

def main():
    root = tk.Tk()
    app = FileStorageApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
