// arduino.ino (Arduino Sketch)
#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

void setup() {
  Serial.begin(57600);
  finger.begin(57600);
  
  if (finger.verifyPassword()) {
    Serial.println("FPM Ready");
  } else {
    Serial.println("FPM Not Found");
    while(1);
  }
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "enroll") {
      enrollFingerprint();
    } else if (command.startsWith("delete")) {
      int id = command.substring(6).toInt();
      deleteFingerprint(id);
    } else if (command == "verify") {
      verifyFingerprint();
    }
  }
}

void enrollFingerprint() {
  int id = getFreeID();
  if (id == -1) return;
  
  int p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
  }
  
  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) return;
  
  delay(2000);
  
  p = finger.getImage();
  if (p != FINGERPRINT_OK) return;
  
  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) return;
  
  p = finger.createModel();
  if (p != FINGERPRINT_OK) return;
  
  p = finger.storeModel(id);
  if (p != FINGERPRINT_OK) return;
  
  Serial.print("ID:");
  Serial.println(id);
}

int getFreeID() {
  for (int id = 1; id < 127; id++) {
    if (finger.loadModel(id) != FINGERPRINT_OK) return id;
  }
  return -1;
}

void deleteFingerprint(int id) {
  if (finger.deleteModel(id) == FINGERPRINT_OK) {
    Serial.println("OK");
  } else {
    Serial.println("ERROR");
  }
}

void verifyFingerprint() {
  if (finger.getImage() != FINGERPRINT_OK) return;
  if (finger.image2Tz() != FINGERPRINT_OK) return;
  if (finger.fingerFastSearch() != FINGERPRINT_OK) return;
  
  Serial.print("ID:");
  Serial.println(finger.fingerID);
}