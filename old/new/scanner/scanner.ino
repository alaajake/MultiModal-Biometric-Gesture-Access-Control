#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

// Define software serial pins for Arduino Uno
SoftwareSerial mySerial(2, 3); // RX, TX for fingerprint module

Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

void setup() {
    Serial.begin(9600);  // USB Serial (communication with Python)
    mySerial.begin(57600);  // Fingerprint sensor baud rate
    Serial.println("R307 Fingerprint Module Ready");
    
    finger.begin(57600);

    if (finger.verifyPassword()) {
        Serial.println("Fingerprint sensor detected!");
    } else {
        Serial.println("Fingerprint sensor NOT found! Check connections.");
        while (1);
    }
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');  // Read the command from Python
        command.trim();  // Remove any whitespace
        
        if (command == "ENROLL") {
            enrollFingerprint();
        } else if (command == "VERIFY") {
            verifyFingerprint();
        }
    }
}

// -------------------- Enroll Fingerprint --------------------
void enrollFingerprint() {
    Serial.println("Place your finger on the scanner...");
    int id = findAvailableID();  // Find the next available ID for enrollment

    if (id == -1) {
        Serial.println("Fingerprint storage full.");
        return;
    }

    int p = -1;
    while (p != FINGERPRINT_OK) {
        p = finger.getImage();
        if (p == FINGERPRINT_NOFINGER) {
            Serial.println("No finger detected. Place your finger on the sensor.");
        } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
            Serial.println("Communication error with sensor.");
        } else if (p == FINGERPRINT_IMAGEFAIL) {
            Serial.println("Imaging error.");
        }
        delay(100);
    }

    p = finger.image2Tz(1);
    if (p != FINGERPRINT_OK) {
        Serial.println("Error converting image.");
        return;
    }

    Serial.println("Remove finger and place it again.");
    delay(2000);

    p = 0;
    while (p != FINGERPRINT_NOFINGER) {
        p = finger.getImage();
        delay(100);
    }

    Serial.println("Place your finger again.");
    p = -1;
    while (p != FINGERPRINT_OK) {
        p = finger.getImage();
        if (p == FINGERPRINT_NOFINGER) {
            Serial.println("No finger detected. Place your finger again.");
        } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
            Serial.println("Communication error.");
        } else if (p == FINGERPRINT_IMAGEFAIL) {
            Serial.println("Imaging error.");
        }
        delay(100);
    }

    p = finger.image2Tz(2);
    if (p != FINGERPRINT_OK) {
        Serial.println("Error converting second image.");
        return;
    }

    Serial.println("Creating fingerprint model...");
    p = finger.createModel();
    if (p == FINGERPRINT_OK) {
        Serial.println("Fingerprint model created successfully!");
    } else {
        Serial.println("Fingerprint model creation failed.");
        return;
    }

    Serial.print("Storing fingerprint at ID ");
    Serial.println(id);
    p = finger.storeModel(id);
    if (p == FINGERPRINT_OK) {
        Serial.println("Fingerprint stored successfully!");
        Serial.println("ENROLL_SUCCESS");  // Notify Python
    } else {
        Serial.println("Failed to store fingerprint.");
        Serial.println("ENROLL_FAIL");  // Notify Python
    }
}

// -------------------- Verify Fingerprint --------------------
void verifyFingerprint() {
    Serial.println("Place your finger for authentication...");
    int p = -1;

    while (p != FINGERPRINT_OK) {
        p = finger.getImage();
        if (p == FINGERPRINT_NOFINGER) {
            Serial.println("No finger detected.");
        } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
            Serial.println("Communication error.");
        } else if (p == FINGERPRINT_IMAGEFAIL) {
            Serial.println("Imaging error.");
        }
        delay(100);
    }

    p = finger.image2Tz(1);
    if (p != FINGERPRINT_OK) {
        Serial.println("Error converting image.");
        Serial.println("VERIFY_FAIL");  // Notify Python
        return;
    }

    p = finger.fingerSearch();
    if (p == FINGERPRINT_OK) {
        Serial.print("Fingerprint matched! ID: ");
        Serial.println(finger.fingerID);
        Serial.println("VERIFY_SUCCESS");  // Notify Python
    } else {
        Serial.println("Fingerprint did not match.");
        Serial.println("VERIFY_FAIL");  // Notify Python
    }
}

// -------------------- Find Next Available ID --------------------
int findAvailableID() {
    for (int i = 1; i < 127; i++) {  // IDs from 1 to 127
        int p = finger.loadModel(i);
        if (p != FINGERPRINT_OK) {
            return i;  // Found an empty slot
        }
    }
    return -1;  // No available slots
}
