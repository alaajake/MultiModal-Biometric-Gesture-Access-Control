#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

void setup() {
  Serial.begin(9600);
  finger.begin(57600);
  
  if (finger.verifyPassword()) {
    Serial.println("Sensor found");
  } else {
    Serial.println("Sensor not found");
    while(1);
  }
}

void loop() {
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