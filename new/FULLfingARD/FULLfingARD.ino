#include <Servo.h>
#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

Servo myservo;
SoftwareSerial mySerial(2, 3); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

char receivedChar;
const int doorPin = 9;
const int lightPin = 8;
const int fanPin = 7;
const int lampPin = 6;
const int ledPin = 5;

unsigned long lastFingerprintCheck = 0;
const unsigned long fingerprintCheckInterval = 100; // Check fingerprint every 100 ms

void setup() {
  Serial.begin(9600);
  pinMode(lightPin, OUTPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(lampPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  myservo.attach(doorPin);
  myservo.write(180);

  finger.begin(57600);
  if (finger.verifyPassword()) {
    Serial.println("Sensor found");
  } else {
    Serial.println("Sensor not found");
    while (1);
  }
}

void loop() {
  // Handle Serial Commands (Servo, Lights, Fan, etc.)
  if (Serial.available() > 0) {
    receivedChar = Serial.read();

    // Right Hand Commands
    if (receivedChar == 'W') myservo.write(90);    // Door Open
    if (receivedChar == 'L') digitalWrite(lightPin, HIGH);  // Light On
    if (receivedChar == 'F') digitalWrite(fanPin, HIGH);    // Fan On
    if (receivedChar == 'P') digitalWrite(lampPin, HIGH);    // Lamp On
    if (receivedChar == 'U') digitalWrite(ledPin, HIGH);    // LED On

    // Left Hand Commands
    if (receivedChar == 'w') myservo.write(180);   // Door Close
    if (receivedChar == 'l') digitalWrite(lightPin, LOW);    // Light Off
    if (receivedChar == 'f') digitalWrite(fanPin, LOW);      // Fan Off
    if (receivedChar == 'p') digitalWrite(lampPin, LOW);      // Lamp Off
    if (receivedChar == 'u') digitalWrite(ledPin, LOW);      // LED Off

    if (receivedChar == 'E') { // Enroll
      enrollFingerprint();
    } else if (receivedChar == 'D') { // Delete
      deleteFingerprint();
    } else if (receivedChar == 'V') { // Verify
      verifyFingerprint();
    }
  }

  // Handle Fingerprint Sensor (non-blocking)
  unsigned long currentTime = millis();
  if (currentTime - lastFingerprintCheck >= fingerprintCheckInterval) {
    lastFingerprintCheck = currentTime;
    checkFingerprintCommands(); //Check for fingerprint commands
  }
}

void checkFingerprintCommands(){
    if (Serial.available() > 0) {
        char command = Serial.read();
        if (command == 'E') { // Enroll
            enrollFingerprint();
        } else if (command == 'D') { // Delete
            deleteFingerprint();
        } else if (command == 'V') { // Verify
            verifyFingerprint();
        }
    }
}

void enrollFingerprint() {
  int id = Serial.parseInt();
  Serial.read(); // Read comma
  String name = Serial.readStringUntil('\n');

  Serial.print("Enrolling ID #");
  Serial.println(id);

  int p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      Serial.println("Image taken");
    } else {
      Serial.println("Error, retrying...");
    }
    delay(10); //small delay to avoid blocking
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) {
    Serial.println("Enroll failed: Feature error");
    return;
  }

  Serial.println("Remove finger");
  delay(2000);

  p = -1;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
    delay(10);
  }

  Serial.println("Place same finger again");
  p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      Serial.println("Image taken");
    } else {
      Serial.println("Error, retrying...");
    }
    delay(10);
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) {
    Serial.println("Enroll failed: Feature error");
    return;
  }

  p = finger.createModel();
  if (p != FINGERPRINT_OK) {
    Serial.println("Enroll failed: Mismatch");
    return;
  }

  p = finger.storeModel(id);
  if (p != FINGERPRINT_OK) {
    Serial.println("Enroll failed: Storage error");
    return;
  }

  Serial.println("Stored!");
}

void deleteFingerprint() {
  int id = Serial.parseInt();
  if (finger.deleteModel(id)) {
    Serial.println("Deleted!");
  } else {
    Serial.println("Delete failed");
  }
}

void verifyFingerprint() {
  int p = finger.getImage();
  if (p != FINGERPRINT_OK) return;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return;

  p = finger.fingerSearch();
  if (p == FINGERPRINT_OK) {
    Serial.print("ID:");
    Serial.println(finger.fingerID);
  } else {
    Serial.println("No match");
  }
}