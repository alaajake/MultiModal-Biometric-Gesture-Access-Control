import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
from deepface import DeepFace
import os
import pickle
import threading
import subprocess
import numpy as np
from PIL import Image, ImageTk
import time

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition System")
        self.root.geometry("600x600")
        
        self.known_embeddings = {}
        self.user_images_dir = "user_images"
        self.embeddings_file = "embeddings.pkl"
        self.is_recognition_running = False
        self.is_adding_user = False
        self.capture_count = 0
        self.MAX_CAPTURES = 10
        self.CAPTURE_INTERVAL = 1
        self.ADMIN_PASSWORD = "12345678"
        
        os.makedirs(self.user_images_dir, exist_ok=True)
        self.create_widgets()
        self.load_embeddings()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        self.user_list = tk.Listbox(main_frame, height=15, font=('Arial', 12))
        self.user_list.pack(pady=10, fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="Add User", command=self.start_add_user)
        self.add_btn.pack(side=tk.LEFT, padx=10)
        
        self.remove_btn = ttk.Button(btn_frame, text="Remove User", command=self.remove_user)
        self.remove_btn.pack(side=tk.LEFT, padx=10)
        
        self.start_btn = ttk.Button(main_frame, text="Start Recognition", command=self.toggle_recognition)
        self.start_btn.pack(pady=10)
        
        self.status_label = tk.Label(main_frame, text="", font=('Arial', 12))
        self.status_label.pack()
        
        self.webcam_label = tk.Label(main_frame)
        self.webcam_label.pack()
    
    def load_embeddings(self):
        if os.path.exists(self.embeddings_file):
            with open(self.embeddings_file, 'rb') as f:
                self.known_embeddings = pickle.load(f)
        
        self.user_list.delete(0, tk.END)
        for user in self.known_embeddings:
            self.user_list.insert(tk.END, user)
    
    def save_embeddings(self):
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.known_embeddings, f)
    
    def start_add_user(self):
        if self.is_recognition_running:
            messagebox.showwarning("Warning", "Stop recognition first before adding new user")
            return
        
        password = simpledialog.askstring("Authentication", "Enter admin password:", show='*')
        if password != self.ADMIN_PASSWORD:
            messagebox.showerror("Error", "Incorrect password!")
            return
        
        name = simpledialog.askstring("New User", "Enter user name:")
        if not name:
            return
            
        if name in self.known_embeddings:
            messagebox.showwarning("Warning", "User already exists!")
            return

        self.is_adding_user = True
        self.capture_count = 0
        self.status_label.config(text=f"Capturing {self.MAX_CAPTURES} images...")
        threading.Thread(target=self.capture_user_images, args=(name,), daemon=True).start()
    
    def capture_user_images(self, name):
        user_dir = os.path.join(self.user_images_dir, name)
        os.makedirs(user_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(0)
        last_capture_time = time.time()
        
        while self.is_adding_user and self.capture_count < self.MAX_CAPTURES:
            ret, frame = cap.read()
            if not ret:
                break
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.webcam_label.imgtk = imgtk
            self.webcam_label.configure(image=imgtk)
            
            if time.time() - last_capture_time > self.CAPTURE_INTERVAL:
                img_path = os.path.join(user_dir, f"{name}_{self.capture_count}.jpg")
                cv2.imwrite(img_path, frame)
                self.capture_count += 1
                self.status_label.config(text=f"Captured {self.capture_count}/{self.MAX_CAPTURES} images")
                last_capture_time = time.time()
            
            self.root.update_idletasks()
        
        cap.release()
        if self.capture_count >= self.MAX_CAPTURES:
            self.create_embeddings(name, user_dir)
            self.status_label.config(text="User added successfully!")
        else:
            self.status_label.config(text="User addition canceled")
        self.is_adding_user = False
        self.webcam_label.configure(image='')
    
    def create_embeddings(self, name, user_dir):
        embeddings = []
        for img_file in os.listdir(user_dir):
            img_path = os.path.join(user_dir, img_file)
            try:
                embedding = DeepFace.represent(img_path=img_path, model_name='Facenet')[0]["embedding"]
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error processing {img_file}: {str(e)}")
        
        if embeddings:
            avg_embedding = np.mean(embeddings, axis=0)
            self.known_embeddings[name] = avg_embedding.tolist()
            self.save_embeddings()
            self.load_embeddings()
    
    def remove_user(self):
        selected = self.user_list.curselection()
        if selected:
            user = self.user_list.get(selected[0])
            del self.known_embeddings[user]
            self.save_embeddings()
            self.load_embeddings()
            messagebox.showinfo("Success", f"{user} removed successfully!")
    
    def toggle_recognition(self):
        if self.is_recognition_running:
            self.is_recognition_running = False
            self.start_btn.config(text="Start Recognition")
            self.status_label.config(text="Recognition stopped")
        else:
            self.is_recognition_running = True
            self.start_btn.config(text="Stop Recognition")
            threading.Thread(target=self.face_recognition, daemon=True).start()
            self.status_label.config(text="Recognition running...")
    
    def face_recognition(self):
        cap = cv2.VideoCapture(0)
        while self.is_recognition_running:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                faces = DeepFace.extract_faces(frame, detector_backend='ssd')
                for face in faces:
                    area = face['facial_area']
                    x = area['x']
                    y = area['y']
                    w = area['w']
                    h = area['h']
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    embedding = DeepFace.represent(frame[y:y+h, x:x+w], model_name='Facenet', enforce_detection=False)[0]["embedding"]
                    
                    verified = False
                    for user, known_embedding in self.known_embeddings.items():
                        result = DeepFace.verify(embedding, known_embedding, 
                                               model_name='Facenet', 
                                               distance_metric='cosine',
                                               enforce_detection=False)
                        if result['verified']:
                            verified = True
                            break
                    
                    if verified:
                        cv2.putText(frame, "Access Granted", (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        subprocess.Popen(["python", "authentication2.py"])
                        self.is_recognition_running = False
                        self.start_btn.config(text="Start Recognition")
                        self.status_label.config(text="Access granted!")
                        # Close the application after 1 second
                        self.root.after(1000, self.root.destroy)
                        break
                    else:
                        cv2.putText(frame, "Access Denied", (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            except Exception as e:
                print(f"Error: {e}")
            
            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()