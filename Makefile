# VentureCompass AI Project Makefile
# Primary command interface leveraging npm scripts and shell scripts for cross-platform compatibility

.PHONY: help setup dev backend frontend test clean build deploy status install db-test db-reset test-be test-fe lint logs

# Default target
help:
	@echo "🎯 VentureCompass AI Project Commands"
	@echo "====================================="
	@echo ""
	@echo "🏗️  Setup & Development:"
	@echo "  make install    - Install all dependencies"
	@echo "  make setup      - Complete environment setup"
	@echo "  make dev        - Start both backend and frontend"
	@echo "  make backend    - Start backend server only (port 8000)"
	@echo "  make frontend   - Start frontend server only (port 5173)"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make db-test    - Test MongoDB connection"
	@echo "  make db-reset   - Reset database (⚠️  WARNING: deletes data)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test       - Run all tests (backend + frontend)"
	@echo "  make test-be    - Run backend tests only"
	@echo "  make test-fe    - Run frontend tests only"
	@echo "  make test-api   - Test API endpoints"
	@echo ""
	@echo "🏗️  Build & Deploy:"
	@echo "  make build      - Build production artifacts"
	@echo "  make clean      - Clean build artifacts and caches"
	@echo "  make lint       - Run linters on all code"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make status     - Show project status"
	@echo "  make logs       - View application logs"
	@echo ""
	@echo "🔗 Quick Links (when running):"
	@echo "  Backend API:    http://localhost:8000"
	@echo "  Frontend:       http://localhost:5173"
	@echo "  API Docs:       http://localhost:8000/docs"
	@echo ""
	@echo "💡 Alternative interfaces:"
	@echo "  npm run <command>     - Use npm scripts directly"
	@echo "  ./scripts/dev.sh      - Unix/Linux/macOS script"
	@echo "  scripts\\dev.bat       - Windows batch script"

# Platform detection
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")
NPM := $(shell command -v npm 2> /dev/null)

# Development commands
install:
ifdef NPM
	npm install
else
	@echo "⚠️  npm not found, installing dependencies manually..."
	cd frontend && npm install
	cd backend && python -m pip install -r requirements.txt
endif

setup: 
ifeq ($(UNAME_S),Windows)
	@echo "🔧 Windows setup - using npm scripts"
	npm run setup
else
	@echo "🔧 Unix/Linux/macOS setup - using shell script"
	chmod +x scripts/dev.sh
	./scripts/dev.sh setup
endif

dev:
ifeq ($(UNAME_S),Windows)
	npm run dev
else
	chmod +x scripts/dev.sh
	./scripts/dev.sh start
endif

backend:
ifdef NPM
	npm run dev:backend
else
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
endif

frontend:
ifdef NPM
	npm run dev:frontend
else
	cd frontend && npm run dev
endif

# Database commands
db-test:
ifeq ($(UNAME_S),Windows)
	npm run db:test
else
	./scripts/dev.sh db-test
endif

db-reset:
	@echo "⚠️  WARNING: This will DELETE ALL DATA!"
ifeq ($(UNAME_S),Windows)
	npm run db:reset
else
	cd backend && python -c "import asyncio; from app.core.database import init_db, get_database; async def reset(): await init_db(); db = get_database(); collections = await db.list_collection_names(); [await db[c].drop() for c in collections]; print('Database reset complete'); asyncio.run(reset())"
endif

# Testing commands
test:
ifeq ($(UNAME_S),Windows)
	npm run test
else
	./scripts/dev.sh test
endif

test-be:
ifeq ($(UNAME_S),Windows)
	npm run test:backend
else
	./scripts/dev.sh test-backend
endif

test-fe:
ifeq ($(UNAME_S),Windows)
	npm run test:frontend
else
	./scripts/dev.sh test-frontend
endif

test-api:
	@echo "🧪 Testing API endpoints..."
	node scripts/test-backend-api.js

# Build and utilities
build:
ifdef NPM
	npm run build
else
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "✅ Build complete!"
endif

clean:
ifeq ($(UNAME_S),Windows)
	npm run clean
else
	./scripts/dev.sh clean
endif

lint:
ifdef NPM
	npm run lint
else
	@echo "Linting frontend..."
	cd frontend && npm run lint
endif

# Monitoring
status:
ifeq ($(UNAME_S),Windows)
	@echo "🎯 Status via Node.js script..."
	node scripts/status.js
else
	./scripts/dev.sh status
endif

logs:
	@echo "📋 Checking logs..."
	@tail -n 50 backend/app.log 2>/dev/null || tail -n 50 logs/app.log 2>/dev/null || echo "No log files found"

# Development shortcuts
start: dev
stop:
	@echo "⏹️  To stop servers, use Ctrl+C in the terminal running them"

# Help for specific environments
help-docker:
	@echo "🐳 Docker commands (when implemented):"
	@echo "  docker-compose up    - Start with Docker"
	@echo "  docker-compose down  - Stop Docker services"

help-prod:
	@echo "🚀 Production deployment:"
	@echo "  make build          - Build production artifacts"
	@echo "  make deploy         - Deploy to AWS (requires setup)"