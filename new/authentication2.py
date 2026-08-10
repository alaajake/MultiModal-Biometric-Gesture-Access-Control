import tkinter as tk
from tkinter import ttk, messagebox
import serial
import subprocess
import json
import sys
import time
from serial.tools import list_ports

USER_DATA_FILE = "user_data.json"

class FingerprintApp:
    def __init__(self, master):
        self.master = master
        master.title("Fingerprint Control System")
        master.geometry("800x600")
        
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 12), padding=6)
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TEntry", font=("Arial", 12))
        
        self.users = self.load_users()
        
        # Main container
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Enrollment Section
        self.enroll_frame = ttk.LabelFrame(self.main_frame, text="User Management")
        self.enroll_frame.pack(fill="x", pady=10)
        
        ttk.Label(self.enroll_frame, text="ID:").grid(row=0, column=0, padx=5)
        self.entry_id = ttk.Entry(self.enroll_frame, width=10)
        self.entry_id.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.enroll_frame, text="Name:").grid(row=0, column=2, padx=5)
        self.entry_name = ttk.Entry(self.enroll_frame, width=25)
        self.entry_name.grid(row=0, column=3, padx=5)
        
        ttk.Button(self.enroll_frame, text="Enroll", command=self.enroll).grid(row=0, column=4, padx=5)
        ttk.Button(self.enroll_frame, text="Delete", command=self.delete).grid(row=0, column=5, padx=5)
        
        # User List
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Registered Users")
        self.list_frame.pack(expand=True, fill="both", pady=10)
        
        self.user_list = tk.Listbox(self.list_frame, font=("Arial", 12), selectmode=tk.SINGLE)
        self.user_list.pack(expand=True, fill="both", padx=5, pady=5)
        self.update_user_list()
        
        # Verification Section
        self.verify_frame = ttk.Frame(self.main_frame)
        self.verify_frame.pack(pady=10)
        
        self.btn_verify = ttk.Button(self.verify_frame, text="Start Verification", command=self.start_verification)
        self.btn_verify.pack(side="left", padx=5)
        
        self.btn_stop = ttk.Button(self.verify_frame, text="Stop Verification", command=self.stop_verification, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        # Status Bar
        self.status_label = ttk.Label(self.main_frame, text="Status: Ready", foreground="black")
        self.status_label.pack(pady=10)
        
        # Serial Setup
        self.verifying = False
        # Instead of auto-detecting, we manually select COM3 for the Arduino.
        self.port = "COM3"
        self.ser = serial.Serial(self.port, 9600, timeout=1)
        self.ser.reset_input_buffer()
        
    def load_users(self):
        try:
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        
    def save_users(self):
        with open(USER_DATA_FILE, "w") as f:
            json.dump(self.users, f, indent=4)
            
    def update_user_list(self):
        self.user_list.delete(0, "end")
        for uid, name in sorted(self.users.items(), key=lambda x: int(x[0])):
            self.user_list.insert("end", f"ID {uid}: {name}")
            
    def send_command(self, cmd):
        self.ser.write(cmd.encode())
        time.sleep(1)
        
    def enroll(self):
        uid = self.entry_id.get()
        name = self.entry_name.get().strip()
        
        if not uid.isdigit() or not name:
            messagebox.showerror("Error", "Valid numeric ID and Name required!")
            return
            
        if uid in self.users:
            messagebox.showerror("Error", "ID already exists!")
            return
            
        self.ser.reset_input_buffer()
        self.send_command(f"E,{uid},{name}\n")
        self.update_status(f"Enrolling {name}... Follow sensor instructions", "blue")
        self.master.after(100, self.check_enroll_response, uid, name)
        
    def check_enroll_response(self, uid, name):
        if self.ser.in_waiting > 0:
            response = self.ser.readline().decode().strip()
            if "Stored!" in response:
                self.users[uid] = name
                self.save_users()
                self.update_user_list()
                self.update_status(f"Success: {name} enrolled", "green")
                self.entry_id.delete(0, "end")
                self.entry_name.delete(0, "end")
            elif "failed" in response.lower():
                self.update_status("Enrollment failed - try again", "red")
            else:
                self.master.after(100, self.check_enroll_response, uid, name)
        else:
            self.master.after(100, self.check_enroll_response, uid, name)
        
    def delete(self):
        uid = self.entry_id.get()
        if not uid.isdigit() or uid not in self.users:
            messagebox.showerror("Error", "Invalid ID!")
            return
            
        self.send_command(f"D,{uid}\n")
        del self.users[uid]
        self.save_users()
        self.update_user_list()
        self.update_status(f"Deleted ID {uid}", "green")
        self.entry_id.delete(0, "end")
        self.entry_name.delete(0, "end")
        
    def start_verification(self):
        self.verifying = True
        self.btn_verify.config(state="disabled")
        self.btn_stop.config(state="enabled")
        self.update_status("Verifying... Scan finger", "blue")
        self.verify_loop()
        
    def stop_verification(self):
        self.verifying = False
        self.btn_verify.config(state="enabled")
        self.btn_stop.config(state="disabled")
        self.update_status("Verification stopped", "black")
        
    def verify_loop(self):
        if self.verifying:
            self.ser.reset_input_buffer()
            self.send_command("V\n")
            self.master.after(100, self.check_verify_response)
            self.master.after(2000, self.verify_loop)
            
    def check_verify_response(self):
        if self.ser.in_waiting > 0:
            response = self.ser.readline().decode().strip()
            if response.startswith("ID:"):
                fid = response.split(":")[1]
                if fid in self.users:
                    self.open_handcont()
            elif "No match" in response:
                self.update_status("Access Denied", "red")
                
    def open_handcont(self):
        self.stop_verification()
        self.ser.close()
        subprocess.Popen([sys.executable, "handcont.py"])
        self.master.destroy()
        
    def update_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", foreground=color)
        
    def on_closing(self):
        self.ser.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FingerprintApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
