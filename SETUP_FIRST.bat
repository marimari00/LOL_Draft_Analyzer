@echo off
echo ============================================
echo  Draft Analyzer - First Time Setup
echo ============================================
echo.
echo This will install all required dependencies.
echo This only needs to be run ONCE.
echo.
pause
echo.

echo [1/2] Installing Python packages...
echo.
pip install fastapi uvicorn pydantic pandas numpy scikit-learn
echo.

echo [2/2] Installing Node.js packages...
echo.
cd frontend
call npm install
cd ..
echo.

echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo You can now run START_HERE.bat to launch the app.
echo.
pause
