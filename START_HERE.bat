@echo off
echo ============================================
echo  League of Legends Draft Analyzer
echo ============================================
echo.

REM Check if fastapi is installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ERROR: Python packages not installed!
    echo.
    echo Please run SETUP_FIRST.bat before starting.
    echo.
    pause
    exit /b 1
)

echo Checking for stuck server processes...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":3000" ^| find "LISTENING"') do (
    echo   Port 3000 in use by PID %%a ^- terminating to free React dev server port.
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do (
    echo   Port 8000 in use by PID %%a ^- terminating to free FastAPI port.
    taskkill /PID %%a /F >nul 2>&1
)
echo.
echo Starting both servers...
echo.
echo [1/2] Starting Backend API on port 8000...
start "Backend API" cmd /k "python backend/draft_api.py"
timeout /t 3 /nobreak > nul
echo.
echo [2/2] Starting Frontend on port 3000...
start "React Frontend" cmd /k "cd frontend && npm start"
echo.
echo ============================================
echo  Both servers are starting!
echo ============================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend:     http://localhost:3000
echo.
echo The browser will open automatically.
echo.
echo To stop: Close both terminal windows
echo          or press Ctrl+C in each window
echo.
pause
