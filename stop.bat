@echo off
REM IELTS AI Coach - Windows Stop Script

echo.
echo ========================================
echo   IELTS AI Coach - Stopping Services
echo ========================================
echo.

REM Stop backend (search for uvicorn process)
echo Stopping backend service...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    taskkill /F /PID %%a 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo Backend stopped successfully
    )
)

REM Stop frontend (search for streamlit process)
echo Stopping frontend service...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501"') do (
    taskkill /F /PID %%a 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo Frontend stopped successfully
    )
)

REM Alternative: Kill all Python processes running streamlit or uvicorn
echo Cleaning up any remaining processes...
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *streamlit*" 2>nul
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *uvicorn*" 2>nul

echo.
echo All services stopped.
echo.
pause
