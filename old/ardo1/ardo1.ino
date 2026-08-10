#include <Servo.h>
Servo myservo;

char receivedChar;
const int doorPin = 9;
const int lightPin = 8;
const int fanPin = 7;
const int lampPin = 6;
const int ledPin = 5;

void setup() {
  Serial.begin(9600);
  pinMode(lightPin, OUTPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(lampPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  myservo.attach(doorPin);
}

void loop() {
  if (Serial.available() > 0) {
    receivedChar = Serial.read();
    
    // Right Hand Commands
    if (receivedChar == 'W') myservo.write(90);   // Door Open 
    if (receivedChar == 'L') digitalWrite(lightPin, HIGH);  // Light On
    if (receivedChar == 'F') digitalWrite(fanPin, HIGH);    // Fan On
    if (receivedChar == 'P') digitalWrite(lampPin, HIGH);   // Lamp On
    if (receivedChar == 'U') digitalWrite(ledPin, HIGH);    // LED On
    
    // Left Hand Commands
    if (receivedChar == 'w') myservo.write(180);    // Door Close
    if (receivedChar == 'l') digitalWrite(lightPin, LOW);    // Light Off
    if (receivedChar == 'f') digitalWrite(fanPin, LOW);      // Fan Off
    if (receivedChar == 'p') digitalWrite(lampPin, LOW);     // Lamp Off
    if (receivedChar == 'u') digitalWrite(ledPin, LOW);      // LED Off
  }
}