import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import os
import time
import keyboard
from datetime import datetime
import sys
import threading

class TitleSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Speedrun Timer")
        self.root.geometry("300x350")
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(default='speedrun_timer.ico')
        except:
            pass
        
        self.list_frame = ttk.Frame(self.root)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(self.list_frame, text="Select Speedrun Title:", font=("Arial", 10)).pack()
        
        self.title_listbox = tk.Listbox(self.list_frame, height=10, font=("Arial", 10))
        self.title_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.title_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.title_listbox.config(yscrollcommand=scrollbar.set)
        
        self.add_button = ttk.Button(self.root, text="Add New Title", command=self.add_title, width=15)
        self.add_button.pack(pady=5)
        
        self.start_button = ttk.Button(self.root, text="Start Timer", command=self.start_timer, state=tk.DISABLED, width=15)
        self.start_button.pack(pady=5)
        
        self.title_listbox.bind("<<ListboxSelect>>", self.on_title_select)
        self.titles = self.load_titles()
        self.update_title_list()
        
        if not self.titles:
            self.title_listbox.insert(tk.END, "No titles available - add one below")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.root.destroy()
        sys.exit(0)
    
    def load_titles(self):
        try:
            if os.path.exists("speedrun_titles.json"):
                with open("speedrun_titles.json", "r") as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_titles(self):
        try:
            with open("speedrun_titles.json", "w") as f:
                json.dump(self.titles, f)
        except:
            pass
    
    def update_title_list(self):
        self.title_listbox.delete(0, tk.END)
        for title in self.titles:
            self.title_listbox.insert(tk.END, title)
    
    def add_title(self):
        new_title = simpledialog.askstring("New Title", "Enter speedrun title:")
        if new_title and new_title.strip():
            new_title = new_title.strip()
            if new_title not in self.titles:
                self.titles.append(new_title)
                self.save_titles()
                self.update_title_list()
                
                index = self.titles.index(new_title)
                self.title_listbox.selection_clear(0, tk.END)
                self.title_listbox.selection_set(index)
                self.title_listbox.activate(index)
                self.start_button.config(state=tk.NORMAL)
            else:
                messagebox.showwarning("Duplicate Title", "This title already exists!")
    
    def on_title_select(self, event):
        if self.title_listbox.curselection():
            selected_text = self.title_listbox.get(self.title_listbox.curselection()[0])
            if selected_text != "No titles available - add one below":
                self.start_button.config(state=tk.NORMAL)
    
    def start_timer(self):
        selected = self.title_listbox.curselection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a title first!")
            return
            
        title = self.title_listbox.get(selected[0])
        if title != "No titles available - add one below":
            self.root.destroy()
            timer_root = tk.Tk()
            SpeedrunTimer(timer_root, title)
            timer_root.mainloop()

class SpeedrunTimer:
    def __init__(self, root, title):
        self.root = root
        self.title = title
        self.root.title(f"Speedrun Timer - {title}")
        self.root.geometry("200x200")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        try:
            self.root.iconbitmap(default='speedrun_timer.ico')
        except:
            pass
        
        self.running = False
        self.start_time = 0
        self.paused_time = 0
        self.segments = []
        self.last_segment_time = 0
        self.personal_best = None
        
        self.keybinds = {
            "start_pause": "f4",
            "split": "f3",
            "reset": "f5"
        }
        
        self.load_keybinds()
        
        self.create_widgets()
        self.setup_hotkeys()
        self.load_run_data()
        self.update_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        self.timer_frame = ttk.Frame(self.root)
        self.timer_frame.pack(pady=(5, 0))
        
        self.title_label = ttk.Label(self.timer_frame, text=self.title, font=("Arial", 9, "bold"), foreground="#e74c3c")
        self.title_label.pack()
        
        self.timer_label = ttk.Label(self.timer_frame, text="00:00.000", font=("Courier New", 20, "bold"), foreground="#3498db")
        self.timer_label.pack()
        
        self.pb_label = ttk.Label(self.timer_frame, text="PB: --:--.---", font=("Courier New", 8), foreground="#27ae60")
        self.pb_label.pack(pady=(0, 5))
        
        self.segments_frame = ttk.Frame(self.root)
        self.segments_frame.pack(fill=tk.X, padx=5, pady=0)
        
        self.segments_text = tk.Text(self.segments_frame, height=3, width=20, font=("Courier New", 7), state=tk.DISABLED)
        self.segments_text.pack(fill=tk.X)
        
        self.clear_btn_frame = ttk.Frame(self.segments_frame)
        self.clear_btn_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.clear_btn = ttk.Button(self.clear_btn_frame, text="🗑Clear Segments", width=2, command=self.clear_segments)
        self.clear_btn.pack(fill=tk.X, padx=5, pady=0)
        
        keybinds_frame = ttk.Frame(self.root)
        keybinds_frame.pack(fill=tk.X, padx=5, pady=(3, 0))
        
        key_text = f"{self.keybinds['start_pause'].upper()}:Start/Pause  {self.keybinds['split'].upper()}:Split  {self.keybinds['reset'].upper()}:Reset"
        self.keybinds_label = ttk.Label(keybinds_frame, text=key_text, font=("Arial", 7))
        self.keybinds_label.pack(side=tk.LEFT)
        
        self.settings_btn = ttk.Button(keybinds_frame, text="⚙", width=3, command=self.open_keybind_config)
        self.settings_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.top_var = tk.BooleanVar(value=True)
        top_check = ttk.Checkbutton(self.root, text="Always on Top", variable=self.top_var, command=self.toggle_always_on_top)
        top_check.pack(pady=1)
    
    def setup_hotkeys(self):
        def hotkey_thread():
            keyboard.add_hotkey(self.keybinds['start_pause'], self.toggle_timer)
            keyboard.add_hotkey(self.keybinds['split'], self.add_segment)
            keyboard.add_hotkey(self.keybinds['reset'], self.reset_timer)
        
        self.hotkey_thread = threading.Thread(target=hotkey_thread, daemon=True)
        self.hotkey_thread.start()
    
    def open_keybind_config(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configure Keybinds")
        config_window.geometry("250x180")
        config_window.resizable(False, False)
        config_window.attributes("-topmost", True)
        
        ttk.Label(config_window, text="Click button to change keybind", font=("Arial", 9)).pack(pady=5)
        
        start_frame = ttk.Frame(config_window)
        start_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(start_frame, text="Start/Pause:").pack(side=tk.LEFT)
        start_btn = ttk.Button(start_frame, text=self.keybinds['start_pause'].upper(), 
                                  command=lambda: self.change_keybind('start_pause', start_btn),
                                  width=12)
        start_btn.pack(side=tk.RIGHT)
        
        split_frame = ttk.Frame(config_window)
        split_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(split_frame, text="Split:").pack(side=tk.LEFT)
        split_btn = ttk.Button(split_frame, text=self.keybinds['split'].upper(), 
                                  command=lambda: self.change_keybind('split', split_btn),
                                  width=12)
        split_btn.pack(side=tk.RIGHT)
        
        reset_frame = ttk.Frame(config_window)
        reset_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(reset_frame, text="Reset:").pack(side=tk.LEFT)
        reset_btn = ttk.Button(reset_frame, text=self.keybinds['reset'].upper(), 
                                  command=lambda: self.change_keybind('reset', reset_btn),
                                  width=12)
        reset_btn.pack(side=tk.RIGHT)
        
        ttk.Button(config_window, text="Close", command=config_window.destroy).pack(pady=10)
    
    def change_keybind(self, action, button):
        button.config(text="Press any key...")
        button.update_idletasks()
        
        key = keyboard.read_key()
        
        self.keybinds[action] = key
        button.config(text=key.upper())
        
        key_text = f"{self.keybinds['start_pause'].upper()}:Start/Pause  {self.keybinds['split'].upper()}:Split  {self.keybinds['reset'].upper()}:Reset"
        self.keybinds_label.config(text=key_text)
        
        self.save_keybinds()
        
        keyboard.unhook_all_hotkeys()
        self.setup_hotkeys()
    
    def load_keybinds(self):
        try:
            if os.path.exists("keybinds.json"):
                with open("keybinds.json", "r") as f:
                    self.keybinds = json.load(f)
        except:
            pass
    
    def save_keybinds(self):
        try:
            with open("keybinds.json", "w") as f:
                json.dump(self.keybinds, f)
        except:
            pass
    
    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.top_var.get())
    
    def clear_segments(self):
        if not self.segments:
            return
        if messagebox.askyesno("Clear Segments", "Are you sure you want to clear all segments?"):
            self.segments = []
            self.last_segment_time = 0
            self.update_segments_display()
    
    def toggle_timer(self):
        if not self.running:
            self.running = True
            if self.start_time == 0:
                self.start_time = time.perf_counter()
            else:
                self.start_time = time.perf_counter() - self.paused_time
        else:
            self.running = False
            self.paused_time = time.perf_counter() - self.start_time
    
    def reset_timer(self):
        if self.running:
            self.running = False
            final_time = time.perf_counter() - self.start_time
        else:
            final_time = self.paused_time
        
        if self.start_time > 0 or self.segments:
            new_pb_detected = False
            if self.personal_best is None or final_time < self.personal_best:
                new_pb_detected = True
                set_pb = messagebox.askyesno("New Personal Best!", f"Your time of {self.format_time(final_time)} is better than your current PB!\nSet as new personal best?")
                if set_pb:
                    self.personal_best = final_time
                    self.pb_label.config(text=f"PB: {self.format_time(self.personal_best)}")
                    self.save_run_data()
            
            save = messagebox.askyesno("Save Run?", "Would you like to save this run?")
            if save:
                self.save_to_text()
            elif new_pb_detected:
                self.save_run_data()
        
        self.start_time = 0
        self.paused_time = 0
        self.timer_label.config(text="00:00.000")
        self.update_segments_display()
    
    def save_to_text(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile=f"{self.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(f"Speedrun: {self.title}\n")
                    if self.personal_best:
                        f.write(f"Personal Best: {self.format_time(self.personal_best)}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("Segment Times:\n")
                    for i, segment in enumerate(self.segments):
                        suffix = "th" if 11 <= i+1 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get((i+1) % 10, "th")
                        f.write(f"{i+1}{suffix}: Segment: {self.format_time(segment['segment_time'])} | Total: {self.format_time(segment['total_time'])}\n")
                    if not self.segments and self.start_time > 0:
                        final_time = time.perf_counter() - self.start_time if self.running else self.paused_time
                        f.write(f"\nTotal Time: {self.format_time(final_time)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
    
    def add_segment(self):
        if not self.running:
            return
        current_time = time.perf_counter() - self.start_time
        segment_time = current_time - self.last_segment_time
        self.last_segment_time = current_time
        self.segments.append({"segment_num": len(self.segments) + 1, "segment_time": segment_time, "total_time": current_time})
        self.update_segments_display()
    
    def update_segments_display(self):
        self.segments_text.config(state=tk.NORMAL)
        self.segments_text.delete(1.0, tk.END)
        for segment in self.segments[-3:]:
            segment_num = segment["segment_num"]
            segment_time = self.format_time(segment["segment_time"])
            total_time = self.format_time(segment["total_time"])
            suffix = "th" if 11 <= segment_num <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(segment_num % 10, "th")
            self.segments_text.insert(tk.END, f"{segment_num}{suffix}: {segment_time} | Total: {total_time}\n")
        self.segments_text.config(state=tk.DISABLED)
        self.segments_text.see(tk.END)
    
    def update_timer(self):
        if self.running:
            current_time = time.perf_counter() - self.start_time
            self.timer_label.config(text=self.format_time(current_time))
        self.root.after(10, self.update_timer)
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:06.3f}"
    
    def load_run_data(self):
        try:
            if os.path.exists("speedrun_data.json"):
                with open("speedrun_data.json", "r") as f:
                    data = json.load(f)
                    if self.title in data:
                        self.segments = data[self.title].get("segments", [])
                        if self.segments:
                            self.last_segment_time = self.segments[-1]["total_time"]
                            self.update_segments_display()
                        if "personal_best" in data[self.title]:
                            self.personal_best = data[self.title]["personal_best"]
                            self.pb_label.config(text=f"PB: {self.format_time(self.personal_best)}")
        except:
            pass
    
    def save_run_data(self):
        try:
            data = {}
            if os.path.exists("speedrun_data.json"):
                with open("speedrun_data.json", "r") as f:
                    data = json.load(f)
            data[self.title] = {"segments": self.segments, "last_segment_time": self.last_segment_time, "personal_best": self.personal_best}
            with open("speedrun_data.json", "w") as f:
                json.dump(data, f)
        except:
            pass
    
    def on_close(self):
        try:
            self.save_run_data()
            self.save_keybinds()
            keyboard.unhook_all_hotkeys()
        finally:
            self.root.destroy()
            sys.exit(0)

def main():
    root = tk.Tk()
    TitleSelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()