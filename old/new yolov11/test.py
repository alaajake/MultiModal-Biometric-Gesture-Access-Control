from ultralytics import YOLO
import cv2

# Load YOLOv11 model (use pretrained weights if available)
model = YOLO(r'C:\Users\alaaj\Desktop\reserch\alaa\new yolov11\yolo11n.pt')  # Or replace with 'path/to/your/yolov11_custom.pt' if using trained weights

# Train the model on your custom dataset for hand gestures
# This step only needs to be run once to create the trained model
#model.train(data=r'Hand Gesture Recognition.v1i.yolov11/data.yaml', epochs=1, imgsz=640)  # Update path and training settings as needed
# Open webcam for live detection
#results = model.train(data=r"C:\Users\alaaj\Desktop\reserch\alaa\new yolov11\Hand Gesture Recognition.v1i.yolov11\data.yaml", epochs=1, imgsz=640)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Run YOLOv11 inference on the current frame
    results = model.predict(source=frame, conf=0.5)  # Adjust confidence threshold if needed

    # Draw bounding boxes and labels on the frame
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            label = result.names[int(box.cls)]  # Class label
            confidence = box.conf[0]  # Confidence score

            # Draw rectangle and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Show frame with detections
    cv2.imshow("Hand Gesture Detection", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
