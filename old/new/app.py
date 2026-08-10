import tkinter as tk
from tkinter import messagebox, simpledialog
import cv2
import mediapipe as mp
import serial
import time
import os
import json
import logging
import threading

# -------------------- Configuration & Setup --------------------
# Logging configuration
logging.basicConfig(filename='access_control.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Files and directories
USER_DATA_FILE = "users.json"
FACE_IMAGE_DIR = "faces"

# Arduino configuration – adjust these for your system.
ARDUINO_PORT = "COM9"      # e.g., "COM3" on Windows or "/dev/ttyACM0" on Linux/Mac.
BAUD_RATE = 9600

# Attempt to establish serial connection with the Arduino.
try:
    arduino_serial = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # Wait for Arduino to initialize.
except Exception as e:
    print("Warning: Arduino not connected or serial port unavailable:", e)
    arduino_serial = None

# -------------------- Utility Functions --------------------
def load_users():
    """Load the registered users from a JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_users(data):
    """Save user data to a JSON file."""
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_event(event):
    """Log events for auditing."""
    logging.info(event)

# -------------------- Face Capture & Recognition --------------------
def capture_face(user_name):
    """
    Use OpenCV to capture a face image from the webcam.
    Press 'c' to capture and 'q' to exit.
    Returns the file path of the saved image or None if not captured.
    """
    if not os.path.exists(FACE_IMAGE_DIR):
        os.makedirs(FACE_IMAGE_DIR)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Webcam not accessible!")
        return None

    cv2.namedWindow("Capture Face (Press 'c' to capture, 'q' to exit)")
    captured_image_path = None

    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image from webcam.")
            break

        cv2.imshow("Capture Face (Press 'c' to capture, 'q' to exit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            # Save the captured image.
            file_name = f"{user_name}_{int(time.time())}.jpg"
            file_path = os.path.join(FACE_IMAGE_DIR, file_name)
            cv2.imwrite(file_path, frame)
            captured_image_path = file_path
            messagebox.showinfo("Success", f"Face captured and saved as {file_name}.")
            break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured_image_path

def recognize_face(stored_face_path):
    """
    Recognize a face by capturing a live image and comparing it to the stored image.
    In production, integrate Google Cloud Vision API (or similar) here.
    For this demo, we capture a live image and assume a match.
    """
    # Capture live face for verification.
    live_face_path = capture_face("live_face")
    if live_face_path is None:
        return False

    # --- Replace the following stub with actual face recognition logic ---
    # For instance, you can send both 'stored_face_path' and 'live_face_path'
    # to Google Cloud Vision API for a comparison.
    # Here, we simply return True to simulate a successful match.
    if os.path.exists(live_face_path):
        os.remove(live_face_path)
    return True

# -------------------- Fingerprint Enrollment & Authentication --------------------
def enroll_fingerprint():
    """
    Enroll a new fingerprint via Arduino.
    Sends an "ENROLL" command and waits for Arduino to respond.
    """
    if arduino_serial is None:
        messagebox.showerror("Error", "Arduino serial connection not available!")
        return False

    try:
        arduino_serial.flushInput()
        enrollment_command = "ENROLL\n"  # Adjust this command as needed.
        arduino_serial.write(enrollment_command.encode())
        messagebox.showinfo("Info", "Fingerprint enrollment started. Follow the scanner instructions.")
        
        # Wait up to 30 seconds for a response.
        timeout = time.time() + 30
        while time.time() < timeout:
            if arduino_serial.in_waiting:
                response_line = arduino_serial.readline().decode().strip()
                print("Arduino:", response_line)
                if "successful" in response_line.lower():
                    messagebox.showinfo("Success", "Fingerprint enrolled successfully!")
                    return True
                elif "failed" in response_line.lower():
                    messagebox.showerror("Error", "Fingerprint enrollment failed. Try again.")
                    return False
        messagebox.showerror("Error", "Fingerprint enrollment timed out.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Error during fingerprint enrollment: {e}")
        return False

def authenticate_fingerprint():
    """
    Authenticate a fingerprint using the Arduino.
    Sends a "VERIFY" command and waits for a match response.
    """
    if arduino_serial is None:
        messagebox.showerror("Error", "Arduino serial connection not available!")
        return False

    try:
        arduino_serial.flushInput()
        verify_command = "VERIFY\n"  # Adjust this command as needed.
        arduino_serial.write(verify_command.encode())
        messagebox.showinfo("Info", "Place your finger on the scanner for authentication.")

        timeout = time.time() + 30
        while time.time() < timeout:
            if arduino_serial.in_waiting:
                response_line = arduino_serial.readline().decode().strip()
                print("Arduino:", response_line)
                if "match" in response_line.lower():
                    messagebox.showinfo("Success", "Fingerprint verified!")
                    return True
                elif "not match" in response_line.lower():
                    messagebox.showerror("Error", "Fingerprint did not match.")
                    return False
        messagebox.showerror("Error", "Fingerprint authentication timed out.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Error during fingerprint authentication: {e}")
        return False

# -------------------- Hand Gesture Control --------------------
def run_gesture_control():
    """
    Activate hand gesture control using Google MediaPipe.
    Detects simple gestures and sends commands (e.g., "SELECT") to Arduino.
    Press 'q' to exit the gesture control window.
    """
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Webcam not accessible for gesture control!")
        return

    gesture_active = True
    messagebox.showinfo("Info", "Starting hand gesture control. Press 'q' in the video window to exit.")
    while gesture_active:
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                # --- Gesture Recognition Stub ---
                # As an example, we calculate the distance between the thumb tip and index finger tip.
                # If below a threshold, we consider it a "Select" gesture.
                thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = image.shape
                thumb_coords = (int(thumb.x * w), int(thumb.y * h))
                index_coords = (int(index.x * w), int(index.y * h))
                distance = ((thumb_coords[0] - index_coords[0]) ** 2 + (thumb_coords[1] - index_coords[1]) ** 2) ** 0.5

                if distance < 30:  # Threshold in pixels – adjust as needed.
                    cv2.putText(image, "Select Gesture", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if arduino_serial:
                        arduino_serial.write("SELECT\n".encode())

        cv2.imshow("Hand Gesture Control (Press 'q' to exit)", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            gesture_active = False

    cap.release()
    cv2.destroyAllWindows()

# -------------------- GUI Windows --------------------
class RegistrationWindow(tk.Toplevel):
    """
    A window for registering a new user:
      - Input full name.
      - Capture face image.
      - Enroll fingerprint.
    User data is saved to a JSON file.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("New User Registration")
        self.geometry("400x400")
        self.face_path = None
        self.fingerprint_enrolled = False
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Register New User", font=("Helvetica", 16)).pack(pady=10)
        tk.Label(self, text="Full Name:").pack(pady=5)
        self.name_entry = tk.Entry(self, width=30)
        self.name_entry.pack(pady=5)
        tk.Button(self, text="Capture Face", command=self.capture_face_action).pack(pady=10)
        tk.Button(self, text="Enroll Fingerprint", command=self.enroll_fingerprint_action).pack(pady=10)
        tk.Button(self, text="Register", command=self.register_action).pack(pady=20)

    def capture_face_action(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name first!")
            return
        self.face_path = capture_face(name)

    def enroll_fingerprint_action(self):
        result = enroll_fingerprint()
        self.fingerprint_enrolled = result

    def register_action(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name cannot be empty!")
            return
        if not self.face_path:
            messagebox.showerror("Error", "Face image not captured!")
            return
        if not self.fingerprint_enrolled:
            messagebox.showerror("Error", "Fingerprint not enrolled!")
            return

        users = load_users()
        if name in users:
            messagebox.showerror("Error", "User already exists!")
            return

        users[name] = {
            "face_image": self.face_path,
            "fingerprint_enrolled": self.fingerprint_enrolled,
            "timestamp": time.time()
        }
        save_users(users)
        log_event(f"User {name} registered.")
        messagebox.showinfo("Success", "User registered successfully!")
        self.destroy()

class AuthenticationWindow(tk.Toplevel):
    """
    A window for user authentication:
      - Verifies fingerprint using Arduino.
      - Performs face recognition.
      - If both succeed, launches the hand gesture control module.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("User Authentication")
        self.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="User Authentication", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self, text="Authenticate Fingerprint", command=self.authenticate_fingerprint_action).pack(pady=10)

    def authenticate_fingerprint_action(self):
        # Step 1: Fingerprint authentication.
        fp_verified = authenticate_fingerprint()
        if not fp_verified:
            log_event("Fingerprint authentication failed.")
            return

        # Step 2: Face recognition.
        users = load_users()
        if not users:
            messagebox.showerror("Error", "No registered users found!")
            return

        user_names = list(users.keys())
        name = simpledialog.askstring("User Selection", f"Enter your registered name:\n{', '.join(user_names)}")
        if not name or name not in users:
            messagebox.showerror("Error", "User not found!")
            return

        stored_face = users[name]["face_image"]
        face_verified = recognize_face(stored_face)
        if face_verified:
            log_event(f"User {name} authenticated successfully.")
            messagebox.showinfo("Success", "Authentication successful. Launching gesture control.")
            # Launch gesture control in a separate thread.
            threading.Thread(target=run_gesture_control, daemon=True).start()
        else:
            log_event(f"Face recognition failed for user {name}.")
            messagebox.showerror("Error", "Face recognition failed. Access denied.")

class AdminDashboardWindow(tk.Toplevel):
    """
    An admin dashboard to manage registered users and view system logs.
    Features include:
      - Listing registered users.
      - Deleting a user.
      - Viewing authentication logs.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Admin Dashboard")
        self.geometry("600x400")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Admin Dashboard", font=("Helvetica", 16)).pack(pady=10)
        self.user_listbox = tk.Listbox(self, width=50)
        self.user_listbox.pack(pady=10)
        self.load_users_list()
        tk.Button(self, text="Delete Selected User", command=self.delete_user).pack(pady=5)
        tk.Button(self, text="Refresh List", command=self.load_users_list).pack(pady=5)
        tk.Button(self, text="View Logs", command=self.view_logs).pack(pady=10)

    def load_users_list(self):
        self.user_listbox.delete(0, tk.END)
        users = load_users()
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def delete_user(self):
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a user to delete!")
            return
        user_name = self.user_listbox.get(selection[0])
        users = load_users()
        if user_name in users:
            del users[user_name]
            save_users(users)
            log_event(f"User {user_name} deleted by admin.")
            messagebox.showinfo("Success", f"User {user_name} deleted.")
            self.load_users_list()

    def view_logs(self):
        # Open the log file using the default text editor.
        if os.path.exists("access_control.log"):
            if os.name == 'nt':
                os.system("notepad access_control.log")
            else:
                os.system("gedit access_control.log")
        else:
            messagebox.showerror("Error", "Log file not found!")

# -------------------- Main Application Window --------------------
class MainApplication(tk.Tk):
    """
    The main application window that provides access to:
      - User Registration.
      - User Authentication.
      - Admin Dashboard.
    Future modules (e.g., voice assistant or mobile integration) can be added here.
    """
    def __init__(self):
        super().__init__()
        self.title("Multi-Modal Access Control System")
        self.geometry("500x400")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Welcome to Multi-Modal Access Control", font=("Helvetica", 18)).pack(pady=20)
        tk.Button(self, text="Register New User", width=25, command=self.open_registration).pack(pady=10)
        tk.Button(self, text="User Authentication", width=25, command=self.open_authentication).pack(pady=10)
        tk.Button(self, text="Admin Dashboard", width=25, command=self.open_admin_dashboard).pack(pady=10)

    def open_registration(self):
        RegistrationWindow(self)

    def open_authentication(self):
        AuthenticationWindow(self)

    def open_admin_dashboard(self):
        AdminDashboardWindow(self)

# -------------------- Main Program --------------------
if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
