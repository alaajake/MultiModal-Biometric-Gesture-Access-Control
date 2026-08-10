import cv2
from cvzone.HandTrackingModule import HandDetector
import serial
import time

# Initialize camera and hand detector
cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# Arduino communication setup (change COM port as needed)
arduino = serial.Serial(port='COM23', baudrate=9600)
time.sleep(2)  # Allow serial connection to initialize

# Previous command storage to avoid spamming
prev_right_command = None
prev_left_command = None

while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)

    if hands:
        for hand in hands:
            handType = hand["type"]  # "Left" or "Right"
            fingers = detector.fingersUp(hand)
            totalFingers = sum(fingers)

            # Display hand type and finger count
            cv2.putText(img, f'{handType} Hand: {totalFingers}',
                        (50, 50 + (30 * hands.index(hand))),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Right Hand Commands
            if handType == "Right":
                if totalFingers == 1 and prev_right_command != "W":
                    arduino.write(b'W')  # Door Open
                    prev_right_command = "W"
                elif totalFingers == 2 and prev_right_command != "L":
                    arduino.write(b'L')  # Light On
                    prev_right_command = "L"
                elif totalFingers == 3 and prev_right_command != "F":
                    arduino.write(b'F')  # Fan On
                    prev_right_command = "F"
                elif totalFingers == 4 and prev_right_command != "P":
                    arduino.write(b'P')  # Lamp On
                    prev_right_command = "P"
                elif totalFingers == 5 and prev_right_command != "U":
                    arduino.write(b'U')  # LED On
                    prev_right_command = "U"

            # Left Hand Commands (Reverse Actions)
            elif handType == "Left":
                if totalFingers == 1 and prev_left_command != "w":
                    arduino.write(b'w')  # Door Close
                    prev_left_command = "w"
                elif totalFingers == 2 and prev_left_command != "l":
                    arduino.write(b'l')  # Light Off
                    prev_left_command = "l"
                elif totalFingers == 3 and prev_left_command != "f":
                    arduino.write(b'f')  # Fan Off
                    prev_left_command = "f"
                elif totalFingers == 4 and prev_left_command != "p":
                    arduino.write(b'p')  # Lamp Off
                    prev_left_command = "p"
                elif totalFingers == 5 and prev_left_command != "u":
                    arduino.write(b'u')  # LED Off
                    prev_left_command = "u"

    cv2.imshow("Hand Controller", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
arduino.close()
cap.release()
cv2.destroyAllWindows()