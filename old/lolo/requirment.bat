@echo off
:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install it manually from https://www.python.org/downloads/
    pause
    exit /b
)

:: Upgrade pip to the latest version
python -m pip install --upgrade pip

:: Install MediaPipe
pip install mediapipe

:: Install OpenCV
pip install opencv-python-headless

:: Install TensorFlow
pip install tensorflow

:: Install tf-nightly for LSTM model (optional)
pip install tf-nightly

:: Install scikit-learn (optional)
pip install scikit-learn

:: Install matplotlib (optional)
pip install matplotlib

echo All required libraries have been installed.
pause
