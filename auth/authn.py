# auth_app.py
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import serial
import os
import json
import threading
from PIL import Image, ImageTk
import time

class AuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Biometric Authentication System")
        
        # Initialize attributes
        self.video = None
        self.arduino = None
        self.auth_active = True
        
        # Face recognition setup
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.users = {}
        self.load_users()
        
        # Hardware initialization
        self.init_camera()
        self.init_arduino()
        
        # GUI setup
        self.create_gui()
        
        # Start authentication thread
        threading.Thread(target=self.continuous_authentication, daemon=True).start()

    def init_camera(self):
        try:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                raise RuntimeError("Camera not available")
            self.current_frame = None
            self.update_camera()
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to initialize camera: {str(e)}")

    def init_arduino(self):
        try:
            self.arduino = serial.Serial('COM24', 57600)  # Update COM port
            time.sleep(2)
        except Exception as e:
            messagebox.showerror("Arduino Error", f"Failed to connect to Arduino: {str(e)}")

    def create_gui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0)

        ttk.Label(main_frame, text="Name:").grid(row=0, column=0)
        self.name_entry = ttk.Entry(main_frame, width=20)
        self.name_entry.grid(row=0, column=1)

        ttk.Button(main_frame, text="Add User", command=self.add_user).grid(row=0, column=2, padx=5)
        ttk.Button(main_frame, text="Delete User", command=self.delete_user).grid(row=0, column=3)

        self.camera_label = ttk.Label(main_frame)
        self.camera_label.grid(row=1, column=0, columnspan=4, pady=10)

        self.status_label = ttk.Label(main_frame, text="Status: Ready", foreground="blue")
        self.status_label.grid(row=2, column=0, columnspan=4)

    def update_camera(self):
        if self.video and self.video.isOpened():
            ret, frame = self.video.read()
            if ret:
                self.current_frame = frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
        self.root.after(10, self.update_camera)

    def add_user(self):
        name = self.name_entry.get()
        if not name:
            messagebox.showerror("Error", "Please enter a name")
            return

        if not self.arduino or not self.arduino.is_open:
            messagebox.showerror("Error", "Arduino connection not available")
            return

        fingerprint_id = self.enroll_fingerprint()
        if fingerprint_id is None:
            return

        if self.capture_face_samples(fingerprint_id):
            self.users[fingerprint_id] = name
            self.train_model()
            self.save_users()
            messagebox.showinfo("Success", "User added successfully")
        else:
            self.delete_fingerprint(fingerprint_id)
            messagebox.showerror("Error", "Face capture failed")

    def enroll_fingerprint(self):
        try:
            self.arduino.write(b'enroll')
            response = self.arduino.readline().decode().strip()
            if response.startswith('ID'):
                return int(response.split(':')[1])
            messagebox.showerror("Error", "Fingerprint enrollment failed")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Fingerprint error: {str(e)}")
            return None

    def capture_face_samples(self, user_id):
        if not self.video or not self.video.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return False

        sample_count = 0
        face_samples = []
        user_dir = f"faces/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        while sample_count < 20:
            ret, frame = self.video.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 1:
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_samples.append(face_roi)
                cv2.imwrite(f"{user_dir}/{sample_count}.jpg", face_roi)
                sample_count += 1
                time.sleep(0.1)

        return True

    def train_model(self):
        faces = []
        labels = []

        for user_id in self.users:
            user_dir = f"faces/{user_id}"
            if not os.path.exists(user_dir):
                continue

            for img_name in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces.append(img)
                    labels.append(user_id)

        if len(faces) > 0:
            self.face_recognizer.train(faces, np.array(labels))

    def delete_user(self):
        name = self.name_entry.get()
        user_id = next((uid for uid, uname in self.users.items() if uname == name), None)

        if user_id is None:
            messagebox.showerror("Error", "User not found")
            return

        self.delete_fingerprint(user_id)
        
        user_dir = f"faces/{user_id}"
        if os.path.exists(user_dir):
            for file in os.listdir(user_dir):
                os.remove(os.path.join(user_dir, file))
            os.rmdir(user_dir)

        del self.users[user_id]
        self.train_model()
        self.save_users()
        messagebox.showinfo("Success", "User deleted successfully")

    def delete_fingerprint(self, fid):
        try:
            self.arduino.write(f'delete:{fid}'.encode())
            response = self.arduino.readline().decode().strip()
            return response == 'OK'
        except Exception as e:
            messagebox.showerror("Error", f"Fingerprint deletion failed: {str(e)}")
            return False

    def continuous_authentication(self):
        while self.auth_active:
            if not self.arduino or not self.arduino.is_open:
                time.sleep(1)
                continue

            fingerprint_id = self.verify_fingerprint()
            if fingerprint_id is not None:
                if self.verify_face(fingerprint_id):
                    self.show_status("Access Granted", "green")
                else:
                    self.show_status("Face Verification Failed", "red")
            time.sleep(1)

    def verify_fingerprint(self):
        try:
            self.arduino.write(b'verify')
            response = self.arduino.readline().decode().strip()
            if response.startswith('ID'):
                return int(response.split(':')[1])
            return None
        except Exception as e:
            return None

    def verify_face(self, user_id):
        if not self.video or not self.video.isOpened():
            return False

        ret, frame = self.video.read()
        if not ret:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, 1.3, 5)

        if len(faces) != 1:
            return False

        x, y, w, h = faces[0]
        label, confidence = self.face_recognizer.predict(gray[y:y+h, x:x+w])
        return label == user_id and confidence < 70

    def show_status(self, text, color):
        self.status_label.config(text=f"Status: {text}", foreground=color)
        self.root.after(3000, lambda: self.status_label.config(text="Status: Ready", foreground="blue"))

    def load_users(self):
        if os.path.exists("users.json"):
            with open("users.json", "r") as f:
                self.users = json.load(f)
                # Convert keys to integers
                self.users = {int(k): v for k, v in self.users.items()}

    def save_users(self):
        with open("users.json", "w") as f:
            json.dump(self.users, f)

    def cleanup(self):
        """Explicit resource cleanup method"""
        self.auth_active = False
        
        if self.video and self.video.isOpened():
            self.video.release()
            
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.close()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = AuthApp(root)
    try:
        root.mainloop()
    finally:
        app.cleanup()