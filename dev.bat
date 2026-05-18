@echo off
echo Starting BAYMAX v11.0 Development Environment...

:: Start Backend in a new window
start cmd /k "python main.py"

:: Start Frontend
echo Navigating to frontend...
cd frontend
npm run dev
