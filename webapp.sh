#!/bin/bash

# olgFeast Web Application Manager
# Usage: ./webapp.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/fastapi_app"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"
BACKEND_LOG_FILE="$SCRIPT_DIR/backend.log"
FRONTEND_LOG_FILE="$SCRIPT_DIR/frontend.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo "=========================================="
    echo "🚀 olgFeast Web Application Manager"
    echo "=========================================="
}

# Check if a process is running
is_process_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Start backend server
start_backend() {
    log_info "Starting backend server..."
    
    if is_process_running "$BACKEND_PID_FILE"; then
        log_warning "Backend server is already running"
        return 0
    fi
    
    cd "$BACKEND_DIR" || {
        log_error "Failed to change to backend directory"
        return 1
    }
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found in $BACKEND_DIR"
        log_info "Please run: cd $BACKEND_DIR && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    # Activate virtual environment and start server
    nohup bash -c "
        source venv/bin/activate
        python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    " > "$BACKEND_LOG_FILE" 2>&1 &
    
    local backend_pid=$!
    echo "$backend_pid" > "$BACKEND_PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if is_process_running "$BACKEND_PID_FILE"; then
        log_success "Backend server started (PID: $backend_pid)"
        log_info "Backend API: http://127.0.0.1:8000"
        log_info "API Docs: http://127.0.0.1:8000/docs"
        log_info "Health Check: http://127.0.0.1:8000/health"
        return 0
    else
        log_error "Failed to start backend server"
        log_info "Check logs: tail -f $BACKEND_LOG_FILE"
        return 1
    fi
}

# Start frontend server
start_frontend() {
    log_info "Starting frontend server..."
    
    if is_process_running "$FRONTEND_PID_FILE"; then
        log_warning "Frontend server is already running"
        return 0
    fi
    
    cd "$FRONTEND_DIR" || {
        log_error "Failed to change to frontend directory"
        return 1
    }
    
    # Check if Node.js and npm are installed
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        log_info "Please install Node.js and npm:"
        log_info "  sudo pacman -S nodejs npm"
        log_info "  Or use nvm: https://github.com/nvm-sh/nvm"
        return 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        log_info "Please install npm: sudo pacman -S npm"
        return 1
    fi
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install || {
            log_error "Failed to install frontend dependencies"
            return 1
        }
    fi
    
    # Start frontend server
    nohup npm start > "$FRONTEND_LOG_FILE" 2>&1 &
    
    local frontend_pid=$!
    echo "$frontend_pid" > "$FRONTEND_PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 5
    if is_process_running "$FRONTEND_PID_FILE"; then
        log_success "Frontend server started (PID: $frontend_pid)"
        log_info "Frontend App: http://localhost:3000"
        return 0
    else
        log_error "Failed to start frontend server"
        log_info "Check logs: tail -f $FRONTEND_LOG_FILE"
        return 1
    fi
}

# Stop backend server
stop_backend() {
    log_info "Stopping backend server..."
    
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "Backend server didn't stop gracefully, force killing..."
                kill -9 "$pid" 2>/dev/null
            fi
            log_success "Backend server stopped"
        else
            log_warning "Backend server was not running"
        fi
        rm -f "$BACKEND_PID_FILE"
    else
        log_warning "Backend server was not running"
    fi
}

# Stop frontend server
stop_frontend() {
    log_info "Stopping frontend server..."
    
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "Frontend server didn't stop gracefully, force killing..."
                kill -9 "$pid" 2>/dev/null
            fi
            log_success "Frontend server stopped"
        else
            log_warning "Frontend server was not running"
        fi
        rm -f "$FRONTEND_PID_FILE"
    else
        log_warning "Frontend server was not running"
    fi
}

# Show status
show_status() {
    print_header
    echo
    
    # Backend status
    if is_process_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        log_success "Backend server is running (PID: $backend_pid)"
        log_info "  • API: http://127.0.0.1:8000"
        log_info "  • Docs: http://127.0.0.1:8000/docs"
        log_info "  • Health: http://127.0.0.1:8000/health"
    else
        log_warning "Backend server is not running"
    fi
    
    echo
    
    # Frontend status
    if is_process_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        log_success "Frontend server is running (PID: $frontend_pid)"
        log_info "  • App: http://localhost:3000"
    else
        log_warning "Frontend server is not running"
    fi
    
    echo
    
    # WebSocket status (if backend is running)
    if is_process_running "$BACKEND_PID_FILE"; then
        log_info "WebSocket endpoints:"
        log_info "  • Kitchen Display: ws://127.0.0.1:8000/ws/kitchen/display"
        log_info "  • Order Updates: ws://127.0.0.1:8000/ws/orders/updates"
        log_info "  • Admin Dashboard: ws://127.0.0.1:8000/ws/admin/dashboard"
    fi
}

# Show logs
show_logs() {
    local service=$1
    
    case $service in
        "backend")
            if [ -f "$BACKEND_LOG_FILE" ]; then
                log_info "Backend logs (press Ctrl+C to exit):"
                tail -f "$BACKEND_LOG_FILE"
            else
                log_warning "Backend log file not found"
            fi
            ;;
        "frontend")
            if [ -f "$FRONTEND_LOG_FILE" ]; then
                log_info "Frontend logs (press Ctrl+C to exit):"
                tail -f "$FRONTEND_LOG_FILE"
            else
                log_warning "Frontend log file not found"
            fi
            ;;
        "all"|"")
            log_info "Showing all logs (press Ctrl+C to exit):"
            if [ -f "$BACKEND_LOG_FILE" ] && [ -f "$FRONTEND_LOG_FILE" ]; then
                tail -f "$BACKEND_LOG_FILE" "$FRONTEND_LOG_FILE"
            elif [ -f "$BACKEND_LOG_FILE" ]; then
                tail -f "$BACKEND_LOG_FILE"
            elif [ -f "$FRONTEND_LOG_FILE" ]; then
                tail -f "$FRONTEND_LOG_FILE"
            else
                log_warning "No log files found"
            fi
            ;;
        *)
            log_error "Invalid log service. Use: backend, frontend, or all"
            exit 1
            ;;
    esac
}

# Main function
main() {
    local command=$1
    local subcommand=$2
    
    case $command in
        "start")
            print_header
            echo
            start_backend
            echo
            start_frontend
            echo
            log_success "Webapp startup complete!"
            echo
            show_status
            ;;
        "stop")
            print_header
            echo
            stop_frontend
            echo
            stop_backend
            echo
            log_success "Webapp shutdown complete!"
            ;;
        "restart")
            print_header
            echo
            log_info "Restarting webapp..."
            echo
            stop_frontend
            stop_backend
            sleep 2
            start_backend
            echo
            start_frontend
            echo
            log_success "Webapp restart complete!"
            echo
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$subcommand"
            ;;
        "help"|"--help"|"-h"|"")
            print_header
            echo
            echo "Usage: $0 [command] [options]"
            echo
            echo "Commands:"
            echo "  start     Start both backend and frontend servers"
            echo "  stop      Stop both backend and frontend servers"
            echo "  restart   Restart both servers"
            echo "  status    Show status of both servers"
            echo "  logs      Show logs [backend|frontend|all]"
            echo "  help      Show this help message"
            echo
            echo "Examples:"
            echo "  $0 start           # Start the entire webapp"
            echo "  $0 stop            # Stop the entire webapp"
            echo "  $0 restart         # Restart the entire webapp"
            echo "  $0 status          # Check status"
            echo "  $0 logs backend    # Show backend logs"
            echo "  $0 logs frontend   # Show frontend logs"
            echo "  $0 logs all        # Show all logs"
            echo
            echo "Log files:"
            echo "  Backend:  $BACKEND_LOG_FILE"
            echo "  Frontend: $FRONTEND_LOG_FILE"
            echo "  PIDs:     $BACKEND_PID_FILE, $FRONTEND_PID_FILE"
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
