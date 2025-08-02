#!/bin/bash
# VentureCompass AI Development Script for Unix/Linux/macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}${BOLD}===================================================="
    echo -e "  $1"
    echo -e "====================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python: $PYTHON_VERSION"
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js: $NODE_VERSION"
    else
        print_error "Node.js not found. Please install Node.js 18+"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm: $NPM_VERSION"
    else
        print_error "npm not found. Please install npm"
        exit 1
    fi
}

# Setup function
setup() {
    print_header "Setting Up VentureCompass AI"
    
    check_dependencies
    
    # Install root dependencies
    print_success "Installing root dependencies..."
    npm install
    
    # Backend setup
    print_success "Setting up backend..."
    cd backend
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        print_success "Created Python virtual environment"
    fi
    
    source .venv/bin/activate
    pip install -r requirements.txt
    print_success "Installed Python dependencies"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_warning "Created .env from example. Please configure your API keys!"
    fi
    
    cd ..
    
    # Frontend setup
    print_success "Setting up frontend..."
    cd frontend
    npm install
    
    if [ ! -f ".env" ]; then
        cp .env.example .env 2>/dev/null || echo "VITE_API_BASE_URL=http://localhost:8000/api" > .env
        print_success "Created frontend .env"
    fi
    
    cd ..
    
    print_success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Configure API keys in backend/.env"
    echo "  2. Start MongoDB (local or Atlas)"
    echo "  3. Run: ./scripts/dev.sh start"
}

# Start development servers
start_dev() {
    print_header "Starting Development Servers"
    
    # Check if MongoDB is accessible
    echo "🔍 Checking MongoDB connection..."
    cd backend
    python3 -c "
import asyncio
from app.core.database import init_db
try:
    asyncio.run(init_db())
    print('[OK] MongoDB connection successful')
except Exception as e:
    print(f'[WARNING] MongoDB connection failed: {e}')
    print('Please ensure MongoDB is running')
" || print_warning "MongoDB connection issues detected"
    cd ..
    
    print_success "Starting servers..."
    echo "  Backend:  http://localhost:8000"
    echo "  Frontend: http://localhost:5173"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop servers"
    
    # Use npm script if available, otherwise manual
    if command -v npm &> /dev/null && [ -f "package.json" ]; then
        npm run dev
    else
        # Fallback to manual startup
        trap 'kill $(jobs -p)' EXIT
        
        # Start backend
        cd backend
        source .venv/bin/activate 2>/dev/null || echo "Warning: Virtual env not found"
        python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
        
        # Start frontend
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        # Wait for both processes
        wait $BACKEND_PID $FRONTEND_PID
    fi
}

# Test functions
test_all() {
    print_header "Running All Tests"
    
    test_backend
    test_frontend
    
    print_success "All tests completed!"
}

test_backend() {
    print_success "Testing backend..."
    cd backend
    
    # Test database
    echo "  🔍 Testing MongoDB connection..."
    python3 -c "
import asyncio
from app.core.database import init_db, get_database
async def test():
    await init_db()
    db = get_database()
    result = await db.command('ping')
    print(f'    Database: {db.name}')
asyncio.run(test())
" || print_error "Database test failed"
    
    # Test agents
    echo "  🤖 Testing agent orchestration..."
    python3 -c "
from app.agents.orchestrator import VentureCompassOrchestrator
orchestrator = VentureCompassOrchestrator()
print('    Orchestrator initialized successfully')
" || print_error "Agent test failed"
    
    cd ..
    print_success "Backend tests completed"
}

test_frontend() {
    print_success "Testing frontend..."
    cd frontend
    
    # Type check and build test
    npm run build || print_error "Frontend build failed"
    
    cd ..
    print_success "Frontend tests completed"
}

# Database functions
db_test() {
    print_header "Testing Database Connection"
    cd backend
    python3 -c "
import asyncio
from app.core.database import init_db, get_database

async def test_connection():
    try:
        await init_db()
        db = get_database()
        result = await db.command('ping')
        print('[OK] MongoDB connection successful!')
        print(f'   Database: {db.name}')
        
        collections = await db.list_collection_names()
        print(f'   Collections: {len(collections)}')
        for col in collections:
            count = await db[col].count_documents({})
            print(f'     - {col}: {count} documents')
        
    except Exception as e:
        print(f'[ERROR] Database connection failed: {e}')
        exit(1)

asyncio.run(test_connection())
"
    cd ..
}

# Status function
show_status() {
    print_header "VentureCompass AI Project Status"
    
    echo "📁 Project Structure:"
    echo "   Root: $(pwd)"
    echo "   Backend: $([ -d "backend" ] && echo "✅ Present" || echo "❌ Missing")"
    echo "   Frontend: $([ -d "frontend" ] && echo "✅ Present" || echo "❌ Missing")"
    
    echo ""
    echo "🔧 Environment:"
    echo "   Backend .env: $([ -f "backend/.env" ] && echo "✅ Present" || echo "❌ Missing")"
    echo "   Frontend .env: $([ -f "frontend/.env" ] && echo "✅ Present" || echo "❌ Missing")"
    echo "   Python venv: $([ -d "backend/.venv" ] && echo "✅ Present" || echo "❌ Missing")"
    echo "   Node modules: $([ -d "frontend/node_modules" ] && echo "✅ Present" || echo "❌ Missing")"
    
    echo ""
    echo "🚀 Services:"
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "   Backend (8000): ✅ Running"
    else
        echo "   Backend (8000): ❌ Not running"
    fi
    
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        echo "   Frontend (5173): ✅ Running"
    else
        echo "   Frontend (5173): ❌ Not running"
    fi
}

# Clean function
clean_all() {
    print_header "Cleaning Project"
    
    echo "🧹 Cleaning Python cache..."
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    echo "🧹 Cleaning Node artifacts..."
    [ -d "frontend/dist" ] && rm -rf frontend/dist
    [ -d "frontend/node_modules/.vite" ] && rm -rf frontend/node_modules/.vite
    
    print_success "Cleanup complete!"
}

# Main script logic
case "${1:-help}" in
    "setup")
        setup
        ;;
    "start"|"dev")
        start_dev
        ;;
    "test")
        test_all
        ;;
    "test-backend")
        test_backend
        ;;
    "test-frontend")
        test_frontend
        ;;
    "db-test")
        db_test
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_all
        ;;
    "help"|*)
        echo "🎯 VentureCompass AI Development Script"
        echo ""
        echo "Usage: ./scripts/dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  setup          Set up development environment"
        echo "  start|dev      Start development servers"
        echo "  test           Run all tests"
        echo "  test-backend   Run backend tests only"
        echo "  test-frontend  Run frontend tests only"
        echo "  db-test        Test database connection"
        echo "  status         Show project status"
        echo "  clean          Clean build artifacts"
        echo "  help           Show this help"
        echo ""
        echo "Examples:"
        echo "  ./scripts/dev.sh setup    # First time setup"
        echo "  ./scripts/dev.sh start    # Start development"
        echo "  ./scripts/dev.sh status   # Check status"
        ;;
esac