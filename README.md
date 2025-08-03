# 🚀 VentureCompass AI v2.0

**AI-Powered Startup Intelligence Platform with 8-Agent LangGraph Orchestration**

VentureCompass AI is a sophisticated investment intelligence platform that generates comprehensive startup analysis through coordinated AI agents. Built for the Tavily Lead GenAI Engineer assignment, it showcases complete Tavily API integration and advanced LangGraph orchestration patterns.

## ✨ Features

- **🤖 8-Agent Intelligence System**: Multi-phase coordinated analysis with Discovery, News, Patent, Founder, Competitive, DeepDive, Verification, and Synthesis agents
- **🔍 Complete Tavily API Integration**: Demonstrates all 4 Tavily APIs (Search, Map, Crawl, Extract) in real-world scenarios
- **💰 Budget-Optimized**: $10 OpenAI API constraint with intelligent caching and cost tracking
- **📊 Professional Reports**: Investment-grade analysis with confidence scoring and source attribution
- **⚡ Real-time Processing**: Async execution with live status updates and error handling
- **🎯 Modern UI**: React + TypeScript interface with animated workflows and responsive design

## 🏗 Architecture Overview

### 8-Agent Multi-Phase System

```mermaid
graph TD
    A[Discovery Agent] --> B[News Agent]
    A --> C[Patent Agent]
    A --> D[Founder Agent]
    A --> E[Competitive Agent]
    A --> F[DeepDive Agent]
    B --> G[Verification Agent]
    C --> G
    D --> G
    E --> G
    F --> G
    G --> H[Synthesis Agent]
```

**Phase 1: Discovery**
- **Discovery Agent**: Maps company digital presence using Tavily Map API

**Phase 2: Parallel Research** (Fan-out)
- **News Agent**: Funding, partnerships, market coverage (Tavily Search API)
- **Patent Agent**: IP portfolios and innovation landscapes
- **Founder Agent**: Leadership team backgrounds and track records
- **Competitive Agent**: Market positioning and competitive landscape
- **DeepDive Agent**: Detailed content analysis (Tavily Crawl + Extract APIs)

**Phase 3: Synthesis** (Fan-in)
- **Verification Agent**: Cross-source validation with confidence scoring
- **Synthesis Agent**: Investment intelligence generation with GPT-4o-mini

## 📁 Project Structure

```
VentureCompassAI/
├── 📂 backend/                    # FastAPI + LangGraph + MongoDB
│   ├── 📂 app/
│   │   ├── 📂 agents/             # 8 specialized AI agents
│   │   │   ├── discovery_agent.py      # Tavily Map API
│   │   │   ├── news_agent.py           # Tavily Search API (news)
│   │   │   ├── patent_agent.py         # IP analysis
│   │   │   ├── founder_agent.py        # Leadership analysis
│   │   │   ├── competitive_agent.py    # Market analysis
│   │   │   ├── deepdive_agent.py       # Tavily Crawl + Extract APIs
│   │   │   ├── verification_agent.py   # Fact-checking
│   │   │   ├── synthesis_agent.py      # Final report generation
│   │   │   └── llm_orchestrator.py     # LangGraph coordination
│   │   ├── 📂 api/v1/             # REST API endpoints
│   │   ├── 📂 core/               # Database and configuration
│   │   ├── 📂 models/             # Pydantic schemas
│   │   ├── 📂 services/           # External API clients
│   │   └── 📂 tools/              # Tavily tool integrations
│   └── requirements.txt
├── 📂 frontend/                   # React + TypeScript + Next.js
│   ├── 📂 src/
│   │   ├── 📂 app/                # Next.js app router
│   │   ├── 📂 components/         # UI components
│   │   │   ├── CompanySearchForm.tsx
│   │   │   ├── RunResults.tsx     # Comprehensive results view
│   │   │   ├── RunsHistory.tsx    # Analysis history
│   │   │   └── 📂 ui/             # Reusable UI components
│   │   ├── 📂 hooks/              # React hooks for API
│   │   ├── 📂 lib/                # Utilities and API client
│   │   └── 📂 types/              # TypeScript definitions
│   └── package.json
├── 📂 docs/                       # Technical documentation
├── 📂 scripts/                    # Development automation
└── 📄 Makefile                    # Cross-platform commands
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.9+ with pip
- **MongoDB Atlas** account (free tier)
- **API Keys**: Tavily, OpenAI
- **Git** for version control

### 🏁 One-Command Setup

Choose your preferred interface (all equivalent):

```bash
# Option 1: Makefile (cross-platform)
make setup && make dev

# Option 2: npm scripts (Windows-friendly)
npm run setup && npm run dev

# Option 3: Platform-specific scripts
./scripts/dev.sh setup && ./scripts/dev.sh start    # Unix/Linux/macOS
scripts\dev.bat setup && scripts\dev.bat start      # Windows
```

### 🔗 Access URLs (after setup)

- **🌐 Frontend**: http://localhost:5173
- **⚡ Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **🔧 API Admin Panel**: http://localhost:8000/redoc

## 🛠 Available Commands

| Task | Makefile | npm Script | Platform Script |
|------|----------|------------|----------------|
| **🏗 First-time setup** | `make setup` | `npm run setup` | `./scripts/dev.sh setup` |
| **🚀 Start both servers** | `make dev` | `npm run dev` | `./scripts/dev.sh start` |
| **⚙️ Backend only** | `make backend` | `npm run dev:backend` | - |
| **🎨 Frontend only** | `make frontend` | `npm run dev:frontend` | - |
| **🧪 Run all tests** | `make test` | `npm run test` | `./scripts/dev.sh test` |
| **🗄️ Test database** | `make db-test` | `npm run db:test` | `./scripts/dev.sh db-test` |
| **📊 Project status** | `make status` | `npm run status` | `./scripts/dev.sh status` |
| **🏗️ Build production** | `make build` | `npm run build` | - |
| **🧹 Clean artifacts** | `make clean` | `npm run clean` | `./scripts/dev.sh clean` |

## ⚙️ Configuration

### Backend Environment (`.env`)

```bash
# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/venturecompass

# Tavily API (Required)
TAVILY_API_KEY=your_tavily_api_key_here

# LLM Configuration
LLM_PROVIDER=openai                    # openai|anthropic|azure_openai
LLM_MODEL=gpt-4o-mini                 # Cost-optimized model
LLM_API_KEY=your_openai_api_key_here  # Or ANTHROPIC_API_KEY

# Budget Controls
COST_CAP_TAVILY_CREDITS=20            # Tavily usage limit
COST_CAP_LLM_USD=10.0                 # OpenAI budget limit
RUN_CACHE_TTL_HOURS=24                # Cache duration

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Frontend Environment (`.env`)

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## 🔌 API Endpoints

### Core Endpoints

- **`POST /api/run`** - Create new analysis run
  ```json
  {
    "company": "Anthropic",
    "domain": "anthropic.com"  // optional
  }
  ```

- **`GET /api/run/{id}`** - Get comprehensive run results
  ```json
  {
    "run_id": "r_12345",
    "status": "completed",
    "company": {"name": "Anthropic", "domain": "anthropic.com"},
    "insights": [...],
    "founders": [...],
    "competitive": {...},
    "deepdive": {...},
    "verification": {...},
    "patents": [...],
    "sources": [...],
    "cost": {"openai_usd": 0.29, "tavily_credits": 0}
  }
  ```

- **`GET /api/run/{id}/export.json`** - Export complete analysis

### Example Usage

```bash
# Create analysis
curl -X POST "http://localhost:8000/api/run" \
  -H "Content-Type: application/json" \
  -d '{"company": "Notion", "domain": "notion.so"}'

# Get results
curl "http://localhost:8000/api/run/r_12345"
```

## 🧪 Development & Testing

### Running Tests

```bash
# All tests
make test

# Specific test suites
make test-api          # API endpoint tests
make test-be           # Backend unit tests
make test-fe           # Frontend component tests

# Database tests
make db-test           # Test MongoDB connection
```

### Database Management

```bash
# Test connection
make db-test

# Reset database (⚠️ WARNING: Deletes all data)
make db-reset
```

### Code Quality

```bash
# Linting
make lint              # Frontend ESLint + TypeScript

# Type checking
cd frontend && npm run type-check
```

### Monitoring & Debugging

```bash
# Project status
make status

# View logs
make logs

# Clean build artifacts
make clean
```

## 🏗 Technical Stack

### Backend Technologies

- **🔥 FastAPI**: Async web framework with automatic OpenAPI docs
- **🕸️ LangGraph**: Agent orchestration and workflow management
- **🗄️ MongoDB Atlas**: Cloud database with optimized indexes
- **🔍 Tavily APIs**: Complete integration (Search, Map, Crawl, Extract)
- **🧠 OpenAI GPT-4o-mini**: Budget-optimized LLM for synthesis
- **📊 Pydantic**: Data validation and serialization
- **⚡ Motor**: Async MongoDB driver

### Frontend Technologies

- **⚛️ React 19**: Latest React with modern hooks
- **📘 TypeScript**: Type-safe development
- **🚀 Next.js 15**: App router with SSR capabilities
- **🎨 Tailwind CSS**: Utility-first styling
- **✨ Framer Motion**: Smooth animations and transitions
- **📡 TanStack Query**: Advanced data fetching and caching
- **🎯 Radix UI**: Accessible component primitives

## 🚨 Troubleshooting

### Common Issues

**1. MongoDB Connection Failed**
```bash
make db-test  # Test connection
# Check MONGODB_URI in backend/.env
```

**2. Port Already in Use**
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill
lsof -ti:5173 | xargs kill

# Windows
netstat -ano | findstr :8000
# Kill process by PID
```

**3. Missing Dependencies**
```bash
make clean && make setup  # Clean reinstall
```

**4. API Keys Not Working**
```bash
# Verify in backend/.env:
# TAVILY_API_KEY=tavily-xxx
# LLM_API_KEY=sk-xxx (for OpenAI)
```

**5. Build Errors**
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear caches
make clean
rm -rf frontend/node_modules frontend/.next
npm install
```

### Performance Optimization

- **Caching**: 24-hour result cache prevents duplicate API calls
- **Budget Controls**: Automatic cost tracking and limits
- **Lazy Loading**: Components load on demand
- **Code Splitting**: Optimized bundle sizes

## 📚 Documentation

- **🏗 Architecture**: See `docs/technical_doc.txt` for detailed implementation
- **📋 Requirements**: See `docs/PRD_v2.txt` for v2.0 specifications
- **🔧 Frontend Setup**: See `FRONTEND_DOCUMENTATION.md`
- **🤖 AI Development**: See `CLAUDE.md` for AI-specific guidelines
- **📖 Error Learning**: See `learn_from_errors.md` for debugging insights

## 🎯 Assignment Context

This project is a **Lead GenAI Engineer interview assignment for Tavily** with specific constraints:

- **⏰ Timeline**: 2 weeks for complete delivery
- **💰 Budget**: $10 OpenAI API limit (hard constraint)
- **🎬 Demo**: 3-5 minute video showcasing multi-agent collaboration
- **🎯 Goal**: Showcase ALL 4 Tavily APIs + advanced LangGraph patterns

**Success Criteria**: Technical excellence (40%) + Creativity (25%) + Code quality (20%) + Demo (15%)

## 🚀 Deployment

### Production Build

```bash
# Build all components
make build

# Frontend build artifacts
ls frontend/.next/

# Backend ready for deployment
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment Setup

1. **MongoDB Atlas**: Set up cluster and get connection string
2. **API Keys**: Obtain Tavily and OpenAI API keys
3. **Environment Variables**: Configure production `.env` files
4. **Domain**: Point your domain to the deployment

## 📄 License

This project is created for the Tavily Lead GenAI Engineer interview assignment.

## 🤝 Contributing

This is an interview assignment, but the codebase demonstrates:

- **Clean Architecture**: Separation of concerns and modular design
- **Type Safety**: Comprehensive TypeScript usage
- **Error Handling**: Graceful degradation and retry logic
- **Documentation**: Comprehensive code and API documentation
- **Testing**: Unit and integration test examples

---

**Built with ❤️ for the Tavily Lead GenAI Engineer Position**

*Showcasing complete Tavily API integration, advanced LangGraph orchestration, and budget-optimized AI development.*