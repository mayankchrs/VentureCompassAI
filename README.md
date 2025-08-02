# VentureCompass AI

AI-powered company intelligence and risk assessment platform that generates investor-grade dossiers with cited research.

## Features

- **Automated Research**: Parallel news and patent discovery using Tavily Search API
- **Risk Assessment**: AI-powered classification and scoring of potential risks
- **Structured Intelligence**: Professional dossiers with citations and evidence
- **Real-time Processing**: Async task processing with status monitoring

## Project Structure

```
VentureCompasAI/
├── backend/                 # FastAPI backend with LangGraph agents
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # Pydantic schemas and data models
│   │   ├── services/       # External API clients (Tavily, LLM)
│   │   └── agents/         # LangGraph orchestration
│   └── requirements.txt
├── frontend/               # React + TypeScript UI
│   └── src/
└── docs/                   # Technical documentation
```

## Quick Start

### 🚀 One-Command Setup (Recommended)

Choose your preferred interface - all are equivalent:

```bash
# Option 1: Makefile (cross-platform)
make setup          # Complete environment setup
make dev            # Start both backend + frontend

# Option 2: npm scripts (Windows-friendly)
npm run setup       # Complete environment setup  
npm run dev         # Start both backend + frontend

# Option 3: Platform-specific scripts
./scripts/dev.sh setup && ./scripts/dev.sh start    # Unix/Linux/macOS
scripts\dev.bat setup && scripts\dev.bat start      # Windows
```

### 🔧 Available Commands

| Task | Makefile | npm | Platform Script |
|------|----------|-----|----------------|
| **First-time setup** | `make setup` | `npm run setup` | `./scripts/dev.sh setup` |
| **Start both servers** | `make dev` | `npm run dev` | `./scripts/dev.sh start` |
| **Backend only** | `make backend` | `npm run dev:backend` | - |
| **Frontend only** | `make frontend` | `npm run dev:frontend` | - |
| **Run all tests** | `make test` | `npm run test` | `./scripts/dev.sh test` |
| **Test database** | `make db-test` | `npm run db:test` | `./scripts/dev.sh db-test` |
| **Check status** | `make status` | `npm run status` | `./scripts/dev.sh status` |
| **Build production** | `make build` | `npm run build` | - |
| **Clean artifacts** | `make clean` | `npm run clean` | `./scripts/dev.sh clean` |

### 💡 Quick Access URLs (when running)

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:5173  
- **API Documentation**: http://localhost:8000/docs
- **API Admin**: http://localhost:8000/redoc

### 🆘 Manual Setup (if automation fails)

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database URI
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```

4. Start development server:
   ```bash
   npm run dev
   ```

</details>

## Environment Variables

### Backend (.env)
- `MONGODB_URI`: MongoDB connection string
- `TAVILY_API_KEY`: Tavily Search API key
- `LLM_API_KEY`: OpenAI/Anthropic API key
- `LLM_PROVIDER`: openai|anthropic|azure_openai
- `LLM_MODEL`: Model name (e.g., gpt-4o-mini)

### Frontend (.env)
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000/api)

## API Endpoints

- `POST /api/run` - Create new analysis run
- `GET /api/run/{id}` - Get run status and results
- `GET /api/run/{id}/export.json` - Export full run data

## Tech Stack

**Backend:**
- FastAPI (async web framework)
- LangGraph (agent orchestration)
- MongoDB (data persistence)
- Tavily API (search and discovery)
- OpenAI/Anthropic (LLM processing)

**Frontend:**
- React + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- SWR (data fetching)

## Development

### 🧪 Testing

```bash
# Run all tests
make test                # or npm run test

# Test specific components
make test-api           # Test API endpoints
make test-be            # Backend tests only
make test-fe            # Frontend tests only  
make db-test            # Test database connection
```

### 🗄️ Database Management

```bash
# Test MongoDB connection
make db-test            # or npm run db:test

# Reset database (⚠️ WARNING: Deletes all data)
make db-reset           # or npm run db:reset
```

### 📊 Monitoring

```bash
# Show project status
make status             # or npm run status

# View application logs  
make logs               # Check backend/app.log

# Clean build artifacts
make clean              # or npm run clean
```

### 🔧 Troubleshooting

**Common Issues:**

1. **MongoDB Connection Failed**
   ```bash
   make db-test  # Test connection
   # Check MongoDB Atlas connection string in backend/.env
   ```

2. **Port Already in Use**
   ```bash
   # Kill processes on ports 8000/5173
   lsof -ti:8000 | xargs kill  # macOS/Linux
   netstat -ano | findstr :8000  # Windows
   ```

3. **Missing Dependencies**
   ```bash
   make clean && make setup  # Clean install
   ```

4. **API Keys Not Configured**
   ```bash
   # Edit backend/.env with your keys:
   # TAVILY_API_KEY=your_key_here
   # OPENAI_API_KEY=your_key_here
   ```

### 📚 Further Reading

- **Architecture**: See `docs/technical_doc.txt` for detailed implementation notes
- **API Documentation**: Visit http://localhost:8000/docs when backend is running
- **Project Requirements**: See `docs/PRD_v2.txt` for v2.0 specifications