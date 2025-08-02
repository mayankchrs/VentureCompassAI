@echo off
REM VentureCompass AI Development Script for Windows

setlocal EnableDelayedExpansion

REM Colors (limited support in Windows CMD)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "BOLD=[1m"
set "NC=[0m"

:print_header
echo.
echo %BLUE%%BOLD%====================================================
echo   %~1
echo ====================================================%NC%
echo.
goto :eof

:print_success
echo %GREEN%[OK] %~1%NC%
goto :eof

:print_error
echo %RED%[ERROR] %~1%NC%
goto :eof

:print_warning
echo %YELLOW%[WARNING] %~1%NC%
goto :eof

:check_dependencies
call :print_header "Checking Dependencies"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Python not found. Please install Python 3.11+"
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do call :print_success "Python: %%i"
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Node.js not found. Please install Node.js 18+"
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do call :print_success "Node.js: %%i"
)

REM Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "npm not found. Please install npm"
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do call :print_success "npm: %%i"
)
goto :eof

:setup
call :print_header "Setting Up VentureCompass AI"

call :check_dependencies
if %errorlevel% neq 0 exit /b 1

REM Install root dependencies
call :print_success "Installing root dependencies..."
npm install
if %errorlevel% neq 0 (
    call :print_error "Failed to install root dependencies"
    exit /b 1
)

REM Backend setup
call :print_success "Setting up backend..."
cd backend

if not exist ".venv" (
    python -m venv .venv
    call :print_success "Created Python virtual environment"
)

call .venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    call :print_error "Failed to install Python dependencies"
    exit /b 1
)
call :print_success "Installed Python dependencies"

if not exist ".env" (
    copy .env.example .env >nul 2>&1
    call :print_warning "Created .env from example. Please configure your API keys!"
)

cd ..

REM Frontend setup
call :print_success "Setting up frontend..."
cd frontend
npm install
if %errorlevel% neq 0 (
    call :print_error "Failed to install frontend dependencies"
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul 2>&1 || echo VITE_API_BASE_URL=http://localhost:8000/api > .env
    call :print_success "Created frontend .env"
)

cd ..

call :print_success "Setup complete!"
echo.
echo Next steps:
echo   1. Configure API keys in backend\.env
echo   2. Start MongoDB (local or Atlas)
echo   3. Run: scripts\dev.bat start
goto :eof

:start_dev
call :print_header "Starting Development Servers"

REM Check MongoDB connection
echo [INFO] Checking MongoDB connection...
cd backend
python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db()); print('[OK] MongoDB connection successful')" 2>nul || call :print_warning "MongoDB connection issues detected"
cd ..

call :print_success "Starting servers..."
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop servers

REM Use npm script if available
if exist "package.json" (
    npm run dev
) else (
    REM Fallback to manual startup
    call :print_warning "Using manual server startup"
    echo Please run these commands in separate terminals:
    echo   1. cd backend ^&^& .venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload
    echo   2. cd frontend ^&^& npm run dev
)
goto :eof

:test_all
call :print_header "Running All Tests"

call :test_backend
call :test_frontend

call :print_success "All tests completed!"
goto :eof

:test_backend
call :print_success "Testing backend..."
cd backend

echo   [INFO] Testing MongoDB connection...
python -c "import asyncio; from app.core.database import init_db, get_database; async def test(): await init_db(); db = get_database(); result = await db.command('ping'); print(f'    Database: {db.name}'); asyncio.run(test())" || call :print_error "Database test failed"

echo   [INFO] Testing agent orchestration...
python -c "from app.agents.orchestrator import VentureCompassOrchestrator; orchestrator = VentureCompassOrchestrator(); print('    Orchestrator initialized successfully')" || call :print_error "Agent test failed"

cd ..
call :print_success "Backend tests completed"
goto :eof

:test_frontend
call :print_success "Testing frontend..."
cd frontend

npm run build || call :print_error "Frontend build failed"

cd ..
call :print_success "Frontend tests completed"
goto :eof

:db_test
call :print_header "Testing Database Connection"
cd backend
python -c "import asyncio; from app.core.database import init_db, get_database; async def test_connection(): await init_db(); db = get_database(); result = await db.command('ping'); print('[OK] MongoDB connection successful!'); print(f'   Database: {db.name}'); collections = await db.list_collection_names(); print(f'   Collections: {len(collections)}'); [print(f'     - {col}: {await db[col].count_documents({})} documents') for col in collections]; asyncio.run(test_connection())"
cd ..
goto :eof

:show_status
call :print_header "VentureCompass AI Project Status"

echo Project Structure:
echo    Root: %CD%
if exist "backend" (
    echo    Backend: [OK] Present
) else (
    echo    Backend: [MISSING]
)
if exist "frontend" (
    echo    Frontend: [OK] Present
) else (
    echo    Frontend: [MISSING]
)

echo.
echo Environment:
if exist "backend\.env" (
    echo    Backend .env: [OK] Present
) else (
    echo    Backend .env: [MISSING]
)
if exist "frontend\.env" (
    echo    Frontend .env: [OK] Present
) else (
    echo    Frontend .env: [MISSING]
)
if exist "backend\.venv" (
    echo    Python venv: [OK] Present
) else (
    echo    Python venv: [MISSING]
)
if exist "frontend\node_modules" (
    echo    Node modules: [OK] Present
) else (
    echo    Node modules: [MISSING]
)

echo.
echo Services:
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo    Backend (8000): [OK] Running
) else (
    echo    Backend (8000): [NOT RUNNING]
)

curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% equ 0 (
    echo    Frontend (5173): [OK] Running
) else (
    echo    Frontend (5173): [NOT RUNNING]
)
goto :eof

:clean_all
call :print_header "Cleaning Project"

echo [INFO] Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul

echo [INFO] Cleaning Node artifacts...
if exist "frontend\dist" rd /s /q "frontend\dist" 2>nul
if exist "frontend\node_modules\.vite" rd /s /q "frontend\node_modules\.vite" 2>nul

call :print_success "Cleanup complete!"
goto :eof

:main
if "%1"=="setup" (
    call :setup
) else if "%1"=="start" (
    call :start_dev
) else if "%1"=="dev" (
    call :start_dev
) else if "%1"=="test" (
    call :test_all
) else if "%1"=="test-backend" (
    call :test_backend
) else if "%1"=="test-frontend" (
    call :test_frontend
) else if "%1"=="db-test" (
    call :db_test
) else if "%1"=="status" (
    call :show_status
) else if "%1"=="clean" (
    call :clean_all
) else (
    echo [BLUE][BOLD]VentureCompass AI Development Script[NC]
    echo.
    echo Usage: scripts\dev.bat [command]
    echo.
    echo Commands:
    echo   setup          Set up development environment
    echo   start^|dev      Start development servers
    echo   test           Run all tests
    echo   test-backend   Run backend tests only
    echo   test-frontend  Run frontend tests only
    echo   db-test        Test database connection
    echo   status         Show project status
    echo   clean          Clean build artifacts
    echo   help           Show this help
    echo.
    echo Examples:
    echo   scripts\dev.bat setup    # First time setup
    echo   scripts\dev.bat start    # Start development
    echo   scripts\dev.bat status   # Check status
)

call :main %*