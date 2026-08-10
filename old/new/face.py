import cv2
import io
import os
from google.cloud import vision
from google.cloud.vision_v1 import types

def capture_image(filename='captured_face.jpg'):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the webcam")
        return None
    
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")
        return filename
    else:
        print("Error: Could not capture image")
        return None

def detect_faces(image_path):
    client = vision.ImageAnnotatorClient()
    
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
        image = types.Image(content=content)
    
    response = client.face_detection(image=image)
    faces = response.face_annotations
    
    if not faces:
        print("No faces detected.")
        return
    
    for i, face in enumerate(faces):
        print(f"Face {i+1}:")
        print(f"  Joy Likelihood: {face.joy_likelihood}")
        print(f"  Sorrow Likelihood: {face.sorrow_likelihood}")
        print(f"  Anger Likelihood: {face.anger_likelihood}")
        print(f"  Surprise Likelihood: {face.surprise_likelihood}")
        print(f"  Headwear Likelihood: {face.headwear_likelihood}")
    
    if response.error.message:
        print(f"Error: {response.error.message}")

if __name__ == "__main__":
    image_file = capture_image()
    if image_file:
        detect_faces(image_file)
