# 🚀 VentureCompass AI v2.0 - Project Makefile
# Cross-platform development automation for 8-agent startup intelligence platform
# Primary interface leveraging npm scripts and platform-specific scripts

.PHONY: help setup dev backend frontend test clean build deploy status install db-test db-reset test-be test-fe test-api lint logs check-env check-deps

# Default target - show help
help:
	@echo "🎯 VentureCompass AI v2.0 - 8-Agent Intelligence Platform"
	@echo "=========================================================="
	@echo ""
	@echo "🏗️  SETUP & DEVELOPMENT:"
	@echo "  make install      - Install all dependencies"
	@echo "  make setup        - Complete environment setup (first time)"
	@echo "  make dev          - Start both backend and frontend servers"
	@echo "  make backend      - Start backend server only (port 8000)"
	@echo "  make frontend     - Start frontend server only (port 5173)"
	@echo ""
	@echo "🗄️  DATABASE MANAGEMENT:"
	@echo "  make db-test      - Test MongoDB Atlas connection"
	@echo "  make db-reset     - Reset database (⚠️  WARNING: deletes all data)"
	@echo ""
	@echo "🧪 TESTING & QUALITY:"
	@echo "  make test         - Run all tests (backend + frontend)"
	@echo "  make test-be      - Run backend tests only"
	@echo "  make test-fe      - Run frontend tests only"
	@echo "  make test-api     - Test API endpoints"
	@echo "  make lint         - Run all linters and type checks"
	@echo ""
	@echo "🏗️  BUILD & DEPLOYMENT:"
	@echo "  make build        - Build production artifacts"
	@echo "  make clean        - Clean build artifacts and caches"
	@echo "  make check-env    - Verify environment configuration"
	@echo "  make check-deps   - Check dependency versions"
	@echo ""
	@echo "📊 MONITORING & DEBUGGING:"
	@echo "  make status       - Show comprehensive project status"
	@echo "  make logs         - View application logs"
	@echo ""
	@echo "🔗 QUICK ACCESS URLS (when running):"
	@echo "  🌐 Frontend:       http://localhost:5173"
	@echo "  ⚡ Backend API:    http://localhost:8000"
	@echo "  📚 API Docs:       http://localhost:8000/docs"
	@echo "  🔧 API Admin:      http://localhost:8000/redoc"
	@echo ""
	@echo "💡 ALTERNATIVE INTERFACES:"
	@echo "  npm run <command>        - Use npm scripts directly"
	@echo "  ./scripts/dev.sh         - Unix/Linux/macOS script"
	@echo "  scripts\\dev.bat          - Windows batch script"
	@echo ""
	@echo "🎯 TAVILY ASSIGNMENT FEATURES:"
	@echo "  ✅ 8-Agent LangGraph orchestration"
	@echo "  ✅ Complete Tavily API integration (Search, Map, Crawl, Extract)"
	@echo "  ✅ Budget-optimized ($10 OpenAI limit)"
	@echo "  ✅ Investment-grade analysis reports"

# Platform detection for cross-platform compatibility
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")
IS_WINDOWS := $(findstring Windows,$(UNAME_S))
NPM := $(shell command -v npm 2> /dev/null)
PYTHON := $(shell command -v python 2> /dev/null || command -v python3 2> /dev/null)

# Color codes for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Helper function to print colored output
define print_status
	@echo "$(GREEN)[INFO]$(NC) $(1)"
endef

define print_warning
	@echo "$(YELLOW)[WARNING]$(NC) $(1)"
endef

define print_error
	@echo "$(RED)[ERROR]$(NC) $(1)"
endef

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

install:
	$(call print_status,"Installing dependencies...")
ifdef NPM
	@echo "📦 Installing root package dependencies..."
	npm install
else
	$(call print_warning,"npm not found, installing dependencies manually...")
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "📦 Installing backend dependencies..."
	cd backend && $(PYTHON) -m pip install -r requirements.txt
endif
	$(call print_status,"Dependencies installed successfully!")

setup: check-deps
	$(call print_status,"Setting up VentureCompass AI development environment...")
ifdef IS_WINDOWS
	@echo "🔧 Windows detected - using npm scripts"
	npm run setup
else
	@echo "🔧 Unix/Linux/macOS detected - using shell script"
	@chmod +x scripts/dev.sh
	./scripts/dev.sh setup
endif
	$(call print_status,"Environment setup complete!")
	@echo ""
	@echo "$(GREEN)🎉 Setup Complete! Next steps:$(NC)"
	@echo "  1. Configure API keys in backend/.env"
	@echo "  2. Run 'make dev' to start both servers"
	@echo "  3. Visit http://localhost:5173 to start analyzing!"

# =============================================================================
# DEVELOPMENT SERVERS
# =============================================================================

dev:
	$(call print_status,"Starting VentureCompass AI development servers...")
ifdef IS_WINDOWS
	npm run dev
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh start
endif

backend:
	$(call print_status,"Starting backend server (FastAPI + 8 agents)...")
ifdef NPM
	npm run dev:backend
else
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
endif

frontend:
	$(call print_status,"Starting frontend server (React + TypeScript)...")
ifdef NPM
	npm run dev:frontend
else
	cd frontend && npm run dev
endif

# =============================================================================
# DATABASE MANAGEMENT
# =============================================================================

db-test:
	$(call print_status,"Testing MongoDB Atlas connection...")
ifdef IS_WINDOWS
	npm run db:test
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh db-test
endif

db-reset:
	$(call print_warning,"⚠️  WARNING: This will DELETE ALL DATA!")
	@echo "Press Ctrl+C to cancel, or press Enter to continue..."
	@read dummy
ifdef IS_WINDOWS
	npm run db:reset
else
	@echo "🗄️ Resetting MongoDB database..."
	cd backend && $(PYTHON) -c "import asyncio; from app.core.database import init_db, get_database; async def reset(): await init_db(); db = get_database(); collections = await db.list_collection_names(); [await db[c].drop() for c in collections]; print('✅ Database reset complete'); asyncio.run(reset())"
endif

# =============================================================================
# TESTING & QUALITY ASSURANCE
# =============================================================================

test:
	$(call print_status,"Running all tests...")
ifdef IS_WINDOWS
	npm run test
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh test
endif

test-be:
	$(call print_status,"Running backend tests...")
ifdef IS_WINDOWS
	npm run test:backend
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh test-backend
endif

test-fe:
	$(call print_status,"Running frontend tests...")
ifdef IS_WINDOWS
	npm run test:frontend
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh test-frontend
endif

test-api:
	$(call print_status,"Testing API endpoints...")
	@echo "🧪 Testing API connectivity and endpoints..."
	node scripts/test-backend-api.js

lint:
	$(call print_status,"Running code quality checks...")
ifdef NPM
	@echo "🔍 ESLint + TypeScript checks..."
	npm run lint
	@echo "🔍 TypeScript compilation check..."
	cd frontend && npm run type-check
else
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint
	@echo "🔍 TypeScript type checking..."
	cd frontend && npm run type-check
endif
	$(call print_status,"Code quality checks completed!")

# =============================================================================
# BUILD & DEPLOYMENT
# =============================================================================

build:
	$(call print_status,"Building production artifacts...")
ifdef NPM
	npm run build
else
	@echo "🏗️ Building frontend..."
	cd frontend && npm run build
	@echo "✅ Frontend build complete!"
endif
	@echo "📦 Production build artifacts:"
	@ls -la frontend/.next/ 2>/dev/null || echo "  Frontend build in frontend/.next/"
	$(call print_status,"Production build completed!")

clean:
	$(call print_status,"Cleaning build artifacts and caches...")
ifdef IS_WINDOWS
	npm run clean
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh clean
endif
	$(call print_status,"Clean completed!")

# =============================================================================
# ENVIRONMENT & DEPENDENCY CHECKING
# =============================================================================

check-env:
	$(call print_status,"Checking environment configuration...")
	@echo "🔍 Environment Check Results:"
	@echo "  Node.js: $$(node --version 2>/dev/null || echo 'Not found')"
	@echo "  npm: $$(npm --version 2>/dev/null || echo 'Not found')"
	@echo "  Python: $$($(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo "  Platform: $(UNAME_S)"
	@echo ""
	@echo "📁 Configuration Files:"
	@echo "  Backend .env: $$(test -f backend/.env && echo '✅ Found' || echo '❌ Missing')"
	@echo "  Frontend .env: $$(test -f frontend/.env && echo '✅ Found' || echo '❌ Missing')"
	@echo ""
	@echo "🔑 API Keys Check (backend/.env):"
	@echo "  TAVILY_API_KEY: $$(grep -q 'TAVILY_API_KEY=' backend/.env 2>/dev/null && echo '✅ Set' || echo '❌ Missing')"
	@echo "  LLM_API_KEY: $$(grep -q 'LLM_API_KEY=' backend/.env 2>/dev/null && echo '✅ Set' || echo '❌ Missing')"
	@echo "  MONGODB_URI: $$(grep -q 'MONGODB_URI=' backend/.env 2>/dev/null && echo '✅ Set' || echo '❌ Missing')"

check-deps:
	$(call print_status,"Checking dependency versions...")
	@echo "📦 Dependency Version Check:"
ifndef NPM
	$(call print_error,"npm is required but not found. Please install Node.js 18+")
	@exit 1
endif
ifndef PYTHON
	$(call print_error,"Python is required but not found. Please install Python 3.9+")
	@exit 1
endif
	@echo "  ✅ npm: $$(npm --version)"
	@echo "  ✅ Node.js: $$(node --version)"
	@echo "  ✅ Python: $$($(PYTHON) --version)"
	$(call print_status,"Dependencies check passed!")

# =============================================================================
# MONITORING & DEBUGGING
# =============================================================================

status:
	$(call print_status,"VentureCompass AI Project Status")
	@echo "================================================"
ifdef IS_WINDOWS
	@echo "🎯 Status via Node.js script..."
	node scripts/status.js
else
	@chmod +x scripts/dev.sh
	./scripts/dev.sh status
endif
	@echo ""
	@echo "🚀 Quick Start Commands:"
	@echo "  make dev          # Start both servers"
	@echo "  make test         # Run all tests"
	@echo "  make build        # Build for production"

logs:
	$(call print_status,"Checking application logs...")
	@echo "📋 Recent log entries:"
	@tail -n 50 backend/app.log 2>/dev/null || tail -n 50 logs/app.log 2>/dev/null || echo "  No log files found"
	@echo ""
	@echo "💡 Tip: Logs are also displayed in the terminal when running 'make dev'"

# =============================================================================
# CONVENIENCE SHORTCUTS
# =============================================================================

start: dev
	@echo "Alias for 'make dev'"

stop:
	$(call print_warning,"To stop servers, use Ctrl+C in the terminal running them")
	@echo "Or find and kill the processes:"
	@echo "  lsof -ti:8000 | xargs kill    # Kill backend (macOS/Linux)"
	@echo "  lsof -ti:5173 | xargs kill    # Kill frontend (macOS/Linux)"
	@echo "  netstat -ano | findstr :8000  # Find backend PID (Windows)"

restart: stop dev

# =============================================================================
# SPECIALIZED HELP
# =============================================================================

help-docker:
	@echo "🐳 Docker Support (Future Enhancement):"
	@echo "  docker-compose up      - Start with Docker"
	@echo "  docker-compose down    - Stop Docker services"
	@echo "  docker-compose build   - Build Docker images"
	@echo ""
	@echo "📝 Note: Docker configuration will be added in future versions"

help-prod:
	@echo "🚀 Production Deployment Guide:"
	@echo "  1. make build           - Build production artifacts"
	@echo "  2. Configure production environment variables"
	@echo "  3. Deploy backend: uvicorn app.main:app --host 0.0.0.0 --port 8000"
	@echo "  4. Deploy frontend: Serve frontend/.next/ with web server"
	@echo "  5. Configure domain and SSL certificates"
	@echo ""
	@echo "🌐 Environment Setup:"
	@echo "  • MongoDB Atlas: Production cluster"
	@echo "  • API Keys: Production Tavily + OpenAI keys"
	@echo "  • Security: CORS, rate limiting, auth"

help-agents:
	@echo "🤖 8-Agent Intelligence System:"
	@echo "  Phase 1 - Discovery:"
	@echo "    🌐 Discovery Agent    - Maps digital presence (Tavily Map API)"
	@echo ""
	@echo "  Phase 2 - Parallel Research:"
	@echo "    📰 News Agent         - Funding & partnerships (Tavily Search API)"
	@echo "    🛡️  Patent Agent       - IP portfolios & innovation"
	@echo "    👥 Founder Agent      - Leadership team analysis"
	@echo "    📈 Competitive Agent  - Market positioning"
	@echo "    🔍 DeepDive Agent     - Content analysis (Tavily Crawl + Extract)"
	@echo ""
	@echo "  Phase 3 - Synthesis:"
	@echo "    ✅ Verification Agent - Fact-checking & confidence scoring"
	@echo "    🧠 Synthesis Agent    - Final report generation"
	@echo ""
	@echo "💡 Each agent uses specialized prompts and tools for optimal results"

# =============================================================================
# TROUBLESHOOTING
# =============================================================================

doctor:
	$(call print_status,"Running project health check...")
	@echo "🩺 VentureCompass AI Health Check"
	@echo "=================================="
	@$(MAKE) check-deps
	@echo ""
	@$(MAKE) check-env
	@echo ""
	@echo "🔧 Common Fixes:"
	@echo "  • Missing dependencies: make clean && make setup"
	@echo "  • Port conflicts: See 'make stop' for process management"
	@echo "  • API key issues: Check backend/.env configuration"
	@echo "  • Database issues: Run 'make db-test'"

# =============================================================================
# VERSION INFO
# =============================================================================

version:
	@echo "🚀 VentureCompass AI v2.0"
	@echo "8-Agent Startup Intelligence Platform"
	@echo ""
	@echo "🎯 Built for Tavily Lead GenAI Engineer Assignment"
	@echo "✨ Complete Tavily API Integration Showcase"
	@echo "🤖 Advanced LangGraph Multi-Agent Orchestration"
	@echo "💰 Budget-Optimized AI Development ($10 constraint)"