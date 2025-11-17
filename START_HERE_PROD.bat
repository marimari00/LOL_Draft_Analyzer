@echo off
setlocal
cd /d "%~dp0"

set BACKEND_PORT=8000
set FRONTEND_PORT=4173

echo ============================================
echo   League of Legends Draft Analyzer (Prod)
echo ============================================
echo.
echo Checking Python dependencies...
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo ERROR: Backend dependencies missing.
    echo Run SETUP_FIRST.bat before launching production mode.
    echo.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found in PATH.
    echo Install Node.js 18+ from https://nodejs.org/ and retry.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing frontend dependencies (npm install)...
pushd frontend >nul
call npm install --no-audit --no-fund
if errorlevel 1 goto :npm_fail

echo.
echo Building production bundle (npm run build)...
call npm run build
if errorlevel 1 goto :npm_fail
popd >nul

echo.
echo Checking for stuck server processes...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%FRONTEND_PORT%" ^| find "LISTENING"') do (
    echo   Port %FRONTEND_PORT% in use by PID %%a ^- terminating.
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%BACKEND_PORT%" ^| find "LISTENING"') do (
    echo   Port %BACKEND_PORT% in use by PID %%a ^- terminating.
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo Starting production backend (Uvicorn)...
start "Backend API (Prod)" cmd /k "cd /d %~dp0 && python -m uvicorn backend.draft_api:app --host 0.0.0.0 --port %BACKEND_PORT% --workers 1"
timeout /t 3 /nobreak >nul

echo Starting static frontend server (serve -s build)...
start "Frontend (Prod)" cmd /k "cd /d %~dp0\frontend && npx serve -s build -l %FRONTEND_PORT%"

echo.
echo ============================================
echo   Production stack is starting up!
echo ============================================
echo Backend API:   http://localhost:%BACKEND_PORT%
echo Frontend (prod): http://localhost:%FRONTEND_PORT%
echo.
echo To stop: close both terminal windows or Ctrl+C inside each.
echo.
pause
exit /b 0

:npm_fail
popd >nul
echo.
echo ERROR: Frontend dependency/build step failed.
echo Check the logs above, fix the issue, and rerun START_HERE_PROD.bat.
echo.
pause
exit /b 1
