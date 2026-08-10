# Multi-Modal Biometric Security System: Face + Fingerprint + Hand Gesture Control

### نظام أمان متعدد الطبقات: التعرف على الوجه + بصمة الإصبع + التحكم بإيماءات اليد

> **Student / Client:** Alaa Razzaq Swayesh
> **Supervisor:** Ali Hamza Sahib

## 📋 Project Overview

Three-layer security access control system: 1) Face Recognition authentication 2) Fingerprint biometric verification 3) Hand gesture-based device control via Computer Vision + Arduino actuators (servo doors, LEDs).

## 🛠️ Technologies Used

- Python
- DeepFace
- Face Recognition
- OpenCV
- MediaPipe
- Arduino
- Fingerprint Sensor
- Servo Motors
- Tkinter
- Pickle

## ✨ Key Features

- ✅ Layer 1: Face Recognition (DeepFace) with add-user via admin password
- ✅ Layer 2: Fingerprint enrollment & matching on Arduino
- ✅ Layer 3: Hand Gesture Recognition (finger counting) → servo/door actions
- ✅ Right/Left hand gesture mapping to opposite actions
- ✅ Tkinter GUI windows for each auth stage
- ✅ Embedded biometric data storage (pickle + Arduino)

## 📁 Repository Structure

```
alaa/
├── src/              # Source code (Python / Arduino .ino)
├── app/              # Desktop / web application
├── models/           # Trained ML models, weights, encodings
├── data/             # Datasets, pickled encodings, databases
├── hardware/         # Arduino sketches (.ino), schematics
├── docs/             # Research papers, Word documents (.docx)
└── assets/           # Images, diagrams, screenshots
```

## 🏗️ Hardware / System Block Diagram

*(Refer to docs folder for detailed schematics, pinouts, and wiring diagrams in the project Word document)*

## 🚀 Setup & Installation

### Python Projects
```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt   # or installreq.py for automated installs

# 3. Run the application
python app.py
```

### Arduino Projects
1. Install **Arduino IDE** (2.x recommended)
2. Install required libraries via Library Manager (project-specific)
3. Open the `.ino` sketch from `hardware/` folder
4. Select correct board & COM port → Upload

## 🧑‍🎓 Project Context

This project is part of a series of **academic graduation / personal portfolio projects** (Computer Techniques Engineering, 2024-2025). Full research papers, circuit diagrams, and documentation are included in the respective `docs/` directories.
---

## 📝 Copyright & Ownership

**© 2026 Alaa Ahmed Ajeel (علاء أحمد عجيل) - All Rights Reserved**

> **Author & Designer:** Alaa Ahmed Ajeel
> **GitHub:** [@alaajake](https://github.com/alaajake)

This project was fully **developed, written, designed, and implemented** by **Alaa Ahmed Ajeel** as part of academic graduation projects and personal research work.

Customized working copies of these projects have been delivered to clients/students, while this original source code repository remains the property of the author under full copyright protection.

**Unauthorized copying, modification, distribution, or commercial use of this code, via any medium, is strictly prohibited without prior written permission from the author.**
