@echo off
REM IELTS AI Coach - Windows Startup Script
REM This script ensures proper environment setup and service startup

setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_DIR=%~dp0"
set "ENV_NAME=ielts-coach2"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=8501"
set "USE_VENV=0"

REM Colors using PowerShell (Windows 10+)
set "PSScript=Write-Host"

echo.
echo ========================================
echo   IELTS AI Coach - Windows Setup
echo ========================================
echo.

REM Function to print colored output
:print_info
powershell -Command "Write-Host '[INFO] %~1' -ForegroundColor Cyan"
goto :eof

:print_success
powershell -Command "Write-Host '[SUCCESS] %~1' -ForegroundColor Green"
goto :eof

:print_warning
powershell -Command "Write-Host '[WARNING] %~1' -ForegroundColor Yellow"
goto :eof

:print_error
powershell -Command "Write-Host '[ERROR] %~1' -ForegroundColor Red"
goto :eof

REM Check if conda is available
call :print_info "Checking for Python environment managers..."

where conda >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :print_success "Conda found"
    set "CONDA_AVAILABLE=1"
) else (
    call :print_warning "Conda not found or not in PATH"
    set "CONDA_AVAILABLE=0"
)

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :print_success "Python found"
    set "PYTHON_AVAILABLE=1"
) else (
    call :print_error "Python not found in PATH"
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Environment selection
if !CONDA_AVAILABLE! EQU 1 (
    echo.
    echo Which environment manager would you like to use?
    echo 1. Conda (recommended if already installed)
    echo 2. Python venv (more lightweight, better for Windows)
    echo.
    set /p "ENV_CHOICE=Enter your choice (1 or 2): "
    
    if "!ENV_CHOICE!"=="2" (
        set "USE_VENV=1"
        call :print_info "Using Python venv"
    ) else (
        set "USE_VENV=0"
        call :print_info "Using Conda"
    )
) else (
    call :print_info "Using Python venv (Conda not available)"
    set "USE_VENV=1"
)

REM Setup environment based on choice
if !USE_VENV! EQU 1 (
    call :setup_venv
) else (
    call :setup_conda
)

if !ERRORLEVEL! NEQ 0 (
    call :print_error "Environment setup failed"
    pause
    exit /b 1
)

REM Check environment variables
call :check_env_vars
if !ERRORLEVEL! NEQ 0 (
    pause
    exit /b 1
)

REM Check ports
call :check_port !BACKEND_PORT! "Backend API"
call :check_port !FRONTEND_PORT! "Frontend App"

REM Start services
call :start_backend
if !ERRORLEVEL! NEQ 0 (
    call :print_error "Failed to start backend"
    pause
    exit /b 1
)

call :start_frontend
if !ERRORLEVEL! NEQ 0 (
    call :print_error "Failed to start frontend"
    pause
    exit /b 1
)

call :show_status

echo.
call :print_success "IELTS AI Coach is running! Press Ctrl+C to stop."
echo.
pause
goto :eof

REM ========================================
REM Functions
REM ========================================

:setup_conda
call :print_info "Setting up Conda environment..."

REM Check if environment exists
conda env list | findstr /C:"!ENV_NAME!" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :print_warning "Environment '!ENV_NAME!' not found"
    
    if exist "!PROJECT_DIR!environment.yml" (
        call :print_info "Creating environment from environment.yml..."
        conda env create -f "!PROJECT_DIR!environment.yml"
        if !ERRORLEVEL! NEQ 0 (
            call :print_error "Failed to create conda environment"
            exit /b 1
        )
        call :print_success "Environment created successfully"
    ) else (
        call :print_error "environment.yml not found"
        exit /b 1
    )
) else (
    call :print_success "Environment '!ENV_NAME!' found"
)

REM Activate environment
call :print_info "Activating conda environment..."
call conda activate !ENV_NAME!
if !ERRORLEVEL! NEQ 0 (
    call :print_error "Failed to activate conda environment"
    exit /b 1
)

call :print_success "Conda environment activated"
goto :eof

:setup_venv
call :print_info "Setting up Python virtual environment..."

set "VENV_DIR=!PROJECT_DIR!venv"

REM Check if venv exists
if not exist "!VENV_DIR!\Scripts\activate.bat" (
    call :print_warning "Virtual environment not found, creating..."
    
    python -m venv "!VENV_DIR!"
    if !ERRORLEVEL! NEQ 0 (
        call :print_error "Failed to create virtual environment"
        exit /b 1
    )
    call :print_success "Virtual environment created"
    
    REM Activate and install requirements
    call "!VENV_DIR!\Scripts\activate.bat"
    
    if exist "!PROJECT_DIR!requirements.txt" (
        call :print_info "Installing requirements..."
        python -m pip install --upgrade pip
        pip install -r "!PROJECT_DIR!requirements.txt"
        if !ERRORLEVEL! NEQ 0 (
            call :print_error "Failed to install requirements"
            exit /b 1
        )
        call :print_success "Requirements installed"
    )
) else (
    call :print_success "Virtual environment found"
    call "!VENV_DIR!\Scripts\activate.bat"
)

call :print_success "Virtual environment activated"
goto :eof

:check_env_vars
call :print_info "Checking environment variables..."

if not exist "!PROJECT_DIR!.env" (
    call :print_error ".env file not found"
    echo Please copy .env.example to .env and fill in your API keys
    exit /b 1
)

REM Load .env file (simplified for Windows)
for /f "usebackq tokens=1,* delims==" %%a in ("!PROJECT_DIR!.env") do (
    set "line=%%a"
    set "value=%%b"
    REM Skip comments and empty lines
    if not "!line:~0,1!"=="#" if not "!line!"=="" (
        set "%%a=%%b"
    )
)

REM Check required variables
if "!GOOGLE_API_KEY!"=="" if "!OPENAI_API_KEY!"=="" if "!ANTHROPIC_API_KEY!"=="" (
    call :print_error "No API key found in .env file"
    echo Please set at least one API key (GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)
    exit /b 1
)

call :print_success "Environment variables validated"
goto :eof

:check_port
set "PORT=%~1"
set "SERVICE=%~2"

netstat -ano | findstr ":%PORT% " >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    call :print_warning "Port %PORT% is already in use (needed for %SERVICE%)"
    set /p "CONTINUE=Do you want to continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        exit /b 1
    )
) else (
    call :print_success "Port %PORT% is available for %SERVICE%"
)
goto :eof

:start_backend
call :print_info "Starting backend service on port !BACKEND_PORT!..."

cd /d "!PROJECT_DIR!"

start /b cmd /c "uvicorn backend.app.main:app --host 0.0.0.0 --port !BACKEND_PORT! --reload > backend.log 2>&1"

REM Wait and check if started
timeout /t 3 /nobreak >nul

REM Check if port is now in use (indicates service started)
netstat -ano | findstr ":!BACKEND_PORT! " >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    call :print_success "Backend started successfully"
    
    REM Try to get health status
    timeout /t 2 /nobreak >nul
    curl -s "http://localhost:!BACKEND_PORT!/health" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        call :print_success "Backend health check passed"
    ) else (
        call :print_warning "Backend health check failed, but service is running"
    )
) else (
    call :print_error "Failed to start backend service"
    type backend.log
    exit /b 1
)

goto :eof

:start_frontend
call :print_info "Starting frontend service on port !FRONTEND_PORT!..."

cd /d "!PROJECT_DIR!"

start /b cmd /c "streamlit run frontend/app.py --server.port !FRONTEND_PORT! --server.headless true > frontend.log 2>&1"

REM Wait and check if started
timeout /t 5 /nobreak >nul

REM Check if port is now in use
netstat -ano | findstr ":!FRONTEND_PORT! " >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    call :print_success "Frontend started successfully"
) else (
    call :print_error "Failed to start frontend service"
    type frontend.log
    exit /b 1
)

goto :eof

:show_status
echo.
call :print_success "IELTS AI Coach is now running!"
echo.
echo Services:
echo   - Backend API:  http://localhost:!BACKEND_PORT!
echo   - Frontend App: http://localhost:!FRONTEND_PORT!
echo   - API Docs:     http://localhost:!BACKEND_PORT!/docs
echo.
echo Logs:
echo   - Backend:  !PROJECT_DIR!backend.log
echo   - Frontend: !PROJECT_DIR!frontend.log
echo.
echo To stop services:
echo   - Press Ctrl+C or close this window
echo   - Or run: stop.bat
echo.
goto :eof
