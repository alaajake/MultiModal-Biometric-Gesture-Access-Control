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

# -------------------- Google Cloud Vision Setup --------------------
# Try to import and create a Vision API client.
# If not available (or not configured), we will use a fallback face comparison.
try:
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    client = vision.ImageAnnotatorClient()
except Exception as e:
    print("Google Cloud Vision API not available, using fallback face recognition.")
    client = None

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

def compare_face_landmarks(face1, face2):
    """
    Dummy implementation for demo purposes.
    In a full implementation, you would compare landmark positions.
    """
    return 0.8

def compare_faces_histogram(stored_path, live_path):
    """
    Fallback face-comparison using color histogram similarity.
    """
    stored_img = cv2.imread(stored_path)
    live_img = cv2.imread(live_path)
    if stored_img is None or live_img is None:
        return 0.0
    stored_hist = cv2.calcHist([stored_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    live_hist = cv2.calcHist([live_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(stored_hist, stored_hist)
    cv2.normalize(live_hist, live_hist)
    similarity = cv2.compareHist(stored_hist, live_hist, cv2.HISTCMP_CORREL)
    return similarity

def recognize_face(stored_face_path):
    """
    Recognize a face by capturing a live image and comparing it to the stored image.
    In production you might use the Google Cloud Vision API; here we use it if available,
    otherwise we fall back to a histogram-based comparison.
    """
    live_face_path = capture_face("live_face")
    if live_face_path is None:
        return False

    if client is not None:
        # Use Google Cloud Vision API for face detection.
        with open(stored_face_path, "rb") as stored_image_file:
            stored_image_content = stored_image_file.read()
        with open(live_face_path, "rb") as live_image_file:
            live_image_content = live_image_file.read()

        stored_image = types.Image(content=stored_image_content)
        live_image = types.Image(content=live_image_content)

        stored_face_response = client.face_detection(image=stored_image)
        live_face_response = client.face_detection(image=live_image)

        stored_faces = stored_face_response.face_annotations
        live_faces = live_face_response.face_annotations

        if not stored_faces or not live_faces:
            os.remove(live_face_path)
            return False

        similarity_score = compare_face_landmarks(stored_faces[0], live_faces[0])
        os.remove(live_face_path)
        return similarity_score >= 0.75
    else:
        # Fallback: compare histograms of the stored and live face images.
        similarity = compare_faces_histogram(stored_face_path, live_face_path)
        os.remove(live_face_path)
        return similarity >= 0.7

# -------------------- Hand Gesture Control --------------------
def detect_gesture(hand_landmarks, image_shape):
    """
    A simplified gesture detection algorithm using hand landmarks.
    Detects:
      - Fist: if average distance from wrist to finger tips is small.
      - Thumbs Up: if thumb is extended while other fingers are folded.
      - Open Palm: if all fingers are extended.
      - Select: if thumb tip and index finger tip are close.
    """
    h, w, _ = image_shape
    thumb = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
    index = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
    middle = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.RING_FINGER_TIP]
    pinky = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_TIP]
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]

    wrist_coords = (int(wrist.x * w), int(wrist.y * h))
    thumb_coords = (int(thumb.x * w), int(thumb.y * h))
    index_coords = (int(index.x * w), int(index.y * h))
    middle_coords = (int(middle.x * w), int(middle.y * h))
    ring_coords = (int(ring.x * w), int(ring.y * h))
    pinky_coords = (int(pinky.x * w), int(pinky.y * h))

    def distance(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2)**0.5

    d_thumb = distance(wrist_coords, thumb_coords)
    d_index = distance(wrist_coords, index_coords)
    d_middle = distance(wrist_coords, middle_coords)
    d_ring = distance(wrist_coords, ring_coords)
    d_pinky = distance(wrist_coords, pinky_coords)
    avg_distance = (d_thumb + d_index + d_middle + d_ring + d_pinky) / 5.0

    if avg_distance < 50:
        return "Fist"
    if d_thumb > avg_distance * 1.5 and d_index < avg_distance * 1.2 and d_middle < avg_distance * 1.2 and d_ring < avg_distance * 1.2 and d_pinky < avg_distance * 1.2:
        return "Thumbs Up"
    if d_thumb > 60 and d_index > 60 and d_middle > 60 and d_ring > 60 and d_pinky > 60:
        return "Open Palm"
    if distance(thumb_coords, index_coords) < 30:
        return "Select"
    return None

def run_gesture_control():
    """
    Activate hand gesture control using Google MediaPipe.
    Recognized gestures (with this demo’s simple algorithm) include:
      - Swipe Left/Right (detected via wrist movement)
      - Fist
      - Thumbs Up
      - Open Palm
      - Select (thumb-index pinch)
    The recognized gestures send commands to Arduino (if connected).
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
    prev_wrist_x = None

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
                # Get wrist coordinate for swipe detection.
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                h, w, _ = image.shape
                wrist_coords = (int(wrist.x * w), int(wrist.y * h))
                swipe = None
                if prev_wrist_x is not None:
                    dx = wrist_coords[0] - prev_wrist_x
                    if dx > 40:
                        swipe = "Swipe Right"
                    elif dx < -40:
                        swipe = "Swipe Left"
                prev_wrist_x = wrist_coords[0]

                gesture = detect_gesture(hand_landmarks, image.shape)
                if swipe is not None:
                    gesture = swipe  # Override if a swipe is detected

                if gesture is not None:
                    cv2.putText(image, f"Gesture: {gesture}", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if arduino_serial:
                        command = gesture.upper() + "\n"
                        arduino_serial.write(command.encode())

        cv2.imshow("Hand Gesture Control (Press 'q' to exit)", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            gesture_active = False

    cap.release()
    cv2.destroyAllWindows()

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

        # Generate a unique user ID (for simplicity, using timestamp)
        user_id = f"user_{int(time.time())}"

        users[name] = {
            "user_id": user_id,
            "face_image": self.face_path,
            "fingerprint_enrolled": self.fingerprint_enrolled,
            "timestamp": time.time()
        }
        save_users(users)
        log_event(f"User {name} registered with ID {user_id}.")
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
