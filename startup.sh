#!/bin/bash

# IELTS AI Coach - Enhanced Cross-Platform Startup Script
# Supports both Conda and Python venv

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="ielts-coach2"
VENV_DIR="${PROJECT_DIR}/venv"
BACKEND_PORT=8000
FRONTEND_PORT=8501
USE_VENV=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if conda is available
check_environment_managers() {
    print_status "Checking for Python environment managers..."
    
    local CONDA_AVAILABLE=0
    local PYTHON_AVAILABLE=0
    
    if command -v conda &> /dev/null; then
        print_success "Conda found"
        CONDA_AVAILABLE=1
    else
        print_warning "Conda not found or not in PATH"
    fi
    
    if command -v python3 &> /dev/null || command -v python &> /dev/null; then
        print_success "Python found"
        PYTHON_AVAILABLE=1
    else
        print_error "Python not found in PATH"
        print_error "Please install Python 3.9+ first"
        exit 1
    fi
    
    # Determine which environment to use
    if [ $CONDA_AVAILABLE -eq 1 ]; then
        echo ""
        echo "Which environment manager would you like to use?"
        echo "1. Conda (recommended if already installed)"
        echo "2. Python venv (more lightweight)"
        echo ""
        read -p "Enter your choice (1 or 2, default is 1): " ENV_CHOICE
        
        if [ "$ENV_CHOICE" = "2" ]; then
            USE_VENV=1
            print_status "Using Python venv"
        else
            USE_VENV=0
            print_status "Using Conda"
        fi
    else
        USE_VENV=1
        print_status "Using Python venv (Conda not available)"
    fi
}

# Function to setup Python venv
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    # Determine Python command
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    else
        PYTHON_CMD=python
    fi
    
    # Check if venv exists
    if [ ! -d "${VENV_DIR}" ] || [ ! -f "${VENV_DIR}/bin/activate" ]; then
        print_warning "Virtual environment not found, creating..."
        
        ${PYTHON_CMD} -m venv "${VENV_DIR}"
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        
        print_success "Virtual environment created"
        
        # Activate and install requirements
        source "${VENV_DIR}/bin/activate"
        
        if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
            print_status "Installing requirements..."
            pip install --upgrade pip
            pip install -r "${PROJECT_DIR}/requirements.txt"
            
            if [ $? -ne 0 ]; then
                print_error "Failed to install requirements"
                exit 1
            fi
            
            print_success "Requirements installed"
        fi
    else
        print_success "Virtual environment found"
        source "${VENV_DIR}/bin/activate"
    fi
    
    print_success "Virtual environment activated"
}

# Function to setup Conda
setup_conda() {
    print_status "Setting up Conda environment..."
    
    # Check if environment exists
    if ! conda env list | grep -q "^${ENV_NAME} "; then
        print_warning "Environment '${ENV_NAME}' not found"
        
        if [ -f "${PROJECT_DIR}/environment.yml" ]; then
            print_status "Creating environment from environment.yml..."
            conda env create -f "${PROJECT_DIR}/environment.yml"
            if [ $? -ne 0 ]; then
                print_error "Failed to create conda environment"
                exit 1
            fi
            print_success "Environment created successfully"
        else
            print_error "environment.yml not found in ${PROJECT_DIR}"
            exit 1
        fi
    else
        print_success "Environment '${ENV_NAME}' found"
    fi
    
    # Activate environment
    print_status "Activating conda environment: ${ENV_NAME}"
    
    # Initialize conda for bash (if not already done)
    eval "$(conda shell.bash hook)"
    
    # Activate environment
    conda activate "${ENV_NAME}"
    
    print_success "Conda environment activated"
}

# Function to check environment variables
check_env_vars() {
    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        print_error ".env file not found"
        print_error "Please copy .env.example to .env and fill in your API keys"
        exit 1
    fi
    
    # Source the .env file and check for required variables
    set -a
    source "${PROJECT_DIR}/.env"
    set +a
    
    # Check if at least one API key is set
    if [ -z "$GOOGLE_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
        print_error "No API key found in .env file"
        print_error "Please set at least one API key (GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)"
        exit 1
    fi
    
    if [ "$LANGCHAIN_TRACING_V2" = "true" ] && [ -z "$LANGCHAIN_API_KEY" ]; then
        print_warning "LangSmith tracing enabled but LANGCHAIN_API_KEY not set"
    fi
    
    print_success "Environment variables validated"
}

# Function to check if port is available
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        print_warning "Port $port is already in use (needed for $service)"
        print_status "Attempting to find process using port $port..."
        lsof -i :$port
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Port $port is available for $service"
    fi
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    # Check Python imports
    python -c "
import sys
try:
    import langchain
    import langchain_google_genai
    import langgraph
    import fastapi
    import streamlit
    print('✓ All required packages are importable')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"
    
    # Check file structure
    required_files=(
        "backend/app/main.py"
        "backend/app/graph_builder.py"
        "backend/app/graph_nodes.py"
        "backend/app/graph_state.py"
        "frontend/app.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "${PROJECT_DIR}/${file}" ]; then
            print_error "Required file not found: ${file}"
            exit 1
        fi
    done
    
    # Check rubrics directory
    if [ ! -d "${PROJECT_DIR}/backend/rubrics" ]; then
        print_error "Rubrics directory not found"
        exit 1
    fi
    
    print_success "Health checks passed"
}

# Function to start backend service
start_backend() {
    print_status "Starting backend service on port ${BACKEND_PORT}..."
    
    cd "${PROJECT_DIR}"
    
    # Start backend in background
    nohup uvicorn backend.app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait a moment and check if it started successfully
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend started successfully (PID: $BACKEND_PID)"
        echo $BACKEND_PID > backend.pid
        
        # Test health endpoint
        sleep 2
        if curl -s "http://localhost:${BACKEND_PORT}/health" > /dev/null; then
            print_success "Backend health check passed"
        else
            print_warning "Backend health check failed, but service is running"
        fi
    else
        print_error "Failed to start backend service"
        cat backend.log
        exit 1
    fi
}

# Function to start frontend service
start_frontend() {
    print_status "Starting frontend service on port ${FRONTEND_PORT}..."
    
    cd "${PROJECT_DIR}"
    
    # Start frontend in background
    nohup streamlit run frontend/app.py --server.port ${FRONTEND_PORT} --server.headless true > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait a moment and check if it started successfully
    sleep 5
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started successfully (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > frontend.pid
    else
        print_error "Failed to start frontend service"
        cat frontend.log
        exit 1
    fi
}

# Function to show service status
show_status() {
    echo
    print_success "🚀 IELTS AI Coach is now running!"
    echo
    echo "📊 Services:"
    echo "  • Backend API:  http://localhost:${BACKEND_PORT}"
    echo "  • Frontend App: http://localhost:${FRONTEND_PORT}"
    echo "  • API Docs:     http://localhost:${BACKEND_PORT}/docs"
    echo
    echo "📋 Logs:"
    echo "  • Backend:  tail -f ${PROJECT_DIR}/backend.log"
    echo "  • Frontend: tail -f ${PROJECT_DIR}/frontend.log"
    echo
    echo "🛑 To stop services:"
    echo "  • ./startup.sh stop"
    echo
    echo "💡 Environment: $([ $USE_VENV -eq 1 ] && echo 'Python venv' || echo 'Conda')"
    echo
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    # Stop backend
    if [ -f backend.pid ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend stopped"
        fi
        rm -f backend.pid
    fi
    
    # Stop frontend
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend stopped"
        fi
        rm -f frontend.pid
    fi
    
    print_success "All services stopped"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [start|stop|restart|status|logs]"
    echo
    echo "Commands:"
    echo "  start   - Start all services (default)"
    echo "  stop    - Stop all services"
    echo "  restart - Restart all services"
    echo "  status  - Show service status"
    echo "  logs    - Show recent logs"
}

# Function to show logs
show_logs() {
    echo "=== Backend Logs ==="
    if [ -f backend.log ]; then
        tail -20 backend.log
    else
        echo "No backend logs found"
    fi
    
    echo
    echo "=== Frontend Logs ==="
    if [ -f frontend.log ]; then
        tail -20 frontend.log
    else
        echo "No frontend logs found"
    fi
}

# Function to check service status
check_status() {
    echo "=== Service Status ==="
    
    # Check backend
    if [ -f backend.pid ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_success "Backend: Running (PID: $BACKEND_PID)"
        else
            print_error "Backend: Stopped (stale PID file)"
        fi
    else
        print_error "Backend: Stopped"
    fi
    
    # Check frontend
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_success "Frontend: Running (PID: $FRONTEND_PID)"
        else
            print_error "Frontend: Stopped (stale PID file)"
        fi
    else
        print_error "Frontend: Stopped"
    fi
    
    # Show environment info
    if [ -f "${VENV_DIR}/bin/activate" ]; then
        echo "Environment: Python venv"
    else
        echo "Environment: Conda"
    fi
}

# Main execution
main() {
    local command=${1:-start}
    
    case $command in
        "start")
            print_status "Starting IELTS AI Coach..."
            check_environment_managers
            
            if [ $USE_VENV -eq 1 ]; then
                setup_venv
            else
                setup_conda
            fi
            
            check_env_vars
            health_check
            check_port $BACKEND_PORT "Backend API"
            check_port $FRONTEND_PORT "Frontend App"
            start_backend
            start_frontend
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            main start
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
